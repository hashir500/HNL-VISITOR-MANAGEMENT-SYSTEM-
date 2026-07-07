from django import forms
from django.contrib.auth.models import User, Group
from accounts.models import UserProfile


class UserManagementForm(forms.ModelForm):
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
        label="Confirm Password",
        widget=forms.PasswordInput,
        required=False
    )

    groups = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        empty_label="Select User Role",
        label="User Role"
    )

    class Meta:
        model = User
        fields = ["username", "account_type", "password1", "password2", "groups", "is_active"]

    def clean(self):
        cleaned = super().clean()
        account_type = cleaned.get("account_type")
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")

        if account_type == "local":
            if not password1 and not self.instance.pk:
                self.add_error("password1", "Password is required for local users.")
            if password1 != password2:
                self.add_error("password2", "Passwords do not match.")

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["username"]

        if self.cleaned_data["account_type"] == "m365":
            user.set_unusable_password()
        elif self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
            user.groups.clear()
            user.groups.add(self.cleaned_data["groups"])

            UserProfile.objects.update_or_create(
                user=user,
                defaults={"account_type": self.cleaned_data["account_type"]}
            )

        return user
