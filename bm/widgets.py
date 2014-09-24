from django.forms.widgets import HiddenInput
from django.template.defaultfilters import safe


class RankingWidget(HiddenInput):
    input_type = 'hidden'

    def render(self, name, value, attrs=None):
        output = super(RankingWidget, self).render(name, value, attrs)
        return safe(output + ('<label for=%s>%s</label>' % (attrs['id'], self.attrs['label'])))