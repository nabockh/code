from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class MultipleChoiceValidator(object):
    message = _('At least two options should be for this type of answer.')
    code = 'invalid'

    def __call__(self, value):
        options = value.split('\r\n')
        if len(options) > 1 and all(options):
            return value
        raise ValidationError(self.message, code=self.code)


multiple_choice_validator = MultipleChoiceValidator()