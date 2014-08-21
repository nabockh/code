from django import forms


class ContactForm(forms.Form):
    first_name = forms.CharField(label='First name', max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField(widget=forms.TextInput())
    comment = forms.CharField(widget=forms.Textarea())

    def __init__(self, request=None, *args, **kwargs):
        if request and request.user.is_authenticated():
            initial = {
                'first_name': request.user.first_name,
                'last_name':  request.user.last_name,
                'email':      request.user.email
            }
            kwargs['initial'] = initial
        super(ContactForm, self).__init__(*args, **kwargs)
