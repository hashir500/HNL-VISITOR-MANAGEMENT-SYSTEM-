from django.db import models

# Create your models here.

class sys_cmp_master(models.Model):
    id = models.AutoField(primary_key= True)
    cmp_code = models.CharField(max_length= 10,unique= True)
    cmp_desc = models.CharField(max_length= 150)
    cmp_active = models.BooleanField(default=True)

    def __str__(self):
        return self.cmp_desc
    
class sys_bra_master(models.Model):
    id = models.AutoField(primary_key= True)
    bra_code = models.CharField(max_length= 10, unique= True)
    bra_desc = models.CharField(max_length= 150)
    bra_active = models.BooleanField(default= True)

    def __str__(self):
        return self.bra_desc
    
class sys_div_master(models.Model):
    id = models.AutoField(primary_key= True)
    div_code = models.CharField(max_length= 10, unique= True)
    div_desc = models.CharField(max_length= 150)
    div_active = models.BooleanField(default= True)

    def __str__(self):
        return self.div_desc
    
class sys_dep_master(models.Model):
    id = models.AutoField(primary_key= True)
    dep_code = models.CharField(max_length=10, unique= True)
    dep_desc = models.CharField(max_length= 150)
    dep_div_code = models.ForeignKey(sys_div_master, on_delete= models.CASCADE)
    dep_active = models.BooleanField(default= True)

    def __str__(self):
        return self.dep_desc
    
class sys_pur_master(models.Model):
    id = models.AutoField(primary_key= True)
    pur_id = models.CharField(max_length= 10, unique= True)
    pur_purpose = models.CharField(max_length= 100)
    pur_active = models.BooleanField(default= True)

    def __str__(self):
        return self.pur_purpose
    
class sys_emp_master(models.Model):
    id = models.AutoField(primary_key=True)
    emp_cmp = models.ForeignKey(sys_cmp_master, on_delete=models.CASCADE)
    emp_bra_code = models.ForeignKey(sys_bra_master, on_delete=models.CASCADE)
    emp_pno = models.CharField(max_length=50, unique=True)
    emp_name = models.CharField(max_length=150)
    emp_designation = models.CharField(max_length=150)
    emp_dep_code = models.ForeignKey(sys_dep_master, on_delete=models.CASCADE)
    emp_email = models.EmailField(blank=True, null=True)
    emp_mobile = models.CharField(max_length=20, blank=True, null=True)
    emp_phone= models.CharField(max_length=20, blank=True, null=True)
    emp_pbx = models.CharField(max_length=20, blank=True, null=True)
    emp_active = models.BooleanField(default=True)

    def __str__(self):
        return self.emp_name
    

class sys_usr_system(models.Model):
    id = models.AutoField(primary_key=True)
    usr_pno = models.CharField(max_length=50, unique=True)
    usr_name = models.CharField(max_length=150)
    usr_designation = models.CharField(max_length=150)

    usr_dep_code = models.ForeignKey(
        sys_dep_master,
        on_delete=models.PROTECT,
    )

    usr_mobile = models.CharField(max_length=20, blank=True, null=True)
    usr_phone = models.CharField(max_length=20, blank=True, null=True)
    usr_email = models.EmailField(unique=True)
    usr_auth = models.CharField(max_length=50, blank=True, null=True)
    usr_loginID = models.CharField(max_length=100, unique=True)
    usr_password = models.CharField(max_length=255, blank=True, null=True)
    usr_access_group = models.CharField(max_length=100)

    # NULL means All Companies
    usr_company = models.ForeignKey(
        sys_cmp_master,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    # NULL means All Branches
    usr_bra_code = models.ForeignKey(
        sys_bra_master,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.usr_name
    
