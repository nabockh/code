import json
from bm.forms import CreateBenchmarkStep12Form, AnswerMultipleChoiceForm, \
    CreateBenchmarkStep3Form, CreateBenchmarkStep4Form, NumericAnswerForm, RangeAnswerForm, RankingAnswerForm, \
    BenchmarkDetailsForm
from bm.models import Benchmark, Region, Question, QuestionChoice, QuestionResponse, ResponseChoice, ResponseNumeric, \
    ResponseRange, QuestionRanking, ResponseRanking, BenchmarkInvitation, QuestionOptions, BenchmarkLink, BenchmarkRating
from core.utils import login_required_ajax
from django.contrib.auth.decorators import login_required
from django.contrib.formtools.wizard.forms import ManagementForm
from django.contrib.formtools.wizard.views import CookieWizardView
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect
from django.template.defaultfilters import safe
from django.utils.decorators import method_decorator
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import FormView
from bm.signals import benchmark_answered
from django.db.models import Count
import StringIO
import xlsxwriter


class BenchmarkCreateWizardView(CookieWizardView):
    template_name = 'bm/create.html'
    form_list = [CreateBenchmarkStep12Form, CreateBenchmarkStep3Form, CreateBenchmarkStep4Form]

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
        # if step == '2':
        #     params['step1data'] = self.storage.get_step_data('1')
        return params

    def get_context_data(self, form, **kwargs):
        context = super(BenchmarkCreateWizardView, self).get_context_data(form, **kwargs)
        if self.steps.current == '2':
            context['selected_contacts'] = self.selected_contacts if hasattr(self, 'selected_contacts') else []
        return context

    def done(self, form_list, **kwargs):
        step2 = form_list[1]
        step3 = form_list[2]
        with transaction.atomic():
            benchmark = Benchmark()
            benchmark.name = step3.cleaned_data['name']
            benchmark.owner = self.request.user
            benchmark.industry = step3.cleaned_data['industry']
            region = Region.objects.get(pk=step3.cleaned_data['geo'])
            benchmark.save()
            benchmark.geographic_coverage.add(region)

            question = Question()
            question.benchmark = benchmark
            question.label = step3.cleaned_data['question_label']
            question.description = step3.cleaned_data['question_text']
            question.type = int(step3.cleaned_data['question_type'])
            question.save()

            if question.type == Question.MULTIPLE:
                choices = step3.cleaned_data['answer_options'].split('\r\n')
                for i, choice in enumerate(choices, start=1):
                    choice = QuestionChoice(label=choice, order=i)
                    question.choices.add(choice)
            elif question.type == Question.RANKING:
                ranks = step3.cleaned_data['answer_options'].split('\r\n')
                for i, rank in enumerate(ranks, start=1):
                    rank = QuestionRanking(label=rank, order=i)
                    question.ranks.add(rank)
            elif question.type == Question.NUMERIC or question.type == Question.RANGE:
                question.options.add(QuestionOptions(step3.cleaned_data.get('units'), step3.cleaned_data.get('max_number_of_decimal')))

            step2_data = self.storage.get_step_data('1')
            for contact in step2.selected_contacts:
                if step2_data.get('1-selected-{0}-invite'.format(contact.id)):
                    invite = BenchmarkInvitation()
                    invite.sender = benchmark.owner
                    invite.recipient = contact
                    invite.status = '0' #not send
                    invite.is_allowed_to_forward_invite = bool(step2_data.get('1-selected-{0}-secondary'.format(contact.id)))
                    benchmark.invites.add(invite)

            link = benchmark.create_link()
            benchmark.calculate_deadline()
            benchmark.save()

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


class BenchmarkSearchView(ListView):
    template_name = 'bm/history.html'
    paginate_by = 10
    context_object_name = 'benchmark'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BenchmarkSearchView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        order_by = self.request.GET.get('order_by', 'name')
        return Benchmark.valid.order_by(order_by).select_related('question')


class BaseBenchmarkAnswerView(FormView):
    success_url = '/thanks/'
    benchmark = None

    # def __init__(self, *args, **kwargs):
    #     self.benchmark = Benchmark.objects.select_related('owner', 'geographic_coverage', '_industry',
    #                                                       'question').first()
    @method_decorator(login_required)
    def dispatch(self, request, slug, *args, **kwargs):

        benchmark_link = BenchmarkLink.objects.filter(slug=slug).select_related('benchmark', 'benchmark__owner',
                                                                                'benchmark__question',
                                                                                'benchmark___industry',
                                                                                'benchmark__geographic_coverage',
                                                                                'benchmark__invites').first()
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
            benchmark_answered.send(sender=self.__class__, user=request.user)
            if not QuestionResponse.objects.filter(user=request.user).count() > 1:
                return redirect('/benchmark/welcome')
            return result
        else:
            return self.form_invalid(form)


class MultipleChoiceAnswerView(BaseBenchmarkAnswerView):
    form_class = AnswerMultipleChoiceForm
    template_name = 'bm/answerMultiple.html'

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
    template_name = 'bm/answerRanking.html'

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
    template_name = 'bm/answerRange.html'

    def dispatch(self, request, benchmark, *args, **kwargs):
        self.benchmark = benchmark
        return super(BaseBenchmarkAnswerView, self).dispatch(self.request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(RangeAnswerView, self).get_form_kwargs()
        kwargs['decimals'] = self.benchmark.question.first().options.values('number_of_decimal')[0]
        return kwargs

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
    template_name = 'bm/answerNumeric.html'

    def dispatch(self, request, benchmark, *args, **kwargs):
        self.benchmark = benchmark
        return super(BaseBenchmarkAnswerView, self).dispatch(self.request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(NumericAnswerView, self).get_form_kwargs()
        kwargs['decimals'] = self.benchmark.question.first().options.values('number_of_decimal')[0]
        return kwargs

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


class WelcomeView(TemplateView):
    template_name = 'bm/welcome.html'

    def get_context_data(self, **kwargs):
        context = super(WelcomeView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class BenchmarkDetailView(FormView):
    form_class = BenchmarkDetailsForm
    template_name = 'bm/details_graphs.html'

    def get_benchmark(self, **kwargs):
        if hasattr(self, 'benchmark'):
            return self.benchmark
        else:
            bm_id = self.kwargs['bm_id']
            self.benchmark = Benchmark.objects.filter(id=bm_id).select_related('question', 'responses',
                                                                                'benchmark___industry',
                                                                                'benchmark__geographic_coverage').first()
            return self.benchmark

    def get_form_kwargs(self):
        kwargs = super(BenchmarkDetailView, self).get_form_kwargs()
        kwargs['benchmark'] = self.get_benchmark()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(BenchmarkDetailView, self).get_context_data(**kwargs)
        benchmark = self.get_benchmark(**kwargs)
        context['benchmark'] = benchmark
        context['question'] = benchmark.question.first()
        context['url'] = self.request.META['HTTP_HOST'] + self.request.path
        group_by_headline = QuestionResponse.objects.filter(question=benchmark.question.first()).values('user__social_profile__headline').annotate(count=Count('user__social_profile__headline'))
        group_by_country = QuestionResponse.objects.filter(question=benchmark.question.first()).values('user__social_profile__location__name').annotate(count=Count('user__social_profile__location__name'))
        group_by_geo = QuestionResponse.objects.filter(question=benchmark.question.first()).values('user__social_profile__location__parent__name').annotate(count=Count('user__social_profile__location__parent__name'))
        group_by_industry = QuestionResponse.objects.filter(question=benchmark.question.first()).values('user__social_profile__company___industry__name').annotate(count=Count('user__social_profile__company___industry__name'))
        for dictionary in group_by_headline:
            dictionary['role'] = dictionary['user__social_profile__headline']
            del dictionary['user__social_profile__headline']
        for dictionary in group_by_geo:
            dictionary['geo'] = dictionary['user__social_profile__location__parent__name']
            del dictionary['user__social_profile__location__parent__name']
        for dictionary in group_by_country:
            dictionary['country'] = dictionary['user__social_profile__location__name']
            del dictionary['user__social_profile__location__name']
        for dictionary in group_by_industry:
            dictionary['industry'] = dictionary['user__social_profile__company___industry__name']
            del dictionary['user__social_profile__company___industry__name']
        headlines = []
        for item in group_by_headline:
            first = item['count']
            second = str(item['role'])
            headlines.append([second, first])
        geo = []
        for item in group_by_geo:
            first = item['count']
            second = str(item['geo'])
            geo.append([second, first])
        countries = []
        for item in group_by_country:
            first = item['count']
            second = str(item['country'])
            countries.append([second, first])
        industries = []
        for item in group_by_industry:
            first = item['count']
            second = str(item['industry'])
            industries.append([second, first])
        context['role'] = list(headlines)
        context['role'].insert(0, ['role', 'count'])
        context['geo'] = list(geo)
        context['geo'].insert(0, ['geo', 'count'])
        context['countries'] = list(countries)
        context['countries'].insert(0, ['countries', 'count'])
        context['industries'] = list(industries)
        context['industries'].insert(0, ['industries', 'count'])

        # Count percentage in aggregated lists
        countries_percentage = list(countries)
        sum_country = sum([each[1] for each in countries_percentage])
        for item in countries_percentage:
            item[1] = round(float(item[1])/sum_country*100)
        geo_percentage = list(geo)
        sum_geo = sum([each[1] for each in geo_percentage])
        for item in geo_percentage:
            item[1] = round(float(item[1])/sum_geo*100)
        role_percentage = list(headlines)
        sum_role = sum([each[1] for each in role_percentage])
        for item in role_percentage:
            item[1] = round(float(item[1])/sum_role*100)
        industry_percentage = list(industries)
        sum_industry = sum([each[1] for each in industry_percentage])
        for item in industry_percentage:
            item[1] = round(float(item[1])/sum_industry*100)
        context['role_percentage'] = role_percentage
        context['industry_percentage'] = industry_percentage
        context['geo_percentage'] = geo_percentage
        context['countries_percentage'] = countries_percentage
        return context

    @method_decorator(login_required_ajax)
    def post(self, request, **kwargs):
        if self.request.is_ajax():
            with transaction.atomic():
                benchmark_id = kwargs['bm_id']
                benchmark = self.get_benchmark(**kwargs)
                # if BenchmarkRating.objects.filter(benchmark=benchmark, user=benchmark.question.first().responses.first().user):
                if Benchmark.objects.filter(id=benchmark.id, question__responses__user=self.request.user):
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
                else:
                    return HttpResponse(401)
        return HttpResponse(200)


class BenchmarkAggregateView(BenchmarkDetailView):

    def get(self, *args, **kwargs):
        self.get_benchmark().aggregate()
        return HttpResponse('Done')

class ExcelDownloadView(BenchmarkDetailView):

    def get(self, *args, **kwargs):
        bm_id = kwargs['bm_id']
        benchmark = Benchmark.objects.filter(id=bm_id).select_related('question',
                                                                        'responses',
                                                                        'benchmark___industry',
                                                                        'benchmark__geographic_coverage').first()
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        question = benchmark.question.first()
        description = question.description
        basic_info = [benchmark.name, question.label, description, benchmark.owner.first_name + ' ' +benchmark.owner.last_name]
        # set info worksheet settings
        info_worksheet = workbook.add_worksheet('Basic information')
        countries_worksheet = workbook.add_worksheet('Countries')
        industry_worksheet = workbook.add_worksheet('Industry')
        role_worksheet = workbook.add_worksheet('Role')
        geo_worksheet = workbook.add_worksheet('Geo')
        contributor_worksheet = workbook.add_worksheet('Contributor Stats')
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
        countries_worksheet.write_column('A1', countries_data[0])
        countries_worksheet.write_column('B1', countries_data[1])
        chart.add_series({
            'categories': '=Countries!$A$1:$A${0}'.format(len(countries_stat)),
            'values':     '=Countries!$B$1:$B${0}'.format(len(countries_stat)),
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
        industry_worksheet.write_column('A1', industry_data[0])
        industry_worksheet.write_column('B1', industry_data[1])
        chart.add_series({
            'categories': '=Industry!$A$1:$A${0}'.format(len(industry_stat)),
            'values':     '=Industry!$B$1:$B${0}'.format(len(industry_stat)),
        })
        chart.set_chartarea({
            'border': {'color': 'black'},
            'fill':   {'color': 'white'}
        })
        industry_worksheet.insert_chart('C3', chart)

        # role stat data worksheet
        chart = workbook.add_chart({'type': 'pie'})
        role_worksheet.set_column(0, 1, 30)
        role_stat = context['role_percentage']
        role_data = [
            [role[0] for role in role_stat],
            [role[1] for role in role_stat],
        ]
        role_worksheet.write_column('A1', role_data[0])
        role_worksheet.write_column('B1', role_data[1])
        chart.add_series({
            'categories': '=Role!$A$1:$A${0}'.format(len(role_stat)),
            'values':     '=Role!$B$1:$B${0}'.format(len(role_stat)),
        })
        chart.set_chartarea({
            'border': {'color': 'black'},
            'fill':   {'color': 'white'}
        })
        role_worksheet.insert_chart('C3', chart)

        # Geo stat data worksheet
        chart = workbook.add_chart({'type': 'pie'})
        geo_worksheet.set_column(0, 1, 30)
        geo_stat = context['geo_percentage']
        geo_data = [
            [geo[0] for geo in geo_stat],
            [geo[1] for geo in geo_stat],
        ]
        geo_worksheet.write_column('A1', geo_data[0])
        geo_worksheet.write_column('B1', geo_data[1])
        chart.add_series({
            'categories': '=Geo!$A$1:$A${0}'.format(len(geo_stat)),
            'values':     '=Geo!$B$1:$B${0}'.format(len(geo_stat)),
        })
        chart.set_chartarea({
            'border': {'color': 'black'},
            'fill':   {'color': 'white'}
        })
        geo_worksheet.insert_chart('C3', chart)

        #Contributor results charts
        # question_type = benchmark.question.first().type
        # if question_type == 1:
        #     contributor_results = benchmark.charts['pie'][1:]
        #     chart = workbook.add_chart({'type': 'pie'})
        # elif question_type == 2:
        #     contributor_results = benchmark.charts['column']
        #     chart = workbook.add_chart({'type': 'column'})
        # elif question_type == 3:
        #     contributor_results = benchmark.charts['pie'][1:]
        #     chart = workbook.add_chart({'type': 'pie'})
        # elif question_type == 4:
        #     contributor_results = benchmark.charts['pie'][1:]
        #     chart = workbook.add_chart({'type': 'pie'})
        #
        # contributor_worksheet.set_column(0, 1, 30)
        # i = 1
        # for result in contributor_results:
        #     contributor_worksheet.write_row('A{0}'.format(i), result)
        #     i+=1
        #
        # chart.add_series({
        #     'categories': '=Contributor Stats!$A$2:$A${0}'.format(len(contributor_results)),
        #     'values':     '=Contributor Stats!$B$2:$D${0}'.format(len(contributor_results)),
        # })
        #
        # chart.set_chartarea({
        #     'border': {'color': 'black'},
        #     'fill':   {'color': 'white'}
        # })
        # contributor_worksheet.insert_chart('E3', chart)

        workbook.close()
        output.seek(0)

        response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename={0}.xlsx'.format(benchmark.name)
        return response

    def get_context_data(self, **kwargs):
        context = super(ExcelDownloadView, self).get_context_data(**kwargs)
        return context