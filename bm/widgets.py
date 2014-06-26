from django.forms.widgets import HiddenInput
from django.template.defaultfilters import safe


class RankingWidget(HiddenInput):
    input_type = 'hidden'

    def render(self, name, value, attrs=None):
        output = super(RankingWidget, self).render(name, value, attrs)
        return safe(str(output) + ('<label for={0}>{1}</label>'.format(attrs['id'], self.attrs['label'])))