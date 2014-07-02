from bm.forms import CreateBenchmarkStep1Form, CreateBenchmarkStep2Form, AnswerMultipleChoiceForm, \
    CreateBenchmarkStep3Form, CreateBenchmarkStep4Form, NumericAnswerForm, RangeAnswerForm, RankingAnswerForm
from bm.models import Benchmark, Region, Question, QuestionChoice, QuestionResponse, ResponseChoice, ResponseNumeric, \
    ResponseRange, QuestionRanking, ResponseRanking, BenchmarkInvitation, QuestionOptions, BenchmarkLink
from django.contrib.auth.decorators import login_required
from django.contrib.formtools.wizard.forms import ManagementForm
from django.contrib.formtools.wizard.views import CookieWizardView
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic.edit import FormView
from bm.signals import benchmark_answered


class BenchmarkCreateWizardView(CookieWizardView):
    template_name = 'bm/create.html'
    form_list = [CreateBenchmarkStep1Form, CreateBenchmarkStep2Form, CreateBenchmarkStep3Form, CreateBenchmarkStep4Form]

    @method_decorator(login_required)
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
        wizard_goto_step = self.request.POST.get('wizard_goto_step', None)
        if wizard_goto_step and wizard_goto_step in self.get_form_list():
            return self.render_goto_step(wizard_goto_step)

        # Check if form was refreshed
        management_form = ManagementForm(self.request.POST, prefix=self.prefix)
        if not management_form.is_valid():
            raise ValidationError(
                _('ManagementForm data is missing or has been tampered.'),
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

            # check if the current step is the last step
            if self.steps.current == self.steps.last:
                # no more steps, render done view
                return self.render_done(form, **kwargs)
            else:
                # proceed to the next step
                return self.render_next_step(form)
        return self.render(form)

    def get_form_kwargs(self, step=None):
        params = {'user': self.request.user}
        if step == '1':
            params['question_type'] = int(self.storage.get_step_data('0').get('0-question_type', '1'))
        return params

    def done(self, form_list, **kwargs):
        step1 = form_list[0]
        step2 = form_list[1]
        step3 = form_list[2]
        with transaction.atomic():
            benchmark = Benchmark()
            benchmark.name = step1.cleaned_data['name']
            benchmark.owner = self.request.user
            benchmark.industry = step1.cleaned_data['industry']
            region = Region.objects.get(pk=step1.cleaned_data['geo'])
            benchmark.save()
            benchmark.geographic_coverage.add(region)

            question = Question()
            question.benchmark = benchmark
            question.label = step1.cleaned_data['question_label']
            question.description = step1.cleaned_data['question_text']
            question.type = int(step2.cleaned_data['question_type'])
            question.save()

            if question.type == Question.MULTIPLE:
                choices = step2.cleaned_data['answer_options'].split('\r\n')
                for i, choice in enumerate(choices, start=1):
                    choice = QuestionChoice(choice, i)
                    question.choices.add(choice)
            elif question.type == Question.RANKING:
                ranks = step2.cleaned_data['answer_options'].split('\r\n')
                for i, rank in enumerate(ranks, start=1):
                    rank = QuestionRanking(rank, i)
                    question.ranks.add(rank)
            elif question.type == Question.NUMERIC or question.type == Question.RANGE:
                question.options.add(QuestionOptions(step2.cleaned_data.get('units'), step2.cleaned_data.get('max_number_of_decimal')))

            step3_data = self.storage.get_step_data('2')
            for contact in step3.contacts_filtered:
                if step3_data.get('2-contact-{0}-invite'.format(contact.id)):
                    invite = BenchmarkInvitation()
                    invite.sender = benchmark.owner
                    invite.recipient = contact
                    invite.status = '0' #not send
                    invite.is_allowed_to_forward_invite = bool(step3_data.get('2-contact-{0}-secondary'.format(contact.id)))
                    benchmark.invites.add(invite)

            link = benchmark.create_link()

        return HttpResponse(link)


class BenchmarkHistoryView(ListView):
    template_name = 'bm/history.html'
    paginate_by = 10
    context_object_name = 'benchmark'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BenchmarkHistoryView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        order_by = self.request.GET.get('order_by', 'name')
        return Benchmark.objects.filter(owner=self.request.user).order_by(order_by).select_related('question')


class BaseBenchmarkAnswerView(FormView):
    success_url = '/thanks/'
    benchmark = None

    # def __init__(self, *args, **kwargs):
    #     self.benchmark = Benchmark.objects.select_related('owner', 'geographic_coverage', '_industry',
    #                                                       'question').first()

    def dispatch(self, request, slug, *args, **kwargs):

        benchmark_link = BenchmarkLink.objects.filter(slug=slug).select_related('benchmark', 'benchmark__owner',
                                                                                'benchmark__question',
                                                                                'benchmark___industry',
                                                                                'benchmark__geographic_coverage',).first()
        if not benchmark_link:
            return HttpResponseNotFound()
        benchmark = benchmark_link.benchmark
        question_type = benchmark.question.first().type
        if question_type == Question.MULTIPLE:
            return MultipleChoiceAnswerView.as_view()(self.request, benchmark, *args, **kwargs)
        elif question_type == Question.RANKING:
            return RankingAnswerView.as_view()(self.request, benchmark, *args, **kwargs)
        elif question_type == Question.RANGE:
            return RangeAnswerView.as_view()(self.request, benchmark, *args, **kwargs)
        elif question_type == Question.NUMERIC:
            return NumericAnswerView.as_view()(self.request, benchmark, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BaseBenchmarkAnswerView, self).get_context_data(**kwargs)
        context['benchmark'] = self.benchmark
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
            benchmark_answered.send(sender=self.__class__, user=request.user)
            return result
        else:
            return self.form_invalid(form)


class MultipleChoiceAnswerView(BaseBenchmarkAnswerView):
    form_class = AnswerMultipleChoiceForm
    template_name = 'bm/answer.html'

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
                choice = form.cleaned_data['choice']
                for choice in QuestionChoice.objects.filter(id__in=choice):
                    bm_response_choice = ResponseChoice()
                    bm_response_choice.choice = choice
                    question_response.data_choices.add(bm_response_choice)
        return super(MultipleChoiceAnswerView, self).form_valid(form)


class RankingAnswerView(BaseBenchmarkAnswerView):
    form_class = RankingAnswerForm
    template_name = 'bm/answer.html'

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
    template_name = 'bm/answer.html'

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
    template_name = 'bm/answer.html'

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
            print form.cleaned_data['numeric_box']

        return super(NumericAnswerView, self).form_valid(form)
