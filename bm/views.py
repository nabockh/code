from bm.forms import CreateBenchmarkStep1, CreateBenchmarkStep2
from bm.models import Benchmark, Region, Question, QuestionChoice
from django.contrib.auth.decorators import login_required
from django.contrib.formtools.wizard.views import CookieWizardView
from django.db import transaction
from django.http import HttpResponse
from django.utils.decorators import method_decorator


class BenchmarkCreateWizardView(CookieWizardView):
    template_name = 'bm/create.html'
    form_list = [CreateBenchmarkStep1, CreateBenchmarkStep2]

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(BenchmarkCreateWizardView, self).dispatch(*args, **kwargs)

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