from django.db import models


class UserManagementPermission(models.Model):
    class Meta:
        managed = False
        permissions = [
            ("view_users", "Can view users"),
            ("add_users", "Can add users"),
            ("change_users", "Can change users"),
            ("delete_users", "Can delete users"),
        ]