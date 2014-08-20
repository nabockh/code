from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class MultipleChoiceValidator(object):
    message = _('At least two options should be for this type of answer.')
    message_max = _('Maximum 10 options can be for this type of answer.')
    message_max_one_item = _('Maximum length of option can be 45.')
    code = 'invalid'

    def __call__(self, value):
        options = value.split('\r\n')
        if len(options) > 1 and all(options):
            if len(options) > 10:
                raise ValidationError(self.message_max, code=self.code)
            for option in options:
                if len(option) > 45:
                    raise ValidationError(self.message_max_one_item, code=self.code)
            return value
        raise ValidationError(self.message, code=self.code)


multiple_choice_validator = MultipleChoiceValidator()