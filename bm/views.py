from datetime import datetime
from app.settings import DEBUG, REGISTERED_USER_REDIRECT_URL
from bm.utils import StringAgg
from django.core.cache import get_cache
from metrics.utils import event_log
from bm import metric_events
from bm.forms import CreateBenchmarkStep12Form, AnswerMultipleChoiceForm, \
    CreateBenchmarkStep3Form, CreateBenchmarkStep4Form, NumericAnswerForm, RangeAnswerForm, RankingAnswerForm, \
    BenchmarkDetailsForm, YesNoAnswerForm
from bm.models import Benchmark, Region, Question, QuestionChoice, QuestionResponse, ResponseChoice, ResponseNumeric, \
    ResponseRange, QuestionRanking, ResponseRanking, BenchmarkInvitation, QuestionOptions, BenchmarkLink, BenchmarkRating, \
    ResponseYesNo, BmInviteEmail
from core.forms import ContactForm
from bm.tasks import send_invites
from core.utils import login_required_ajax
from django.contrib.auth.decorators import login_required
from django.contrib.formtools.wizard.forms import ManagementForm
from django.contrib.formtools.wizard.views import SessionWizardView
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import Http404
from django.shortcuts import redirect
from django.template import loader, Context
from django.utils.datastructures import MultiValueDict
from django.utils.decorators import method_decorator
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import FormView
from bm.signals import benchmark_answered, benchmark_created
from django.db.models import Count, Q, Avg, F
from social.models import Contact

import json
import StringIO
import xlsxwriter


class BenchmarkCreateWizardView(SessionWizardView):
    template_name = 'bm/create.html'
    form_list = [CreateBenchmarkStep12Form, CreateBenchmarkStep3Form, CreateBenchmarkStep4Form]

    @method_decorator(login_required)
    @event_log(event_type=dict(GET=metric_events.BM_CREATE_OPEN))
    def dispatch(self, *args, **kwargs):
        return super(BenchmarkCreateWizardView, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        """
        This method handles POST requests.

        The wizard will render either the current step (if form validation
        wasn't successful), the next step (if the current step was stored
        successful) or the done view (if no more steps are available)
        """
        # Look for a wizard_goto_step element in the posted data which
        # contains a valid step name. If one was found, render the requested
        # form. (This makes stepping back a lot easier).

        # if self.request.is_ajax():
        #     print 'ajax'

        wizard_goto_step = self.request.POST.get('wizard_goto_step', None)
        if wizard_goto_step and wizard_goto_step in self.get_form_list():
            return self.render_goto_step(wizard_goto_step)

        # Check if form was refreshed
        management_form = ManagementForm(self.request.POST, prefix=self.prefix)
        if not management_form.is_valid():
            raise ValidationError(
                ('ManagementForm data is missing or has been tampered.'),
                code='missing_management_form',
            )

        form_current_step = management_form.cleaned_data['current_step']
        if (form_current_step != self.steps.current and
                    self.storage.current_step is not None):
            # form refreshed, change current step
            self.storage.current_step = form_current_step

        # get the form for the current step
        form = self.get_form(data=self.request.POST, files=self.request.FILES)

        # and try to validate
        if form.is_valid():
            # if the form is valid, store the cleaned data and files.
            self.storage.set_step_data(self.steps.current, self.process_step(form))
            self.storage.set_step_files(self.steps.current, self.process_step_files(form))

            save_and_wizard_goto_step = self.request.POST.get('save_and_wizard_goto_step', None)
            if save_and_wizard_goto_step and save_and_wizard_goto_step in self.get_form_list():
                return self.render_goto_step(save_and_wizard_goto_step)

            add_selected = self.request.POST.get('add_selected', None)
            if add_selected and add_selected in self.get_form_list():
                return self.render_goto_step(add_selected, context={'active_tab': 3})
            # check if the current step is the last step
            if self.steps.current == self.steps.last:
                # no more steps, render done view
                return self.render_done(form, **kwargs)
            else:
                # proceed to the next step
                return self.render_next_step(form)
        return self.render(form)

    def render_next_step(self, form, **kwargs):
        """
        This method gets called when the next step/form should be rendered.
        `form` contains the last/current form.
        """
        next_step = self.steps.next
        if next_step in ['1', '2'] and self.storage.data['step_data'].get('0') is None:
            return HttpResponseRedirect('create')
        if next_step == '2':
            new_form = self.get_form(next_step,
                data=None,
                files=self.storage.get_step_files(next_step))
        else:
            new_form = self.get_form(next_step,
                data=self.storage.get_step_data(next_step),
                files=self.storage.get_step_files(next_step))

        # change the stored current step
        self.storage.current_step = next_step
        return self.render(new_form, **kwargs)


    def render_done(self, form, **kwargs):
        """
        This method gets called when all forms passed. The method should also
        re-validate all steps to prevent manipulation. If any form don't
        validate, `render_revalidation_failure` should get called.
        If everything is fine call `done`.
        """
        final_form_list = []
        # walk through the form list and try to validate the data again.
        for form_key in self.get_form_list():
            form_obj = self.get_form(step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key))
            if not form_obj.is_valid():
                return self.render_revalidation_failure(form_key, form_obj, **kwargs)
            final_form_list.append(form_obj)

        # render the done view and reset the wizard before returning the
        # response. This is needed to prevent from rendering done with the
        # same data twice.
        if self.request.is_ajax():
            preview_body = self.request.session._session.get('preview_body', None)
            # if
            benchmark = self.done(final_form_list, preview=True, **kwargs)
            return self.render_email_preview(self.request, benchmark, form)

        done_response = self.done(final_form_list, **kwargs)

        self.storage.reset()
        return done_response

    @staticmethod
    def render_email_preview(request, benchmark, form):
        template = loader.get_template('alerts/invite.html')
        # TODO: http is hardcoded
        context = Context({
            'benchmark': benchmark,
            'question_label': form.cleaned_data['question_label'],
            'benchmark_name': benchmark.name,
            'query_details': form.cleaned_data['question_text'],
            'benchmark_creator': benchmark.owner.get_full_name(),
            'link_to_answer': "Link to answer form will be here",
            'link_to_bm_results': "Link to benchmark results will be here",
            'remaining_before_closure': benchmark.days_left,
        })
        preview_body = request.session._session.get('preview_body', None)
        default_preview = request.session._session.get('default_preview', None)
        if preview_body and (preview_body != default_preview):
            context = preview_body
        else:
            context = template.render(context)
            request.session['default_preview'] = context
        response = HttpResponse("<textarea type='text' style='width:100%' name='text-area' id='default_text'>"
                                + context
                                + '</textarea>')
        return response

    def render_goto_step(self, goto_step, **kwargs):
        """
        This method gets called when the current step has to be changed.
        `goto_step` contains the requested step to go to.
        """
        self.storage.current_step = goto_step
        form = self.get_form(
            data=self.storage.get_step_data(self.steps.current),
            files=self.storage.get_step_files(self.steps.current))
        return self.render(form, **kwargs.get('context', {}))

    def get_form_kwargs(self, step=None):
        params = {'user': self.request.user}
        if step == '1':
            params['wizard'] = self
        if step == '1' or step == '2':
            params['step0data'] = self.storage.get_step_data('0')
        if step == '2':
            params['end_date'] = getattr(self, 'end_date', datetime.now())
        return params

    def get_context_data(self, form, **kwargs):
        context = super(BenchmarkCreateWizardView, self).get_context_data(form, **kwargs)

        #reset email preview session keys
        if len(self.storage.data.get('step_data')) == 0:
            self.refresh_preview_data()

        if self.steps.current == '2':
            context['selected_contacts'] = self.selected_contacts if hasattr(self, 'selected_contacts') else []
            question_type = form.initial['question_type']
            if question_type == '1':
                choices = [(i, i) for i in (form.initial['answer_options'].split('\r\n')[:-1])]
                context['multiple_form'] = AnswerMultipleChoiceForm(choices)
            elif question_type == '2':
                ranks = [(i, answ) for i, answ in enumerate((form.initial['answer_options'].split('\r\n')[:-1]), 1)]
                context['ranking_form'] = RankingAnswerForm(ranks)
            if question_type == '3':
                context['numeric_form'] = NumericAnswerForm()
            elif question_type == '4':
                context['yes_no_form'] = YesNoAnswerForm()
            elif question_type == '5':
                context['range_form'] = RangeAnswerForm()
        return context

    @event_log(event_type=metric_events.BM_CREATE_DONE, object='benchmark')
    def done(self, form_list, preview=False, **kwargs):
        step2 = form_list[1]
        step3 = form_list[2]
        with transaction.atomic():
            benchmark = Benchmark()
            benchmark.name = step3.cleaned_data['name']
            benchmark.owner = self.request.user
            # TODO: Industry and Geo(?) must be fixed later to support multiple choice inputs
            if isinstance(step3.cleaned_data['industry'], list):
                benchmark.industry = step3.cleaned_data['industry'][0]
            elif step3.cleaned_data['industry'] == u'':
                benchmark.industry = None
            else:
                benchmark.industry = step3.cleaned_data['industry']
            benchmark.min_numbers_of_responses = step3.cleaned_data['minimum_number_of_answers']
            if preview:
                self.benchmark = benchmark
                return self.benchmark
            benchmark.save()

            if isinstance(step3.cleaned_data['geo'], list):
                bm_geo = step3.cleaned_data['geo'][0]
            else:
                bm_geo = step3.cleaned_data['geo']
            if bm_geo:
                region = Region.objects.get(pk=bm_geo)
                benchmark.geographic_coverage.add(region)
            if self.request.session._session.get('preview_body', None):
                invite_mail = BmInviteEmail()
                invite_mail.benchmark = benchmark
                invite_mail.body = self.request.session._session.get('preview_body', None)
                invite_mail.save()
            question = Question()
            question.benchmark = benchmark
            question.label = step3.cleaned_data['question_label']
            question.description = step3.cleaned_data['question_text']
            question.type = int(step3.cleaned_data['question_type'])
            question.save()

            if question.type == Question.MULTIPLE:
                choices = step3.cleaned_data['answer_options'].split('\r\n')
                choices = [option for option in choices if option]
                for i, choice in enumerate(choices, start=1):
                    choice = QuestionChoice(label=choice, order=i)
                    question.choices.add(choice)
            elif question.type == Question.RANKING:
                ranks = step3.cleaned_data['answer_options'].split('\r\n')
                ranks = [option for option in ranks if option]
                for i, rank in enumerate(ranks, start=1):
                    rank = QuestionRanking(label=rank, order=i)
                    question.ranks.add(rank)
            elif question.type == Question.NUMERIC or question.type == Question.RANGE:
                question.options.add(QuestionOptions(units=step3.cleaned_data.get('units')))

            step2_data = self.storage.get_step_data('1')
            for contact in step2.selected_contacts:
                if step3.data.get(contact.invite_element):
                    invite = BenchmarkInvitation()
                    invite.sender = benchmark.owner
                    invite.recipient = contact
                    invite.status = '0' #not send
                    invite.is_allowed_to_forward_invite = bool(step3.data.get(contact.secondary_element))
                    benchmark.invites.add(invite)

            link = benchmark.create_link()
            benchmark.calculate_deadline()
            benchmark.save()
            self.refresh_preview_data()
        if benchmark.pk:
            benchmark_created.send(sender=self.__class__, request=self.request, benchmark=benchmark)
            self.benchmark = benchmark
        return redirect('bm_dashboard')

    def refresh_preview_data(self):
            self.request.session['preview_body'] = None
            self.request.session['default_preview'] = None


class PreviewPopupView(FormView):

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            preview_body = self.request.session._session.get('preview_body', None)
            new_body = self.request.POST.get('text-area')
            if not preview_body or preview_body != new_body:
                self.request.session['preview_body'] = new_body
                return HttpResponse(200)
            else:
                return HttpResponse(200)


class BenchmarkHistoryView(ListView):
    template_name = 'bm/history.html'
    context_object_name = 'benchmark'
    model = Benchmark

    def get_context_data(self, **kwargs):
        data = super(BenchmarkHistoryView, self).get_context_data(**kwargs)
        data['contact_form'] = ContactForm()
        return data

    @method_decorator(login_required)
    @event_log(event_type=metric_events.BM_HISTORY_OPEN)
    def dispatch(self, request, *args, **kwargs):
        return super(BenchmarkHistoryView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Benchmark.valid.filter(Q(owner=self.request.user) |
                                      Q(question__responses__user=self.request.user),
                                      end_date__lte=datetime.now()).order_by('-start_date')


class BenchmarkSearchView(ListView):
    template_name = 'bm/history.html'
    # paginate_by = 10
    context_object_name = 'benchmark'
    model = Benchmark

    def get_context_data(self, **kwargs):
        data = super(BenchmarkSearchView, self).get_context_data(**kwargs)
        data['contact_form'] = ContactForm()
        return data

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BenchmarkSearchView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Benchmark.valid.filter(end_date__lte=datetime.now())\
            .extra(select={'description': 'bm_question.description'})\
            .select_related('owner')\
            .annotate(rate_avg=Avg('ratings__rating'),
                      _contributors=Count('question__responses')).order_by('-start_date')


class BaseBenchmarkAnswerView(FormView):
    success_url = '/dashboard'
    benchmark = None

    @method_decorator(login_required)
    def dispatch(self, request, slug, *args, **kwargs):

        benchmark_link = BenchmarkLink.objects\
            .filter(slug=slug,)\
            .select_related('benchmark', 'benchmark__owner',
                            'benchmark__question',
                            'benchmark___industry',
                            'benchmark__geographic_coverage',
                            'benchmark__invites')\
            .first()
        if not benchmark_link:
            raise Http404
        benchmark = benchmark_link.benchmark
        if benchmark.end_date <= datetime.date(datetime.now()):
            return ForbiddenView.as_view()(self.request, *args, **kwargs)
        if request.user == benchmark.owner:
            return ForbiddenView.as_view()(self.request, *args, **kwargs)
        user_responses_count = benchmark.question\
            .filter(responses__user=request.user)\
            .annotate(responses_count=Count('responses'))\
            .values_list('responses_count', flat=True)\
            .first()
        if user_responses_count and not DEBUG:
            return HttpResponseRedirect(REGISTERED_USER_REDIRECT_URL)
        friendly_contacts_count = BenchmarkInvitation.user_friendly_invites_count(
                                    request.user.first_name,
                                    request.user.last_name,
                                    benchmark.id)

        recipient = benchmark.invites.filter(Q(recipient__user=request.user)).first()
        if not recipient and friendly_contacts_count == 0:
            return ForbiddenView.as_view()(self.request, *args, **kwargs)

        question_type = benchmark.question.first().type
        if question_type == Question.MULTIPLE:
            return MultipleChoiceAnswerView.as_view()(self.request, benchmark, *args, **kwargs)
        elif question_type == Question.RANKING:
            return RankingAnswerView.as_view()(self.request, benchmark, *args, **kwargs)
        elif question_type == Question.RANGE:
            return RangeAnswerView.as_view()(self.request, benchmark, *args, **kwargs)
        elif question_type == Question.NUMERIC:
            return NumericAnswerView.as_view()(self.request, benchmark, *args, **kwargs)
        elif question_type == Question.YES_NO:
            return YesNoAnswerView.as_view()(self.request, benchmark, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super(BaseBenchmarkAnswerView, self).get_context_data(**kwargs)
        context['benchmark'] = self.benchmark
        context['contributors'] = self.benchmark.invites.count()
        return context

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            result = self.form_valid(form)
            benchmark_answered.send(sender=self.__class__, request=request, user=request.user, benchmark=self.benchmark)
            return result
        else:
            return self.form_invalid(form)

answer_event_log = event_log(event_type=dict(GET=metric_events.BM_ANSWER_OPEN, POST=metric_events.BM_ANSWER_SAVE), object='benchmark')


class MultipleChoiceAnswerView(BaseBenchmarkAnswerView):
    form_class = AnswerMultipleChoiceForm
    template_name = 'bm/answer/Multiple.html'

    @answer_event_log
    def dispatch(self, request, benchmark, *args, **kwargs):
        self.benchmark = benchmark
        return super(BaseBenchmarkAnswerView, self).dispatch(self.request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(MultipleChoiceAnswerView, self).get_form_kwargs()
        kwargs['choices'] = self.benchmark.question.first().choices.values_list('id', 'label')
        return kwargs

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        if form.is_valid():
            with transaction.atomic():
                question_response = QuestionResponse()
                question_response.user = self.request.user
                question_response.question = self.benchmark.question.first()
                question_response.save()
                choices = form.cleaned_data['choice']
                choices = QuestionChoice.objects.filter(id__in=choices)
                for choice in choices:
                    bm_response_choice = ResponseChoice()
                    bm_response_choice.choice = choice
                    question_response.data_choices.add(bm_response_choice)
        return super(MultipleChoiceAnswerView, self).form_valid(form)


class RankingAnswerView(BaseBenchmarkAnswerView):
    form_class = RankingAnswerForm
    template_name = 'bm/answer/Ranking.html'

    @answer_event_log
    def dispatch(self, request, benchmark, *args, **kwargs):
        self.benchmark = benchmark
        return super(BaseBenchmarkAnswerView, self).dispatch(self.request, *args, **kwargs)


    def get_form_kwargs(self):
        kwargs = super(RankingAnswerView, self).get_form_kwargs()
        kwargs['ranks'] = self.benchmark.question.first().ranks.values_list('id', 'label')
        return kwargs

    def form_valid(self, form):
        if form.is_valid():
            with transaction.atomic():
                question_response = QuestionResponse()
                question_response.user = self.request.user
                question_response.question = self.benchmark.question.first()
                question_response.save()
                ranks = question_response.question.ranks.all()
                for rank in ranks:
                    rank_value = form.cleaned_data['rank{0}'.format(rank.id)]
                    response_rank = ResponseRanking()
                    response_rank.rank = rank
                    response_rank.value = rank_value
                    question_response.data_ranks.add(response_rank)
            return super(RankingAnswerView, self).form_valid(form)


class RangeAnswerView(BaseBenchmarkAnswerView):
    form_class = RangeAnswerForm
    template_name = 'bm/answer/Range.html'

    @answer_event_log
    def dispatch(self, request, benchmark, *args, **kwargs):
        self.benchmark = benchmark
        return super(BaseBenchmarkAnswerView, self).dispatch(self.request, *args, **kwargs)

    def form_valid(self, form):
        if form.is_valid():
            with transaction.atomic():
                question_response = QuestionResponse()
                question_response.user = self.request.user
                question_response.question = self.benchmark.question.first()
                question_response.save()
                bm_response_range = ResponseRange()
                min_val = form.cleaned_data['min']
                max_val = form.cleaned_data['max']
                bm_response_range.min = min_val
                bm_response_range.max = max_val
                question_response.data_range.add(bm_response_range)
        return super(RangeAnswerView, self).form_valid(form)


class NumericAnswerView(BaseBenchmarkAnswerView):
    form_class = NumericAnswerForm
    template_name = 'bm/answer/Numeric.html'

    @answer_event_log
    def dispatch(self, request, benchmark, *args, **kwargs):
        self.benchmark = benchmark
        return super(BaseBenchmarkAnswerView, self).dispatch(self.request, *args, **kwargs)

    def form_valid(self, form):
        if form.is_valid():
            with transaction.atomic():
                question_response = QuestionResponse()
                question_response.user = self.request.user
                question_response.question = self.benchmark.question.first()
                question_response.save()
                bm_response_numeric = ResponseNumeric()
                bm_response_numeric.value = form.cleaned_data['numeric_box']
                question_response.data_numeric.add(bm_response_numeric)

        return super(NumericAnswerView, self).form_valid(form)


class YesNoAnswerView(BaseBenchmarkAnswerView):
    form_class = YesNoAnswerForm
    template_name = 'bm/answer/Yes_No.html'

    @answer_event_log
    def dispatch(self, request, benchmark, *args, **kwargs):
        self.benchmark = benchmark
        return super(BaseBenchmarkAnswerView, self).dispatch(self.request, *args, **kwargs)

    def form_valid(self, form):
        if form.is_valid():
            with transaction.atomic():
                question_response = QuestionResponse()
                question_response.user = self.request.user
                question_response.question = self.benchmark.question.first()
                question_response.save()
                bm_response_yes_no = ResponseYesNo()
                bm_response_yes_no.value = form.cleaned_data['Choose Yes or No:']
                question_response.data_boolean.add(bm_response_yes_no)

        return super(YesNoAnswerView, self).form_valid(form)


class ForbiddenView(TemplateView):
    template_name = '403.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context, status=403)


class WelcomeView(TemplateView):
    template_name = 'bm/welcome.html'

    def get_context_data(self, **kwargs):
        context = super(WelcomeView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class BenchmarkDetailView(FormView):
    form_class = BenchmarkDetailsForm
    template_name = 'bm/details_graphs.html'

    @event_log(event_type=dict(GET=metric_events.BM_DETAIL_OPEN, POST=metric_events.BM_RATE_SAVE), object='benchmark')
    def dispatch(self, request, *args, **kwargs):
        if not self.get_benchmark() and not DEBUG:
            return ForbiddenView.as_view()(self.request, *args, **kwargs)
        return super(BenchmarkDetailView, self).dispatch(request, *args, **kwargs)

    def get_benchmark(self, **kwargs):

        if hasattr(self, 'benchmark'):
            return self.benchmark
        else:
            bm_id = self.kwargs['bm_id']
            f = Q(id=bm_id) if DEBUG else Q(id=bm_id, end_date__lte=datetime.now())
            self.benchmark = Benchmark.valid.filter(f)\
                .select_related('question', 'responses',
                                'benchmark___industry',
                                'benchmark__geographic_coverage').first()
            return self.benchmark

    def get_form_kwargs(self):
        kwargs = super(BenchmarkDetailView, self).get_form_kwargs()
        kwargs['benchmark'] = self.get_benchmark()
        return kwargs

    def get_context_data(self, **kwargs):
        # Note: Role data was removed by request of Customer, but possible will be
        # needed in future
        benchmark = self.get_benchmark(**kwargs)
        question = benchmark.question.first()
        is_contributor = not self.request.user.is_anonymous() and \
                         Benchmark.objects.filter(id=benchmark.id, question__responses__user=self.request.user)
        cache = get_cache('default')
        cache_key = 'bm_detail_view_context%d' % benchmark.id
        context = cache.get(cache_key)
        if context is None:
            context = dict()
            context['url'] = self.request.META['HTTP_HOST'] + self.request.path
            # group_by_headline = QuestionResponse.objects.filter(question=benchmark.question.first()).\
            #     values('user__social_profile__headline').annotate(count=Count('id'))
            group_by_country = QuestionResponse.objects.filter(question=question).\
                values('user__social_profile__location__name').annotate(count=Count('id'))
            group_by_geo = QuestionResponse.objects.filter(question=question).\
                values('user__social_profile__location__parent__name').annotate(count=Count('id'))
            group_by_industry = QuestionResponse.objects.filter(question=question).\
                values('user__social_profile__company___industry__name').annotate(count=Count('id'))
            # for dictionary in group_by_headline:
            #     dictionary['role'] = dictionary['user__social_profile__headline'] or "Not Available"
            #     del dictionary['user__social_profile__headline']
            for dictionary in group_by_geo:
                dictionary['geo'] = dictionary['user__social_profile__location__parent__name'] or "Not Available"
                del dictionary['user__social_profile__location__parent__name']
            for dictionary in group_by_country:
                dictionary['country'] = dictionary['user__social_profile__location__name'] or "Not Available"
                del dictionary['user__social_profile__location__name']
            for dictionary in group_by_industry:
                dictionary['industry'] = dictionary['user__social_profile__company___industry__name'] or "Not Available"
                del dictionary['user__social_profile__company___industry__name']
            # headlines = []
            # for item in group_by_headline:
            #     first = item['count']
            #     second = item['role']
            #     headlines.append([second, first])
            geo = []
            for item in group_by_geo:
                first = item['count']
                second = item['geo']
                geo.append([second, first])
            countries = []
            for item in group_by_country:
                first = item['count']
                second = item['country']
                countries.append([second, first])
            industries = []
            for item in group_by_industry:
                first = item['count']
                second = item['industry']
                industries.append([second, first])
            # context['role'] = list(headlines)
            # context['role'].insert(0, ['role', 'count'])
            context['geo'] = list(geo)
            context['geo'].insert(0, ['geo', 'count'])
            context['countries'] = list(countries)
            context['countries'].insert(0, ['countries', 'count'])
            context['industries'] = list(industries)
            context['industries'].insert(0, ['industries', 'count'])

            for field in ['geo', 'countries', 'industries']:
                context[field] = json.dumps(context[field])

            # Count percentage in aggregated lists
            countries_percentage = list(countries)
            sum_country = sum([each[1] for each in countries_percentage])
            for item in countries_percentage:
                item[1] = round(float(item[1])/sum_country*100)
            geo_percentage = list(geo)
            sum_geo = sum([each[1] for each in geo_percentage])
            for item in geo_percentage:
                item[1] = round(float(item[1])/sum_geo*100)
            # role_percentage = list(headlines)
            # sum_role = sum([each[1] for each in role_percentage])
            # for item in role_percentage:
            #     item[1] = round(float(item[1])/sum_role*100)
            industry_percentage = list(industries)
            sum_industry = sum([each[1] for each in industry_percentage])
            for item in industry_percentage:
                item[1] = round(float(item[1])/sum_industry*100)
            # context['role_percentage'] = role_percentage
            context['industry_percentage'] = industry_percentage
            context['geo_percentage'] = geo_percentage
            context['countries_percentage'] = countries_percentage
            cache.set(cache_key, context)
        context.update(super(BenchmarkDetailView, self).get_context_data(**kwargs))
        context['benchmark'] = benchmark
        context['question'] = question
        context['is_contributor'] = is_contributor
        return context

    @method_decorator(login_required_ajax)
    def post(self, request, **kwargs):
        if self.request.is_ajax():
            with transaction.atomic():
                benchmark_id = kwargs['bm_id']
                benchmark = self.get_benchmark(**kwargs)
                if BenchmarkRating.objects.filter(benchmark=benchmark, user=request.user).first():
                    rating = BenchmarkRating.objects.filter(benchmark=benchmark, user=request.user).first()
                    rating.rating = request.POST.get('rate')
                    rating.user = request.user
                    rating.save()
                    benchmark.ratings.add(rating)
                else:
                    rating = BenchmarkRating()
                    rating.rating = request.POST.get('rate')
                    rating.benchmark_id = benchmark_id
                    rating.user = request.user
                    rating.save()
                    benchmark.ratings.add(rating)
                return HttpResponse(benchmark.calc_average_rating())
        return HttpResponse(200)


class BenchmarkAddRecipientsView(FormView):
    template_name = 'bm/add_recipients.html'
    form_class = CreateBenchmarkStep3Form
    success_url = reverse_lazy('bm_dashboard')

    @method_decorator(login_required)
    def dispatch(self, request, bm_id, *args, **kwargs):
        self.benchmark = Benchmark.pending.filter(pk=bm_id, owner=request.user).first()
        if not self.benchmark:
            raise Http404
        self.except_ids = set(self.benchmark.invites.values_list('recipient_id', flat=True))
        return super(BenchmarkAddRecipientsView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        class Mock(object):
            pass
        kwargs = super(BenchmarkAddRecipientsView, self).get_form_kwargs()
        wizard = Mock()
        geo = self.benchmark.geographic_coverage.first()
        params = dict(
            user=self.request.user,
            step0data=MultiValueDict({
                '0-geo': [geo.id] if geo else '',
                '0-industry': [self.benchmark.industry.code] if self.benchmark.industry else '',
            }),
            wizard=wizard,
            prefix='1',
            except_ids=self.except_ids,
            benchmark=self.benchmark
        )
        kwargs.update(params)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(BenchmarkAddRecipientsView, self).get_context_data(**kwargs)
        if self.request.POST.get('add_selected', None):
            context['active_tab'] = 3
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        send_invitations = self.request.POST.get('send_invitations')
        if form.is_valid() and send_invitations:
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    @event_log(event_type=metric_events.BM_ADD_PARTICIPANTS, object='benchmark')
    def form_valid(self, form):
        for contact in form.selected_contacts:
            if contact.id not in self.except_ids:
                if form.cleaned_data.get(contact.invite_element) or form.cleaned_data.get('contact-{0}-invite'.format(contact.id)):
                    invite = BenchmarkInvitation()
                    invite.sender = self.benchmark.owner
                    invite.recipient = contact
                    invite.status = 0 # not send
                    invite.is_allowed_to_forward_invite = \
                        bool(form.data.get(form.prefix + '-' + contact.secondary_element) or
                             form.cleaned_data.get('contact-{0}-secondary'.format(contact.id)))
                    self.benchmark.invites.add(invite)
        if self.benchmark.approved:
            send_invites.delay(self.benchmark.id)
        return super(BenchmarkAddRecipientsView, self).form_valid(form)


class BenchmarkAggregateView(BenchmarkDetailView):

    def get(self, *args, **kwargs):
        if self.get_benchmark():
            self.get_benchmark().aggregate()
        else:
            return ForbiddenView.as_view()(self.request, *args, **kwargs)
        return HttpResponse('Done')


class ExcelDownloadView(BenchmarkDetailView):

    @method_decorator(login_required)
    @event_log(event_type=metric_events.BM_EXCEL_EXPORT, object='benchmark')
    def dispatch(self, request, *args, **kwargs):
        if not self.get_benchmark() and not DEBUG:
            return ForbiddenView.as_view()(self.request, *args, **kwargs)
        return super(BenchmarkDetailView, self).dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        bm_id = kwargs['bm_id']
        benchmark = Benchmark.objects.filter(id=bm_id).select_related('question',
                                                                        'responses',
                                                                        'benchmark___industry',
                                                                        'benchmark__geographic_coverage').first()
        self.benchmark = benchmark
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        bold = workbook.add_format({'bold': True})
        question = benchmark.question.first()
        description = question.description
        if benchmark.owner:
            owner = benchmark.owner.first_name + ' ' + benchmark.owner.last_name
        else:
            owner = None
        basic_info = [benchmark.name, question.label, description]
        if owner:
            basic_info.append(owner)
        # set info worksheet settings
        info_worksheet = workbook.add_worksheet('Basic information')
        contributor_worksheet = workbook.add_worksheet('Contributor Stats')
        countries_worksheet = workbook.add_worksheet('Countries')
        industry_worksheet = workbook.add_worksheet('Industry')
        # role_worksheet = workbook.add_worksheet('Role')
        geo_worksheet = workbook.add_worksheet('Geo')
        col = 1
        row = 0
        cell_format = workbook.add_format({'bold': True})
        info_worksheet.set_column(0, 1, 30)
        info_worksheet.write(0, 0, 'Benchmark Name:', cell_format)
        info_worksheet.write(1, 0, 'Question:', cell_format)
        info_worksheet.write(2, 0, 'Description:', cell_format)
        info_worksheet.write(3, 0, 'Owner:', cell_format)
        for info in basic_info:
            info_worksheet.write(row, col, info)
            row += 1
        context = self.get_context_data(**kwargs)

        # Graph worksheet settings
        # Countries stat data worksheet
        chart = workbook.add_chart({'type': 'pie'})
        countries_stat = context['countries_percentage']
        countries_worksheet.set_column(0, 1, 30)
        countries_data = [
            [countrie[0] for countrie in countries_stat],
            [countrie[1] for countrie in countries_stat],
        ]
        headings = ['Country', 'Percentage %']
        countries_worksheet.write_row('A1', headings, bold)
        countries_worksheet.write_column('A2', countries_data[0])
        countries_worksheet.write_column('B2', countries_data[1])
        chart.add_series({
            'categories': '=Countries!$A$2:$A${0}'.format(len(countries_stat)+1),
            'values':     '=Countries!$B$2:$B${0}'.format(len(countries_stat)+1),
        })
        chart.set_chartarea({
            'border': {'color': 'black'},
            'fill':   {'color': 'white'}
        })
        countries_worksheet.insert_chart('C3', chart)

        # industry stat data worksheet
        chart = workbook.add_chart({'type': 'pie'})
        industry_worksheet.set_column(0, 1, 30)
        industry_stat = context['industry_percentage']
        industry_data = [
            [industry[0] for industry in industry_stat],
            [industry[1] for industry in industry_stat],
        ]
        headings = ['Industry', 'Percentage %']
        industry_worksheet.write_row('A1', headings, bold)
        industry_worksheet.write_column('A2', industry_data[0])
        industry_worksheet.write_column('B2', industry_data[1])
        chart.add_series({
            'categories': '=Industry!$A$2:$A${0}'.format(len(industry_stat)+1),
            'values':     '=Industry!$B$2:$B${0}'.format(len(industry_stat)+1),
        })
        chart.set_chartarea({
            'border': {'color': 'black'},
            'fill':   {'color': 'white'}
        })
        industry_worksheet.insert_chart('C3', chart)

        #NOTE: Role Stats were removed by request of customer, but it is possible that
        # we will need this in future.

        # role stat data worksheet
        # chart = workbook.add_chart({'type': 'pie'})
        # role_worksheet.set_column(0, 1, 30)
        # role_stat = context['role_percentage']
        # role_data = [
        #     [role[0] for role in role_stat],
        #     [role[1] for role in role_stat],
        # ]
        # headings = ['Role', 'Percentage %']
        # role_worksheet.write_row('A1', headings, bold)
        # role_worksheet.write_column('A2', role_data[0])
        # role_worksheet.write_column('B2', role_data[1])
        # chart.add_series({
        #     'categories': '=Role!$A$2:$A${0}'.format(len(role_stat)+1),
        #     'values':     '=Role!$B$2:$B${0}'.format(len(role_stat)+1),
        # })
        # chart.set_chartarea({
        #     'border': {'color': 'black'},
        #     'fill':   {'color': 'white'}
        # })
        # role_worksheet.insert_chart('C3', chart)

        # Geo stat data worksheet
        chart = workbook.add_chart({'type': 'pie'})
        geo_worksheet.set_column(0, 1, 30)
        geo_stat = context['geo_percentage']
        geo_data = [
            [geo[0] for geo in geo_stat],
            [geo[1] for geo in geo_stat],
        ]
        headings = ['Geo', 'Percentage %']
        geo_worksheet.write_row('A1', headings, bold)
        geo_worksheet.write_column('A2', geo_data[0])
        geo_worksheet.write_column('B2', geo_data[1])
        chart.add_series({
            'categories': '=Geo!$A$2:$A${0}'.format(len(geo_stat)+1),
            'values':     '=Geo!$B$2:$B${0}'.format(len(geo_stat)+1),
        })
        chart.set_chartarea({
            'border': {'color': 'black'},
            'fill':   {'color': 'white'}
        })
        geo_worksheet.insert_chart('C3', chart)

        # Contributor results charts
        question_type = benchmark.question.first().type
        if question_type == 1:
            contributor_results = benchmark.charts['pie'][1:]
            chart = workbook.add_chart({'type': 'pie'})
        elif question_type == 2:
            contributor_results = json.loads(benchmark.charts)['bar_excel']
            chart = workbook.add_chart({'type': 'bar', 'subtype': 'percent_stacked'})
        elif question_type == 3:
            contributor_results = benchmark.charts['bell_curve']
            area_data = benchmark.charts['area']
            chart_bell_curve = workbook.add_chart({'type': 'scatter'})
            chart_area = workbook.add_chart({'type': 'area'})
        elif question_type == 4:
            contributor_results = benchmark.charts['pie']
            chart = workbook.add_chart({'type': 'pie'})
        elif question_type == 5:
            stock_data = benchmark.charts['ecxel_stock']
            area_data = benchmark.charts['area']
            chart_stock = workbook.add_chart({'type': 'stock'})
            chart_area = workbook.add_chart({'type': 'area'})
        contributor_worksheet.set_column(0, 1, 30)
        if question_type == 1:
            data = [
                [x[0] for x in contributor_results],
                [x[1] for x in contributor_results]
            ]
            suma = sum(data[1])
            percents = []
            for item in data[1]:
                percents.append(round((float(item)/suma)*100))
            headings = ['Answer', 'Percentage %']
            contributor_worksheet.write_row('A1', headings, bold)
            contributor_worksheet.write_column('A2', data[0])
            contributor_worksheet.write_column('B2', percents)
            chart.add_series({
                'categories': '=Contributor Stats!$A$2:$A${0}'.format(len(contributor_results) + 1),
                'values':     '=Contributor Stats!$B$2:$B${0}'.format(len(contributor_results) + 1),
                'data_labels': {'percentage': True}
            })
            chart.set_chartarea({
                'border': {'color': 'black'},
                'fill':   {'color': 'white'}
            })
            chart.set_title({'name': benchmark.name})
            contributor_worksheet.insert_chart('F3', chart)

        elif question_type == 2:
            ranks = ['', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
            ranks_count = []
            for idx, result in enumerate(contributor_results[::-1], start=2):
                contributor_worksheet.write_column('%s%s' % (ranks[idx], 1), result)
                ranks_count.append('Rank'+str(idx-1))
            contributor_worksheet.write_column('A2', ranks_count)
            last_col = ranks[len(ranks_count) + 1]
            for idx, i in enumerate(ranks_count, start=2):
                chart.add_series({
                    'name': i,
                    'values': "=Contributor Stats!$B$%s:$%s$%s" % (idx, last_col, idx),
                    'categories': "='Contributor Stats'!B1:$%s$1" % (last_col,),
                    'data_labels': {'value': True},
                })
            chart.set_title({'name': benchmark.name})
            chart.set_size({'x_scale': 2.5, 'y_scale': 2})
            chart.set_style(3)
            contributor_worksheet.insert_chart('A13', chart)
        elif question_type == 3:
            internal_worksheet = workbook.add_worksheet('Internal')
            data = [
                contributor_results.keys(),
                contributor_results.values()
            ]
            headings = ['Property', 'Value']
            contributor_worksheet.write_row('A1', headings, bold)
            contributor_worksheet.write_column('A2', data[0])
            contributor_worksheet.write_column('B2', data[1])

            min = contributor_results['min']
            max = contributor_results['max']
            avg = contributor_results['avg']
            sd = contributor_results['sd']

            step = 6*sd/50
            first_step = avg-(3*sd)
            steps = [first_step]
            i = 0
            while i < 50:
                steps.append((steps[i]+step))
                i += 1
            steps_count = len(steps) + 7
            internal_worksheet.write_column('C1', steps)

            # Enable worksheet protection
            internal_worksheet.write_array_formula('D1:D50',
                                                   "{=NORMDIST(C1:C50,'Contributor Stats'!$B$3,"
                                                   "'Contributor Stats'!$B$4,0)}")
            chart_bell_curve.add_series({
                'name':         benchmark.name,
                'categories': "='Internal'!C1:C50",
                'values': "='Internal'!D1:D50",
                'line': {'dash_type': 'solid', 'width': 1, 'color': 'red'}

            })

            chart_bell_curve.set_chartarea({
                'border': {'color': 'black'},
                'fill':   {'color': 'white'}
            })
            # for item in area_data:
            area_headings = ['% of contributor below value', 'Contributor Value']
            contributor_worksheet.write_row('A6' , area_headings)
            for idx, (point, val) in enumerate(area_data[1:], start=7):
                contributor_worksheet.write_row('A%s' % idx, [point, ])
                contributor_worksheet.write_row('B%s' % idx, [val, ])
            chart_area.add_series({
                'name':         benchmark.name,
                'categories': "='Contributor Stats'!A7:A{0}".format(len(area_data[1:]) + 6),
                'values': "='Contributor Stats'!B7:B{0}".format(len(area_data[1:]) + 6),
            })
            chart_bell_curve.set_y_axis({'num_format': ''})
            contributor_worksheet.insert_chart('F6', chart_bell_curve)
            contributor_worksheet.insert_chart('F23', chart_area)
            # internal_worksheet.protect()
            internal_worksheet.hide()
        elif question_type == 4:
            no_values = [[value[0], value[1]] for value in contributor_results if value[0] == 'No']
            yes_values = [[value[0], value[1]] for value in contributor_results if value[0] == 'Yes']
            no = no_values[0] if no_values else []
            yes = yes_values[0] if yes_values else []
            headings = ['Answer', '% of respondents']
            contributor_worksheet.write_row('A1', headings, bold)
            contributor_worksheet.write_row('A2', no)
            contributor_worksheet.write_row('A3', yes)

            chart.add_series({
                'categories': '=Contributor Stats!$A$2:$A$3',
                'values':     '=Contributor Stats!$B$2:$B$3',
                'data_labels': {'percentage': True}
            })
            chart.set_title({'name': benchmark.name})
            chart.set_chartarea({
                'border': {'color': 'black'},
                'fill':   {'color': 'white'}
            })
            contributor_worksheet.insert_chart('F3', chart)
        elif question_type == 5:
            # Stock chart
            headings = ['Quartile', 'Min', 'Max', 'Avg']
            for idx, quartile in enumerate(stock_data, start=2):
                contributor_worksheet.write_row('A%s' % idx, quartile)
            contributor_worksheet.write_row('A1', headings)
            chart_stock.add_series({
                # 'name': "=Contributor Stats!$B$1:$B$1",
                'values':     "=Contributor Stats!$B$2:$B$5",
                'marker': {
                    'type': 'circle',
                    'size': 4,
                    'border': {'color': 'black'},
                    'fill':   {'color': 'blue'},
                },
            })
            chart_stock.add_series({
                # 'categories': "'=Contributor Stats'!$A$2:$A$5",
                'values':     "=Contributor Stats!$C$2:$C$5",
                'marker': {
                    'type': 'circle',
                    'size': 4,
                    'border': {'color': 'black'},
                    'fill':   {'color': 'green'},
                },
            })
            chart_stock.add_series({
                'categories': "='Contributor Stats'!A2:A5",
                'values':     "=Contributor Stats!$D$2:$D$5",
                'marker': {
                    'type': 'triangle',
                    'size': 6,
                    'border': {'color': 'black'},
                    'fill':   {'color': 'red'},
                },
            })
            chart_stock.set_x_axis({'name': '% of Respondents'})
            chart_stock.set_y_axis({'name': 'Values'})
            chart_stock.set_legend({'none': True})
            chart_stock.set_title ({'name': benchmark.name})
            chart_stock.set_style(2)
            chart_stock.set_legend({'none':True})
            contributor_worksheet.insert_chart('E1', chart_stock)
            # Area Chart
            headings_area = ['Frequency', 'Average']
            for idx, data in enumerate(area_data[1:], start=17):
                contributor_worksheet.write_row('A%s' % idx, data)
            index_row = 16
            contributor_worksheet.write_row('A%s' % index_row, headings_area)
            row_index = len(area_data[1:]) + 16
            chart_area.add_series({
                'name':         benchmark.name,
                'categories': "='Contributor Stats'!A17:A%s" % row_index,
                'values': "='Contributor Stats'!B17:B%s" % row_index,
            })
            chart_area.set_legend({'none': True})
            chart_area.set_x_axis({'name': '% of Respondents'})
            contributor_worksheet.insert_chart('E17', chart_area)
        workbook.close()
        output.seek(0)

        response = HttpResponse(output.read(),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="{0}.xlsx"'.format(benchmark.name)
        return response

    def get_context_data(self, **kwargs):
        context = super(ExcelDownloadView, self).get_context_data(**kwargs)
        return context