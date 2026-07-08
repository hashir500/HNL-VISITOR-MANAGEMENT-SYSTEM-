from django import forms
from .models import sys_cmp_master


class CompanyMasterForm(forms.ModelForm):
    class Meta:
        model = sys_cmp_master
        fields = ["cmp_code", "cmp_desc", "cmp_active"]