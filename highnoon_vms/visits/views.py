from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import visit
from visitors.models import visitor, visitor_card
from masters.models import (
    sys_bra_master,
    sys_cmp_master,
    sys_emp_master,
    sys_pur_master,
    sys_usr_system,
)


def get_logged_in_vms_user(request):
    """
    Return the sys_usr_system record linked to the logged-in
    Django authentication user.

    Superusers are allowed to operate without a User Master record.
    """
    if request.user.is_superuser:
        return None

    login_id = (
        request.user.username
        or request.user.email
        or ""
    ).strip().lower()

    return (
        sys_usr_system.objects
        .select_related(
            "usr_company",
            "usr_bra_code",
        )
        .filter(usr_loginID__iexact=login_id)
        .first()
    )


def get_visit_access_settings(request):
    """
    Resolve the logged-in user's Company and Branch access.

    Rules:
    - Superuser: all companies and all branches.
    - usr_company is None: all companies.
    - usr_bra_code is None: all branches.
    - Otherwise, access is restricted to the assigned values.
    """
    user_master = get_logged_in_vms_user(request)

    if request.user.is_superuser:
        return {
            "user_master": None,
            "has_user_master": True,
            "can_select_company": True,
            "can_select_branch": True,
            "assigned_company_code": None,
            "assigned_branch_code": None,
        }

    if not user_master:
        return {
            "user_master": None,
            "has_user_master": False,
            "can_select_company": False,
            "can_select_branch": False,
            "assigned_company_code": None,
            "assigned_branch_code": None,
        }

    assigned_company_code = (
        user_master.usr_company.cmp_code
        if user_master.usr_company
        else None
    )

    assigned_branch_code = (
        user_master.usr_bra_code.bra_code
        if user_master.usr_bra_code
        else None
    )

    return {
        "user_master": user_master,
        "has_user_master": True,
        "can_select_company": user_master.usr_company is None,
        "can_select_branch": user_master.usr_bra_code is None,
        "assigned_company_code": assigned_company_code,
        "assigned_branch_code": assigned_branch_code,
    }


def normalize_filter_value(value):
    """
    Convert empty and ALL dropdown values to None.
    """
    value = (value or "").strip()

    if not value or value.upper() == "ALL":
        return None

    return value


def get_selected_access_filters(request, access):
    """
    Determine the active Company and Branch filters.

    Restricted users cannot override their assigned values by
    manually changing the query string.
    """
    if access["can_select_company"]:
        selected_company = normalize_filter_value(
            request.GET.get("company")
        )
    else:
        selected_company = access["assigned_company_code"]

    if access["can_select_branch"]:
        selected_branch = normalize_filter_value(
            request.GET.get("branch")
        )
    else:
        selected_branch = access["assigned_branch_code"]

    return selected_company, selected_branch


def apply_employee_access_filter(
    queryset,
    access,
    selected_company=None,
    selected_branch=None,
):
    """
    Apply Company and Branch access rules to an employee queryset.
    """
    if not access["has_user_master"]:
        return queryset.none()

    if not access["can_select_company"]:
        selected_company = access["assigned_company_code"]

    if not access["can_select_branch"]:
        selected_branch = access["assigned_branch_code"]

    if selected_company:
        queryset = queryset.filter(
            emp_cmp__cmp_code=selected_company
        )

    if selected_branch:
        queryset = queryset.filter(
            emp_bra_code__bra_code=selected_branch
        )

    return queryset


def apply_visit_access_filter(
    queryset,
    access,
    selected_company=None,
    selected_branch=None,
):
    """
    Apply Company and Branch access rules through the employee
    associated with each visit.
    """
    if not access["has_user_master"]:
        return queryset.none()

    if not access["can_select_company"]:
        selected_company = access["assigned_company_code"]

    if not access["can_select_branch"]:
        selected_branch = access["assigned_branch_code"]

    if selected_company:
        queryset = queryset.filter(
            employee__emp_cmp__cmp_code=selected_company
        )

    if selected_branch:
        queryset = queryset.filter(
            employee__emp_bra_code__bra_code=selected_branch
        )

    return queryset


def user_can_access_employee(request, employee_obj):
    """
    Server-side access check for the employee selected in Add Visit.
    """
    access = get_visit_access_settings(request)

    if not access["has_user_master"]:
        return False

    if request.user.is_superuser:
        return True

    if (
        access["assigned_company_code"]
        and (
            not employee_obj.emp_cmp
            or employee_obj.emp_cmp.cmp_code
            != access["assigned_company_code"]
        )
    ):
        return False

    if (
        access["assigned_branch_code"]
        and (
            not employee_obj.emp_bra_code
            or employee_obj.emp_bra_code.bra_code
            != access["assigned_branch_code"]
        )
    ):
        return False

    return True


def get_visit_list_redirect(request):
    """
    Preserve active filters after Add Visit or Checkout.

    The HTML will submit these hidden fields:
    current_search, current_company and current_branch.
    """
    query_parameters = {}

    current_search = (
        request.POST.get("current_search") or ""
    ).strip()

    current_company = (
        request.POST.get("current_company") or ""
    ).strip()

    current_branch = (
        request.POST.get("current_branch") or ""
    ).strip()

    if current_search:
        query_parameters["search"] = current_search

    if current_company:
        query_parameters["company"] = current_company

    if current_branch:
        query_parameters["branch"] = current_branch

    url = reverse("visit_list")

    if query_parameters:
        url = f"{url}?{urlencode(query_parameters)}"

    return redirect(url)


@login_required
@permission_required(
    "visits.view_visit",
    raise_exception=True,
)
def visit_list(request):
    search = (request.GET.get("search") or "").strip()
    today = timezone.localdate()

    access = get_visit_access_settings(request)

    selected_company, selected_branch = (
        get_selected_access_filters(request, access)
    )

    start_of_day = timezone.make_aware(
        timezone.datetime.combine(
            today,
            timezone.datetime.min.time(),
        )
    )

    end_of_day = timezone.make_aware(
        timezone.datetime.combine(
            today,
            timezone.datetime.max.time(),
        )
    )

    visits = (
        visit.objects
        .select_related(
            "visitor",
            "employee",
            "employee__emp_cmp",
            "employee__emp_bra_code",
            "employee__emp_dep_code",
            "visitor_card",
        )
        .filter(
            Q(
                check_in_time__range=(
                    start_of_day,
                    end_of_day,
                )
            )
            | Q(status="Checked In")
        )
    )

    visits = apply_visit_access_filter(
        queryset=visits,
        access=access,
        selected_company=selected_company,
        selected_branch=selected_branch,
    )

    if search:
        visits = visits.filter(
            Q(visitor_card__CRD_No__icontains=search)
            | Q(visitor__visitor_name__icontains=search)
            | Q(employee__emp_name__icontains=search)
            | Q(employee__emp_pno__icontains=search)
        )

    visits = visits.order_by("-check_in_time")

    employees = (
        sys_emp_master.objects
        .select_related(
            "emp_cmp",
            "emp_bra_code",
            "emp_dep_code",
        )
        .filter(emp_active=True)
    )

    employees = apply_employee_access_filter(
        queryset=employees,
        access=access,
        selected_company=selected_company,
        selected_branch=selected_branch,
    ).order_by("emp_name")

    visitors = (
        visitor.objects
        .all()
        .order_by("visitor_name")
    )

    cards = (
        visitor_card.objects
        .filter(CRD_Active=True)
        .order_by("CRD_No")
    )

    purposes = (
        sys_pur_master.objects
        .filter(pur_active=True)
        .order_by("pur_purpose")
    )

    companies = (
        sys_cmp_master.objects
        .all()
        .order_by("cmp_code")
    )

    branches = (
        sys_bra_master.objects
        .all()
        .order_by("bra_code")
    )

    # Restricted users only receive the Company/Branch they can access.
    if not access["can_select_company"]:
        companies = companies.filter(
            cmp_code=access["assigned_company_code"]
        )

    if not access["can_select_branch"]:
        branches = branches.filter(
            bra_code=access["assigned_branch_code"]
        )

    return render(
        request,
        "visits/visit_list.html",
        {
            "visits": visits,
            "visitors": visitors,
            "employees": employees,
            "cards": cards,
            "purposes": purposes,
            "companies": companies,
            "branches": branches,
            "search": search,
            "today": today,
            "selected_company": selected_company or "ALL",
            "selected_branch": selected_branch or "ALL",
            "can_select_company": access["can_select_company"],
            "can_select_branch": access["can_select_branch"],
            "has_visit_access": access["has_user_master"],
            "selected_visitor_id": request.GET.get(
                "visitor_id"
            ),
            "open_add_visit": request.GET.get(
                "open_add_visit"
            ),
        },
    )


@login_required
@permission_required(
    "visits.change_visit",
    raise_exception=True,
)
def visit_checkout(request, visit_id):
    visit_obj = get_object_or_404(
        visit.objects.select_related(
            "employee",
            "employee__emp_cmp",
            "employee__emp_bra_code",
            "visitor_card",
        ),
        visit_id=visit_id,
    )

    if not user_can_access_employee(
        request,
        visit_obj.employee,
    ):
        messages.error(
            request,
            "You do not have access to check out this visit.",
        )
        return get_visit_list_redirect(request)

    if request.method == "POST":
        if visit_obj.status != "Checked In":
            messages.warning(
                request,
                "This visitor has already been checked out.",
            )
            return get_visit_list_redirect(request)

        visit_obj.check_out_time = timezone.now()
        visit_obj.status = "Checked Out"

        if visit_obj.visitor_card:
            visit_obj.visitor_card.CRD_Active = True
            visit_obj.visitor_card.save(
                update_fields=["CRD_Active"]
            )

        visit_obj.save(
            update_fields=[
                "check_out_time",
                "status",
            ]
        )

        messages.success(
            request,
            "Visitor checked out successfully.",
        )

    return get_visit_list_redirect(request)


@login_required
@permission_required(
    "visits.add_visit",
    raise_exception=True,
)
def visit_create(request):
    if request.method != "POST":
        return redirect("visit_list")

    visitor_obj = get_object_or_404(
        visitor,
        visitor_id=request.POST.get("visitor"),
    )

    employee_obj = get_object_or_404(
        sys_emp_master.objects.select_related(
            "emp_cmp",
            "emp_bra_code",
            "emp_dep_code",
        ),
        pk=request.POST.get("employee"),
    )

    if not user_can_access_employee(
        request,
        employee_obj,
    ):
        messages.error(
            request,
            "You do not have access to create a visit for "
            "the selected employee.",
        )
        return get_visit_list_redirect(request)

    selected_card = get_object_or_404(
        visitor_card,
        id=request.POST.get("visitor_card"),
    )

    if not selected_card.CRD_Active:
        messages.error(
            request,
            f"Card {selected_card.CRD_No} is currently unavailable.",
        )
        return get_visit_list_redirect(request)

    card_in_use = visit.objects.filter(
        visitor_card=selected_card,
        status="Checked In",
    ).exists()

    if card_in_use:
        messages.error(
            request,
            f"Card {selected_card.CRD_No} is already in use.",
        )
        return get_visit_list_redirect(request)

    purpose_obj = get_object_or_404(
        sys_pur_master,
        pur_id=request.POST.get("purpose"),
        pur_active=True,
    )

    purpose_name = (
        purpose_obj.pur_purpose or ""
    ).strip()

    if purpose_name.lower() in ["other", "others"]:
        visit_purpose = (
            request.POST.get("other_purpose") or ""
        ).strip()

        if not visit_purpose:
            messages.error(
                request,
                "Please specify the purpose.",
            )
            return get_visit_list_redirect(request)
    else:
        visit_purpose = purpose_name

    visit.objects.create(
        visitor=visitor_obj,
        employee=employee_obj,
        visitor_card=selected_card,
        visit_purpose=visit_purpose,
    )

    selected_card.CRD_Active = False
    selected_card.save(
        update_fields=["CRD_Active"]
    )

    messages.success(
        request,
        "Visit created successfully.",
    )

    return get_visit_list_redirect(request)
