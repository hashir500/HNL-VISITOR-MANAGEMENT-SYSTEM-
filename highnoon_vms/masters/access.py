from .models import sys_emp_master, sys_usr_system


def get_system_user(django_user):
    if not django_user or not django_user.is_authenticated:
        return None

    return (
        sys_usr_system.objects
        .select_related("usr_company", "usr_bra_code")
        .filter(usr_loginID__iexact=django_user.username)
        .first()
    )


def employees_visible_to_user(django_user):
    employees = sys_emp_master.objects.select_related(
        "emp_cmp",
        "emp_bra_code",
        "emp_dep_code",
    ).all()

    if django_user.is_superuser:
        return employees

    system_user = get_system_user(django_user)

    if not system_user:
        return employees.none()

    if system_user.usr_company_id:
        employees = employees.filter(
            emp_cmp=system_user.usr_company
        )

    if system_user.usr_bra_code_id:
        employees = employees.filter(
            emp_bra_code=system_user.usr_bra_code
        )

    return employees