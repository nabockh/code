from django import forms


class EmailInvitationRequest(forms.Form):
    email = forms.EmailField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'EMAIL ADDRESS'}))
