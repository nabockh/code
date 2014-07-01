from bm.models import Question, Region
from django import forms
from bm.widgets import RankingWidget
from django.db.models import Q
from social.models import LinkedInIndustry


class CreateBenchmarkStep1Form(forms.Form):
    name = forms.CharField(max_length=45)
    industry = forms.ChoiceField()
    geo = forms.ChoiceField()
    question_label = forms.CharField(max_length=255)
    question_text = forms.CharField(widget=forms.Textarea())
    question_type = forms.MultipleChoiceField(choices=Question.TYPES)

    def __init__(self, user, *args, **kwargs):
        super(CreateBenchmarkStep1Form, self).__init__(*args, **kwargs)
        self.fields['geo'].choices = list(Region.regions.values_list('id', 'name').order_by('name'))
        self.fields['industry'].choices = list(LinkedInIndustry.get_proposal(user.contacts))


class CreateBenchmarkStep2Form(forms.Form):
    question_type = forms.ChoiceField(choices=Question.TYPES)
    answer_options = forms.CharField(widget=forms.Textarea())
    additional_comments = forms.CharField(widget=forms.Textarea(), required=False)
    minimum_number_of_answers = forms.IntegerField(min_value=0, initial=5)

    def __init__(self, user, question_type, *args, **kwargs):
        super(CreateBenchmarkStep2Form, self).__init__(*args, **kwargs)
        if question_type == Question.NUMERIC or question_type == Question.RANGE:
            del self.fields['answer_options']
            self.fields.insert(1, 'units', forms.CharField(max_length=50))
            self.fields.insert(2, 'max_number_of_decimal', forms.IntegerField(min_value=1, max_value=6))


class CreateBenchmarkStep3Form(forms.Form):
    industry = forms.ChoiceField(required=False)
    geo = forms.ChoiceField(required=False)
    role = forms.CharField(max_length=200, required=False)
    name = forms.CharField(max_length=100, required=False)

    def __init__(self, user, *args, **kwargs):
        super(CreateBenchmarkStep3Form, self).__init__(*args, **kwargs)
        regions = [('', '------')]
        regions.extend(list(Region.regions.values_list('id', 'name').order_by('name')))
        self.fields['geo'].choices = regions
        industries = [('', '------')]
        industries.extend(list(LinkedInIndustry.get_proposal(user.contacts)))
        self.fields['industry'].choices = industries
        if self.is_valid():
            contact_filter = {}
            name_filter = None
            if self.cleaned_data.get('name'):
                name_filter = Q(last_name__istartswith=self.cleaned_data.get('name')) | \
                              Q(first_name__istartswith=self.cleaned_data.get('name'))
            if self.cleaned_data.get('role'):
                contact_filter['headline__icontains'] = self.cleaned_data.get('role')
            if self.cleaned_data.get('industry'):
                contact_filter['company___industry__code'] = self.cleaned_data.get('industry')
            if self.cleaned_data.get('geo'):
                contact_filter['location__parent__id'] = self.cleaned_data.get('geo')
            self.contacts_filtered = user.contacts.filter(name_filter, **contact_filter) if name_filter else \
                user.contacts.filter(**contact_filter)
            for contact in self.contacts_filtered:
                self.fields['contact-{0}-invite'.format(contact.id)] = forms.BooleanField(label=contact.full_name)
                self.fields['contact-{0}-secondary'.format(contact.id)] = forms.BooleanField(label='')



class CreateBenchmarkStep4Form(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super(CreateBenchmarkStep4Form, self).__init__(*args, **kwargs)


class AnswerMultipleChoiceForm(forms.Form):

    def __init__(self, choices, *args, **kwargs):
        super(AnswerMultipleChoiceForm, self).__init__(*args, **kwargs)
        self.fields['choice'] = forms.MultipleChoiceField(choices=choices, widget=forms.CheckboxSelectMultiple())


class NumericAnswerForm(forms.Form):
    numeric_box = forms.IntegerField()


class RangeAnswerForm(forms.Form):
    min = forms.IntegerField(label="min")
    max = forms.IntegerField(label='max')


class RankingAnswerForm(forms.Form):
    def __init__(self, ranks, *args, **kwargs):
        super(RankingAnswerForm, self).__init__(*args, **kwargs)
        for i, rank in enumerate(ranks):
            self.fields['rank{0}'.format(rank[0])] = forms.IntegerField(widget=RankingWidget(attrs={'label': rank[1], 'value':i}))
