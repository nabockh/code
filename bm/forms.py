from bm.models import Question
from django import forms


class CreateBenchmarkStep1(forms.Form):
    name = forms.CharField(max_length=45, required=True)
    industry = forms.ChoiceField(required=True)
    question_label = forms.CharField(max_length=255, required=True)
    question_text = forms.CharField(widget=forms.Textarea())
    question_type = forms.ChoiceField(choices=Question.TYPES, widget=forms.SelectMultiple())