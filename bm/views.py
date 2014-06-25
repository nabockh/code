from bm.forms import CreateBenchmarkStep1Form, CreateBenchmarkStep2Form, AnswerMultipleChoiceForm, \
    CreateBenchmarkStep3Form, NumericAnswerForm
from bm.models import Benchmark, Region, Question, QuestionChoice, QuestionResponse, ResponseChoice, ResponseNumeric
from django.contrib.auth.decorators import login_required
from django.contrib.formtools.wizard.views import CookieWizardView
from django.db import transaction
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic.edit import FormView


class BenchmarkCreateWizardView(CookieWizardView):
    template_name = 'bm/create.html'
    form_list = [CreateBenchmarkStep1Form, CreateBenchmarkStep2Form, CreateBenchmarkStep3Form]

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(BenchmarkCreateWizardView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self, step=None):
        return {'user': self.request.user}

    def done(self, form_list, **kwargs):
        step1 = form_list[0]
        step2 = form_list[1]
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
                for i, choice in enumerate(choices):
                    choice = QuestionChoice(choice, i)
                    question.choices.add(choice)
        return HttpResponse('OK')


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

    def __init__(self):
        self.benchmark = Benchmark.objects.select_related('owner', 'geographic_coverage', '_industry', 'question').first()

    def dispatch(self, request, *args, **kwargs):
        question_type = self.benchmark.question.first().type
        if question_type == Question.MULTIPLE:
            return MultipleChoiceAnswerView.as_view()(self.request, *args, **kwargs)
        elif question_type == Question.RANKING:
            return RankingAnswerView.as_view()(self.request, *args, **kwargs)
        elif question_type == Question.RANGE:
            return RangeAnswerView.as_view()(self.request, *args, **kwargs)
        elif question_type == Question.NUMERIC:
            return NumericAnswerView.as_view()(self.request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BaseBenchmarkAnswerView, self).get_context_data(**kwargs)
        context['benchmark'] = self.benchmark
        return context


class MultipleChoiceAnswerView(BaseBenchmarkAnswerView):
    form_class = AnswerMultipleChoiceForm
    template_name = 'bm/answer.html'

    def dispatch(self, request, *args, **kwargs):
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
            print form.cleaned_data['choice']
        return super(MultipleChoiceAnswerView, self).form_valid(form)


class RankingAnswerView(BaseBenchmarkAnswerView):

    def dispatch(self, request, *args, **kwargs):
        return super(BaseBenchmarkAnswerView, self).dispatch(self.request, *args, **kwargs)


class RangeAnswerView(BaseBenchmarkAnswerView):
    form_class = NumericAnswerForm
    template_name = 'bm/answer.html'

    def dispatch(self, request, *args, **kwargs):
        return super(BaseBenchmarkAnswerView, self).dispatch(self.request, *args, **kwargs)

    def form_valid(self, form):
        if form.is_valid():
            with transaction.atomic():
                pass


class NumericAnswerView(BaseBenchmarkAnswerView):
    form_class = NumericAnswerForm
    template_name = 'bm/answer.html'

    def dispatch(self, request, *args, **kwargs):
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
