from datetime import datetime, timedelta
import math
from app import settings
from app.settings import BENCHMARK_DURATIONS_DAYS
from bm.tasks import benchmark_aggregate
import re
from bm.validators import multiple_choice_validator
from bm.models import Question, Region, QuestionOptions
from django import forms
from bm.widgets import RankingWidget
from django.db.models import Q
from social.models import LinkedInIndustry, Contact
from math import pow


class CreateBenchmarkStep12Form(forms.Form):
    name = forms.CharField(max_length=45)
    industry = forms.ChoiceField()
    geo = forms.ChoiceField(required=False)
    question_label = forms.CharField(max_length=255)
    question_text = forms.CharField(widget=forms.Textarea(attrs={'maxlength': 10000}),
                                    max_length=10000, required=False)
    question_type = forms.ChoiceField(choices=Question.TYPES)
    answer_options = forms.CharField(widget=forms.Textarea(), validators=[multiple_choice_validator])
    units = forms.ChoiceField(initial='$', choices=QuestionOptions.UNITS)
    min_value = 1 if settings.DEBUG else 5
    minimum_number_of_answers = forms.IntegerField(min_value=min_value, initial=5)

    def __init__(self, user, data, *args, **kwargs):
        super(CreateBenchmarkStep12Form, self).__init__(data=data, *args, **kwargs)
        regions = [('', 'All')]
        regions.extend(list(Region.regions.values_list('id', 'name').order_by('name')))
        self.fields['geo'].choices = regions
        proposed_industry = LinkedInIndustry.get_proposal(user.contacts)
        if proposed_industry:
            self.fields['industry'].choices = list(proposed_industry)
        else:
            self.fields['industry'].choices = list(LinkedInIndustry.objects.values_list('code', 'name'))
        units = data and data.get('0-units') or kwargs.get('initial', {}).get('units')
        if units and not units in [v for v, _ in QuestionOptions.UNITS]:
            choices = list(QuestionOptions.UNITS)
            choices.insert(0, (units, units))
            choices = tuple(choices)
            self.fields['units'] = forms.ChoiceField(initial=units, choices=choices)
        question_type = int(data and data.get(kwargs['prefix'] + '-question_type', '1') or '1')
        if question_type == Question.MULTIPLE or question_type == Question.RANKING:
            self.fields['units'].required = False
        elif question_type == Question.NUMERIC or question_type == Question.RANGE:
            self.fields['answer_options'].required = False
            self.fields['answer_options'].validators = []
        elif question_type == Question.YES_NO:
            self.fields['answer_options'].required = False
            self.fields['units'].required = False
            self.fields['answer_options'].validators = []


class CreateBenchmarkStep3Form(forms.Form):
    industry = forms.MultipleChoiceField(required=False)
    geo = forms.ChoiceField(required=False)
    role = forms.CharField(max_length=200, required=False)
    name = forms.CharField(max_length=100, required=False)

    def clean(self):
        if self.user.is_superuser:
            return self.cleaned_data
        if self.is_continue and hasattr(self, 'selected_contacts'):
            if len(self.selected_contacts) < self.min_number_of_answers:
                self.errors['__all__'] = self.error_class(
                    ['You need to select at least  %d contacts to proceed' % self.min_number_of_answers])
        return self.cleaned_data

    @staticmethod
    def num(s):
        try:
            return int(s)
        except (ValueError, TypeError):
            return 0

    def __init__(self, user, step0data, wizard, except_ids=set(), *args, **kwargs):
        super(CreateBenchmarkStep3Form, self).__init__(*args, **kwargs)
        self.user = user
        self.min_number_of_answers = self.num(step0data.get('0-minimum_number_of_answers'))
        data = kwargs.get('data') or {}
        self.is_continue = data.get('is_continue', False) and not (
            data.get('add_selected') or data.get('save_and_wizard_goto_step'))
        regions = [('', 'All')]
        regions.extend(list(Region.regions.values_list('id', 'name').order_by('name')))
        self.fields['geo'].choices = regions
        self.fields['geo'].initial = step0data.get('0-geo')
        industries = list(LinkedInIndustry.get_proposal(user.contacts))
        self.fields['industry'].choices = industries
        self.fields['industry'].initial = step0data.getlist('0-industry')
        cleaned_data = {
            'geo': data.get('%s-%s' % (self.prefix, 'geo')) if data else self.fields['geo'].initial,
            'industry': data.getlist('%s-%s' % (self.prefix, 'industry')) if data else self.fields['industry'].initial,
            'name': data.get('%s-%s' % (self.prefix, 'name')),
            'role': data.get('%s-%s' % (self.prefix, 'role')),
        }
        contact_filter = {}
        name_filter = None
        if cleaned_data.get('name'):
            name_filter = Q(last_name__istartswith=cleaned_data.get('name')) | \
                          Q(first_name__istartswith=cleaned_data.get('name'))
        if cleaned_data.get('role'):
            contact_filter['headline__icontains'] = cleaned_data.get('role')
        if cleaned_data.get('industry'):
            contact_filter['company___industry__code__in'] = cleaned_data.get('industry')
        if cleaned_data.get('geo'):
            contact_filter['location__parent__id'] = cleaned_data.get('geo')
        self.contacts_filtered = user.contacts.filter(name_filter, **contact_filter).exclude(id__in=except_ids) \
            .order_by('first_name') if name_filter else \
            user.contacts.filter(**contact_filter).exclude(id__in=except_ids).order_by('first_name')
        for contact in self.contacts_filtered:
            self.fields['contact-{0}-invite'.format(contact.id)] = \
                forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'choose-checkbox'}), required=False)
            contact.invite_element = 'contact-{0}-invite'.format(contact.id)
            self.fields['contact-{0}-secondary'.format(contact.id)] = \
                forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'share-checkbox'}), required=False)
            contact.secondary_element = 'contact-{0}-secondary'.format(contact.id)

        self.add_suggested_contacts(cleaned_data.get('geo'), cleaned_data.get('industry'), user, except_ids)
        wizard.selected_contacts = self.add_selected_contacts(data, except_ids)
        wizard.end_date = self.end_date

    def add_suggested_contacts(self, geo, industry, user=None, exclude_ids=[]):
        self.suggested_contacts = Contact.get_suggested(geo, industry, user, exclude_ids)
        for contact in self.suggested_contacts:
            self.fields['suggested-{0}-invite'.format(contact.id)] = \
                forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'choose-checkbox'}), required=False)
            contact.invite_element = 'suggested-{0}-invite'.format(contact.id)
            self.fields['suggested-{0}-secondary'.format(contact.id)] = \
                forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'share-checkbox'}), required=False)
            contact.secondary_element = 'suggested-{0}-secondary'.format(contact.id)

    def add_selected_contacts(self, data, except_ids):
        selected_ids = []
        selected_secondary_ids = []

        for key in data.keys():
            r = re.match(r'1-selected-(?P<contact_id>\d+)-invite', key)
            if r:
                cid = int(r.group('contact_id'))
                selected_ids.append(cid)
                if data.get('{0}-selected-{1}-secondary'.format(self.prefix, cid)):
                    selected_secondary_ids.append(cid)

        for contact in self.contacts_filtered:
            if data.get('{0}-contact-{1}-invite'.format(self.prefix, contact.id)):
                selected_ids.append(contact.id)
                if data.get('{0}-contact-{1}-secondary'.format(self.prefix, contact.id)):
                    selected_secondary_ids.append(contact.id)
        for contact in self.suggested_contacts:
            if data.get('{0}-suggested-{1}-invite'.format(self.prefix, contact.id)):
                selected_ids.append(contact.id)
                if data.get('{0}-suggested-{1}-secondary'.format(self.prefix, contact.id)):
                    selected_secondary_ids.append(contact.id)

        selected_ids = set(selected_ids)
        selected_secondary_ids = set(selected_secondary_ids)
        selected_ids = selected_ids - except_ids

        count_without_email = 0
        self.selected_contacts = Contact.objects.filter(id__in=selected_ids).select_related('user')
        for contact in self.selected_contacts:
            self.fields['selected-{0}-invite'.format(contact.id)] = \
                forms.BooleanField(initial=True,
                                   widget=forms.CheckboxInput(attrs={'class': 'choose-checkbox', 'checked': 'checked'}),
                                   required=False)
            self.fields['contact-{0}-invite'.format(contact.id)] = \
                forms.BooleanField(initial=True,
                                   widget=forms.CheckboxInput(attrs={'class': 'choose-checkbox', 'checked': 'checked'}),
                                   required=False)
            contact.invite_element = 'selected-{0}-invite'.format(contact.id)
            attr = {'class': 'share-checkbox'}
            if contact.id in selected_secondary_ids:
                attr['checked'] = 'checked'
                contact.allow_secondary = True
            else:
                contact.allow_secondary = False

            self.fields['selected-{0}-secondary'.format(contact.id)] = \
                forms.BooleanField(widget=forms.CheckboxInput(attrs=attr), required=False)
            self.fields['contact-{0}-secondary'.format(contact.id)] = \
                forms.BooleanField(widget=forms.CheckboxInput(attrs=attr), required=False)

            contact.secondary_element = 'selected-{0}-secondary'.format(contact.id)
            if not contact.email:
                count_without_email += 1
        days_to_sent_via_linkedin = math.ceil(float(count_without_email) / 100)
        self.end_date = datetime.now() + timedelta(days=days_to_sent_via_linkedin + BENCHMARK_DURATIONS_DAYS)
        return self.selected_contacts


class CreateBenchmarkStep4Form(CreateBenchmarkStep12Form):
    email_body = forms.CharField(widget=forms.Textarea(attrs={'id': 'email_body', 'hidden': True}), required=False)

    def __init__(self, user, step0data, end_date, *args, **kwargs):
        if step0data.get('0-geo') == u'':
            geo_name = 'Global'
        else:
            geo_name = Region.objects.get(id=int(step0data.get('0-geo'))).name
        if step0data.get('0-industry') == u'':
            industry_name = 'All'
        else:
            industry_name = LinkedInIndustry.objects.get(code=int(step0data.get('0-industry'))).name
        initial = {
            'name': step0data.get('0-name'),
            'geo': step0data.get('0-geo'),
            'geo_name': geo_name,
            'industry': step0data.get('0-industry'),
            'industry_name': industry_name,
            'question_label': step0data.get('0-question_label'),
            'question_text': step0data.get('0-question_text'),
            'question_type': step0data.get('0-question_type'),
            'answer_options': step0data.get('0-answer_options'),
            'units': step0data.get('0-units'),
            'minimum_number_of_answers': step0data.get('0-minimum_number_of_answers'),
            'end_date': end_date.date()
        }
        kwargs['initial'] = initial
        super(CreateBenchmarkStep4Form, self).__init__(user, *args, **kwargs)
        self.end_date = end_date



class AnswerMultipleChoiceForm(forms.Form):
    def __init__(self, choices, *args, **kwargs):
        super(AnswerMultipleChoiceForm, self).__init__(*args, **kwargs)
        self.fields['choice'] = forms.MultipleChoiceField(choices=choices, widget=forms.CheckboxSelectMultiple(),
                                                          label='Your Answer:')


class NumericAnswerForm(forms.Form):
    numeric_box = forms.IntegerField(min_value=-1000000, max_value=1000000)


class RangeAnswerForm(forms.Form):
    min = forms.IntegerField(min_value=-1000000, max_value=1000000, widget=forms.NumberInput(attrs={'placeholder': '1'}))
    max = forms.IntegerField(min_value=-1000000, max_value=1000000, widget=forms.NumberInput(attrs={'placeholder': '1000000'}))

    def __init__(self, *args, **kwargs):
        super(RangeAnswerForm, self).__init__(*args, **kwargs)
        data = kwargs.get('data', {})
        self.fields['max'].min_value = data.get('min', 0)

    def clean_max(self):
        if self.cleaned_data['min'] > self.cleaned_data['max']:
            self.errors['max'] = self.error_class(['Value should be more or equal %d' % self.cleaned_data['min']])
        return self.cleaned_data['max']


class RankingAnswerForm(forms.Form):
    def __init__(self, ranks, *args, **kwargs):
        super(RankingAnswerForm, self).__init__(*args, **kwargs)
        self.ranks = []
        for i, rank in enumerate(ranks):
            field_name = 'rank{0}'.format(rank[0])
            self.fields[field_name] = forms.IntegerField(widget=RankingWidget(attrs={'label': rank[1], 'value': i}))
            self.ranks.append(field_name)


class YesNoAnswerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(YesNoAnswerForm, self).__init__(*args, **kwargs)
        self.fields['Choose Yes or No:'] = forms.TypedChoiceField(coerce=lambda x: x == 'True',
                                                                  choices=((True, 'Yes'), (False, 'No')),
                                                                  widget=forms.RadioSelect)


class DeclineBenchmarkForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(), required=True)

    def __init__(self, benchmark, owner, email, *args, **kwargs):
        super(DeclineBenchmarkForm, self).__init__(*args, **kwargs)
        self.fields['Benchmark name'] = forms.CharField(
            widget=forms.TextInput({'value': benchmark, 'readonly': 'readonly'}), )
        self.fields['Benchmark owner'] = forms.CharField(
            widget=forms.TextInput({'value': owner, 'readonly': 'readonly'}))
        self.fields['Owner email'] = forms.EmailField(widget=forms.TextInput({'value': email, 'readonly': 'readonly'}))


class SendMailForm(forms.Form):
    def __init__(self, user, *args, **kwargs):
        super(SendMailForm, self).__init__(*args, **kwargs)
        self.fields['User'] = forms.CharField(widget=forms.TextInput({'value': user}))
        self.fields['To'] = forms.EmailField(widget=forms.TextInput({'value': user.email}))
        self.fields['Subject'] = forms.CharField()
        self.fields['Email_text'] = forms.CharField(widget=forms.Textarea())


class BenchmarkDetailsForm(forms.Form):
    choices = [
        ('Role', 'Role'), ('Geo', 'Geographic'),  ('Country', 'Country'), ('Industry', 'Industry')]

    def __init__(self, benchmark, *args, **kwargs):
        super(BenchmarkDetailsForm, self).__init__(*args, **kwargs)
        self.fields['Benchmark_Results'] = forms.ChoiceField(choices=benchmark.available_charts,
                                                             initial=benchmark.default_chart)
        self.fields['Contributor_Data'] = forms.ChoiceField(choices=self.choices)


class InviteColleagueForm(forms.Form):
    colleague_email = forms.EmailField()
