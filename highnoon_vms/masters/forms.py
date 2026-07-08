from django import forms
from .models import sys_cmp_master
from .models import sys_bra_master
from .models import sys_div_master

# company form
class CompanyMasterForm(forms.ModelForm):
    class Meta:
        model = sys_cmp_master
        fields = ["cmp_code", "cmp_desc", "cmp_active"]

# branch form
class BranchMasterForm(forms.ModelForm):
    class Meta:
        model = sys_bra_master
        fields = ["bra_code", "bra_desc", "bra_active"]

# divison form
class DivisionMasterForm(forms.ModelForm):
    class Meta:
        model = sys_div_master
        fields = ["div_code", "div_desc", "div_active"]