from django import forms
from django.contrib.auth.models import User, Group
from .models import UserProfile


class CustomUserCreationForm(forms.ModelForm):

    account_type = forms.ChoiceField(
        choices=UserProfile.ACCOUNT_TYPE_CHOICES,
        label="Account Type"
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        required=False
    )

    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
        required=False
    )

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Groups"
    )

    class Meta:
        model = User
        fields = (
            "username",
            "account_type",
            "password1",
            "password2",
            "groups",
            "is_staff",
            "is_active",
        )

    def clean(self):
        cleaned_data = super().clean()
        account_type = cleaned_data.get("account_type")
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if account_type == "local":
            if not password1:
                self.add_error("password1", "Password is required for local users.")
            if not password2:
                self.add_error("password2", "Password confirmation is required.")
            if password1 and password2 and password1 != password2:
                self.add_error("password2", "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["username"]

        if self.cleaned_data["account_type"] == "m365":
            user.set_unusable_password()
        else:
            user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
            user.groups.set(self.cleaned_data["groups"])

            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "account_type": self.cleaned_data["account_type"]
                }
            )

        return user