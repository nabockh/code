from bm.models import Question, Region
from django import forms
from social.models import LinkedInIndustry


class CreateBenchmarkStep1Form(forms.Form):
    name = forms.CharField(max_length=45)
    industry = forms.ChoiceField()
    geo = forms.ChoiceField()
    question_label = forms.CharField(max_length=255)
    question_text = forms.CharField(widget=forms.Textarea())
    question_type = forms.MultipleChoiceField(choices=Question.TYPES)

    def __init__(self, *args, **kwargs):
        super(CreateBenchmarkStep1Form, self).__init__(*args, **kwargs)
        self.fields['geo'].choices = list(Region.regions.values_list('id', 'name').order_by('name'))
        self.fields['industry'].choices = list(LinkedInIndustry.objects.values_list('code', 'name').order_by('name'))


class CreateBenchmarkStep2Form(forms.Form):
    question_type = forms.ChoiceField(choices=Question.TYPES)
    answer_options = forms.CharField(widget=forms.Textarea())
    additional_comments = forms.CharField(widget=forms.Textarea(), required=False)
    minimum_number_of_answers = forms.IntegerField(min_value=0, initial=5)


class CreateBenchmarkStep3Form(forms.Form):
    pass    


class AnswerMultipleChoiceForm(forms.Form):

    def __init__(self, choices, *args, **kwargs):
        super(AnswerMultipleChoiceForm, self).__init__(*args, **kwargs)
        self.fields['choice'] = forms.MultipleChoiceField(choices=choices, widget=forms.CheckboxSelectMultiple())

