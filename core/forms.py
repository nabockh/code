from django import forms

class ContactForm(forms.Form):
    first_name = forms.CharField(label='First name',max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField(widget=forms.TextInput())
    comment = forms.CharField(widget=forms.Textarea())