from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from core.models import Team

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    favorite_team = forms.ModelChoiceField(
        queryset=Team.objects.all(),
        required=False,
        empty_label="Select your favorite team"
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "favorite_team")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user 