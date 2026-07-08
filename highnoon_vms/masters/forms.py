from django import forms
from .models import sys_cmp_master
from .models import sys_bra_master
from .models import sys_div_master
from .models import sys_dep_master
from .models import sys_emp_master
from .models import sys_pur_master


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

# department form
class DepartmentMasterForm(forms.ModelForm):
    class Meta:
        model = sys_dep_master
        fields = ["dep_code", "dep_desc", "dep_div_code", "dep_active"]

# employee form
class EmployeeMasterForm(forms.ModelForm):
    class Meta:
        model = sys_emp_master
        fields = [
            "emp_cmp",
            "emp_bra_code",
            "emp_pno",
            "emp_name",
            "emp_designation",
            "emp_dep_code",
            "emp_email",
            "emp_mobile",
            "emp_phone",
            "emp_pbx",
            "emp_active",
        ]

# purpose forms
class PurposeMasterForm(forms.ModelForm):
    class Meta:
        model = sys_pur_master
        fields = ["pur_id", "pur_purpose", "pur_active"]