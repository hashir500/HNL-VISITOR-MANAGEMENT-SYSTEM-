from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime

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
    if request.user.is_superuser:
        return None

    login_id = (
        request.user.username
        or request.user.email
        or ""
    ).strip().lower()

    return (
        sys_usr_system.objects
        .select_related("usr_company", "usr_bra_code")
        .filter(usr_loginID__iexact=login_id)
        .first()
    )


def get_visit_access_settings(request):
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
    value = (value or "").strip()
    if not value or value.upper() == "ALL":
        return None
    return value


def get_selected_access_filters(request, access):
    if access["can_select_company"]:
        selected_company = normalize_filter_value(request.GET.get("company"))
    else:
        selected_company = access["assigned_company_code"]

    if access["can_select_branch"]:
        selected_branch = normalize_filter_value(request.GET.get("branch"))
    else:
        selected_branch = access["assigned_branch_code"]

    return selected_company, selected_branch


def apply_employee_access_filter(queryset, access, selected_company=None, selected_branch=None):
    if not access["has_user_master"]:
        return queryset.none()
    if not access["can_select_company"]:
        selected_company = access["assigned_company_code"]
    if not access["can_select_branch"]:
        selected_branch = access["assigned_branch_code"]

    if selected_company:
        queryset = queryset.filter(emp_cmp__cmp_code=selected_company)
    if selected_branch:
        queryset = queryset.filter(emp_bra_code__bra_code=selected_branch)
    return queryset


def apply_visit_access_filter(queryset, access, selected_company=None, selected_branch=None):
    if not access["has_user_master"]:
        return queryset.none()
    if not access["can_select_company"]:
        selected_company = access["assigned_company_code"]
    if not access["can_select_branch"]:
        selected_branch = access["assigned_branch_code"]

    if selected_company:
        queryset = queryset.filter(employee__emp_cmp__cmp_code=selected_company)
    if selected_branch:
        queryset = queryset.filter(employee__emp_bra_code__bra_code=selected_branch)
    return queryset


def user_can_access_employee(request, employee_obj):
    access = get_visit_access_settings(request)
    if not access["has_user_master"]:
        return False
    if request.user.is_superuser:
        return True
    if access["assigned_company_code"] and (not employee_obj.emp_cmp or employee_obj.emp_cmp.cmp_code != access["assigned_company_code"]):
        return False
    if access["assigned_branch_code"] and (not employee_obj.emp_bra_code or employee_obj.emp_bra_code.bra_code != access["assigned_branch_code"]):
        return False
    return True


def get_visit_list_redirect(request):
    query_parameters = {}
    current_search = (request.POST.get("current_search") or "").strip()
    current_company = (request.POST.get("current_company") or "").strip()
    current_branch = (request.POST.get("current_branch") or "").strip()

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
@permission_required("visits.view_visit", raise_exception=True)
def get_employees_by_branch(request):
    branch_code = (request.GET.get("branch") or "").strip()
    search_term = (request.GET.get("q") or "").strip()
    search_all = request.GET.get("search_all") == "1"
    save_session = request.GET.get("save_session") == "1"
    clear_session = request.GET.get("clear_session") == "1"

    if clear_session:
        request.session.pop("vms_modal_selected_branch", None)
        return JsonResponse({"employees": [], "status": "cleared"})

    if save_session and branch_code and branch_code.upper() != "ALL":
        request.session["vms_modal_selected_branch"] = branch_code

    access = get_visit_access_settings(request)
    employees = sys_emp_master.objects.select_related(
        "emp_cmp", "emp_bra_code", "emp_dep_code"
    ).filter(emp_active=True)

    # Clean branch code (e.g. '02' -> '2' for fallback matching)
    clean_branch = branch_code.lstrip('0') if branch_code else ''

    # Filter by branch unless searching globally
    if not search_all and branch_code and branch_code.upper() != "ALL":
        employees = employees.filter(
            Q(emp_bra_code__bra_code__iexact=branch_code) |
            Q(emp_bra_code__bra_code__icontains=branch_code) |
            (Q(emp_bra_code__bra_code__icontains=clean_branch) if clean_branch else Q())
        )
    elif search_all:
        # If user master restricts company, apply it, but allow searching across branches
        if access["has_user_master"] and not access["can_select_company"] and access["assigned_company_code"]:
            employees = employees.filter(emp_cmp__cmp_code=access["assigned_company_code"])

    # Live search query by Name or PNO
    if search_term:
        employees = employees.filter(
            Q(emp_name__icontains=search_term) |
            Q(emp_pno__icontains=search_term)
        )

    employees = employees.order_by("emp_name")[:100]

    data = []
    for emp in employees:
        dep_str = f" - {emp.emp_dep_code.dep_code}" if emp.emp_dep_code else ""
        cmp_str = f" - {emp.emp_cmp.cmp_code}" if emp.emp_cmp else ""
        bra_str = f" - {emp.emp_bra_code.bra_code}" if emp.emp_bra_code else ""
        data.append({
            "id": emp.pk,
            "text": f"{emp.emp_pno} - {emp.emp_name}{dep_str}{cmp_str}{bra_str}"
        })

    return JsonResponse({"results": data, "employees": data})


@login_required
@permission_required("visits.can_view_backlogs", raise_exception=True)
def get_last_employee_for_visitor(request, visitor_id):
    last_visit = visit.objects.filter(visitor_id=visitor_id).order_by('-check_in_time').first()
    if last_visit and last_visit.employee:
        return JsonResponse({'employee_id': last_visit.employee.pk})
    return JsonResponse({'employee_id': None})


@login_required
@permission_required("visits.view_visit", raise_exception=True)
def visit_list(request):
    search = (request.GET.get("search") or "").strip()
    today = timezone.localdate()
    access = get_visit_access_settings(request)
    selected_company, selected_branch = get_selected_access_filters(request, access)

    start_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    end_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))

    visits = visit.objects.select_related(
        "visitor", "employee", "employee__emp_cmp", "employee__emp_bra_code", "employee__emp_dep_code", "visitor_card"
    ).filter(
        (Q(check_in_time__range=(start_of_day, end_of_day)) | Q(status="Checked In")),
        is_backlog=False
    )

    visits = apply_visit_access_filter(visits, access, selected_company, selected_branch)

    if search:
        visits = visits.filter(
            Q(visitor_card__CRD_No__icontains=search)
            | Q(visitor__visitor_name__icontains=search)
            | Q(employee__emp_name__icontains=search)
            | Q(employee__emp_pno__icontains=search)
        )

    visits = visits.order_by("-check_in_time")
    employees = sys_emp_master.objects.select_related("emp_cmp", "emp_bra_code", "emp_dep_code").filter(emp_active=True)
    employees = apply_employee_access_filter(employees, access, selected_company, selected_branch).order_by("emp_name")
    
    visitors = visitor.objects.all().order_by("visitor_name")
    cards = visitor_card.objects.filter(CRD_Active=True).order_by("CRD_No")
    purposes = sys_pur_master.objects.filter(pur_active=True).order_by("pur_purpose")
    companies = sys_cmp_master.objects.all().order_by("cmp_code")
    branches = sys_bra_master.objects.all().order_by("bra_code")

    if not access["can_select_company"]:
        companies = companies.filter(cmp_code=access["assigned_company_code"])
    if not access["can_select_branch"]:
        branches = branches.filter(bra_code=access["assigned_branch_code"])

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
            "selected_visitor_id": request.GET.get("visitor_id"),
            "open_add_visit": request.GET.get("open_add_visit"),
            "saved_modal_branch": request.session.get("vms_modal_selected_branch", ""),
        },
    )


@login_required
@permission_required("visits.change_visit", raise_exception=True)
def visit_checkout(request, visit_id):
    visit_obj = get_object_or_404(
        visit.objects.select_related("employee", "employee__emp_cmp", "employee__emp_bra_code", "visitor_card"),
        visit_id=visit_id,
    )

    if not user_can_access_employee(request, visit_obj.employee):
        messages.error(request, "You do not have access to check out this visit.")
        return get_visit_list_redirect(request)

    if request.method == "POST":
        if visit_obj.status != "Checked In":
            messages.warning(request, "This visitor has already been checked out.")
            return get_visit_list_redirect(request)

        visit_obj.check_out_time = timezone.now()
        visit_obj.status = "Checked Out"

        if visit_obj.visitor_card:
            visit_obj.visitor_card.CRD_Active = True
            visit_obj.visitor_card.save(update_fields=["CRD_Active"])

        visit_obj.save(update_fields=["check_out_time", "status"])
        messages.success(request, "Visitor checked out successfully.")

    return get_visit_list_redirect(request)


@login_required
@permission_required("visits.add_visit", raise_exception=True)
def visit_create(request):
    if request.method != "POST":
        return redirect("visit_list")

    selected_modal_branch = request.POST.get('selected_branch', '').strip()
    if selected_modal_branch:
        request.session['vms_modal_selected_branch'] = selected_modal_branch

    visitor_obj = get_object_or_404(visitor, visitor_id=request.POST.get("visitor"))
    employee_obj = get_object_or_404(
        sys_emp_master.objects.select_related("emp_cmp", "emp_bra_code", "emp_dep_code"),
        pk=request.POST.get("employee")
    )

    if not user_can_access_employee(request, employee_obj):
        messages.error(request, "You do not have access to create a visit for the selected employee.")
        return get_visit_list_redirect(request)

    selected_card = get_object_or_404(visitor_card, id=request.POST.get("visitor_card"))

    if not selected_card.CRD_Active:
        messages.error(request, f"Card {selected_card.CRD_No} is currently unavailable.")
        return get_visit_list_redirect(request)

    if visit.objects.filter(visitor_card=selected_card, status="Checked In").exists():
        messages.error(request, f"Card {selected_card.CRD_No} is already in use.")
        return get_visit_list_redirect(request)

    purpose_obj = get_object_or_404(sys_pur_master, pur_id=request.POST.get("purpose"), pur_active=True)
    purpose_name = (purpose_obj.pur_purpose or "").strip()

    if purpose_name.lower() in ["other", "others"]:
        visit_purpose = (request.POST.get("other_purpose") or "").strip()
        if not visit_purpose:
            messages.error(request, "Please specify the purpose.")
            return get_visit_list_redirect(request)
    else:
        visit_purpose = purpose_name

    visit.objects.create(
        visitor=visitor_obj,
        employee=employee_obj,
        visitor_card=selected_card,
        visit_purpose=visit_purpose,
        is_backlog=False
    )

    selected_card.CRD_Active = False
    selected_card.save(update_fields=["CRD_Active"])
    messages.success(request, "Visit created successfully.")
    return get_visit_list_redirect(request)


@login_required
@permission_required("visits.can_view_backlogs", raise_exception=True)
def backlog_list_create(request):
    if request.method == 'POST':
        visitor_id = request.POST.get('visitor')
        employee_id = request.POST.get('employee')
        card_id = request.POST.get('visitor_card')
        purpose_id = request.POST.get('purpose')
        other_purpose = request.POST.get('other_purpose', '').strip()
        selected_modal_branch = request.POST.get('selected_branch', '').strip()
        
        if selected_modal_branch:
            request.session['vms_modal_selected_branch'] = selected_modal_branch

        checkin_str = request.POST.get('check_in_time')
        checkout_str = request.POST.get('check_out_time')

        check_in_time = parse_datetime(checkin_str) if checkin_str else None
        check_out_time = parse_datetime(checkout_str) if checkout_str else None

        if not visitor_id or not employee_id or not card_id or not purpose_id or not check_in_time:
            messages.error(request, "Visitor, Host Employee, Card, Purpose, and Check-In time are required.")
        elif check_out_time and check_out_time <= check_in_time:
            messages.error(request, "Error: Checkout time must be chronologically after Check-In time.")
        else:
            try:
                visitor_obj = get_object_or_404(visitor, visitor_id=visitor_id)
                employee_obj = get_object_or_404(sys_emp_master, pk=employee_id)
                selected_card = get_object_or_404(visitor_card, id=card_id)
                purpose_obj = get_object_or_404(sys_pur_master, pur_id=purpose_id)

                purpose_name = (purpose_obj.pur_purpose or "").strip()
                if purpose_name.lower() in ["other", "others"]:
                    visit_purpose = other_purpose
                    if not visit_purpose:
                        messages.error(request, "Please specify the custom purpose.")
                        return redirect('backlog_list_create')
                else:
                    visit_purpose = purpose_name

                final_status = "Checked Out" if check_out_time else "Checked In"

                visit.objects.create(
                    visitor=visitor_obj,
                    employee=employee_obj,
                    visitor_card=selected_card,
                    visit_purpose=visit_purpose,
                    check_in_time=check_in_time,
                    check_out_time=check_out_time,
                    status=final_status,
                    is_backlog=True
                )
                messages.success(request, f"Backlogged visit for {visitor_obj.visitor_name} recorded successfully!")
                
                request.session['last_backlog_checkin'] = checkin_str
                request.session['last_backlog_checkout'] = checkout_str or ''

                return redirect(reverse('backlog_list_create') + '?open_add_backlog=1')

            except Exception as e:
                messages.error(request, f"Database Write Error: {str(e)}")

    search = (request.GET.get('search') or '').strip()
    selected_visitor_id = request.GET.get('selected_visitor_id')

    access = get_visit_access_settings(request)
    selected_company, selected_branch = get_selected_access_filters(request, access)

    backlogs = visit.objects.filter(is_backlog=True).select_related(
        "visitor", "employee", "employee__emp_cmp", "employee__emp_bra_code", "employee__emp_dep_code", "visitor_card"
    )
    backlogs = apply_visit_access_filter(backlogs, access, selected_company, selected_branch)

    if search:
        backlogs = backlogs.filter(
            Q(visitor_card__CRD_No__icontains=search)
            | Q(visitor__visitor_name__icontains=search)
            | Q(employee__emp_name__icontains=search)
            | Q(employee__emp_pno__icontains=search)
        )
    backlogs = backlogs.order_by('-check_in_time')

    visitors = visitor.objects.all().order_by('visitor_name')
    employees = sys_emp_master.objects.filter(emp_active=True)
    employees = apply_employee_access_filter(employees, access, selected_company, selected_branch).order_by('emp_name')
    cards = visitor_card.objects.all().order_by('CRD_No')
    purposes = sys_pur_master.objects.filter(pur_active=True).order_by('pur_purpose')

    companies = sys_cmp_master.objects.all().order_by('cmp_code')
    branches = sys_bra_master.objects.all().order_by('bra_code')

    if not access["can_select_company"]:
        companies = companies.filter(cmp_code=access["assigned_company_code"])
    if not access["can_select_branch"]:
        branches = branches.filter(bra_code=access["assigned_branch_code"])

    context = {
        'visitors': visitors,
        'employees': employees,
        'cards': cards,
        'purposes': purposes,
        'backlogs': backlogs,
        'companies': companies,
        'branches': branches,
        'search': search,
        'selected_company': selected_company or "ALL",
        'selected_branch': selected_branch or "ALL",
        'can_select_company': access["can_select_company"],
        'can_select_branch': access["can_select_branch"],
        'has_visit_access': access["has_user_master"],
        'selected_visitor_id': selected_visitor_id,
        'open_add_backlog': request.GET.get('open_add_backlog'),
        'last_checkin': request.session.get('last_backlog_checkin', ''),
        'last_checkout': request.session.get('last_backlog_checkout', ''),
        'saved_modal_branch': request.session.get("vms_modal_selected_branch", ""),
    }
    return render(request, 'visits/backlogs.html', context)


@login_required
@permission_required("visits.can_view_backlogs", raise_exception=True)
def backlog_edit(request, visit_id):
    visit_obj = get_object_or_404(visit, visit_id=visit_id, is_backlog=True)

    if not user_can_access_employee(request, visit_obj.employee):
        messages.error(request, "You do not have permission to edit this backlog entry.")
        return redirect('backlog_list_create')

    if request.method == "POST":
        visitor_id = request.POST.get('visitor')
        employee_id = request.POST.get('employee')
        card_id = request.POST.get('visitor_card')
        purpose_id = request.POST.get('purpose')
        other_purpose = request.POST.get('other_purpose', '').strip()

        checkin_str = request.POST.get('check_in_time')
        checkout_str = request.POST.get('check_out_time')

        check_in_time = parse_datetime(checkin_str) if checkin_str else None
        check_out_time = parse_datetime(checkout_str) if checkout_str else None

        if not visitor_id or not employee_id or not card_id or not purpose_id or not check_in_time:
            messages.error(request, "Visitor, Host Employee, Card, Purpose, and Check-In time are required.")
            return redirect('backlog_list_create')

        if check_out_time and check_out_time <= check_in_time:
            messages.error(request, "Error: Checkout time must be chronologically after Check-In time.")
            return redirect('backlog_list_create')

        try:
            visitor_obj = get_object_or_404(visitor, visitor_id=visitor_id)
            employee_obj = get_object_or_404(sys_emp_master, pk=employee_id)
            selected_card = get_object_or_404(visitor_card, id=card_id)
            purpose_obj = get_object_or_404(sys_pur_master, pur_id=purpose_id)

            purpose_name = (purpose_obj.pur_purpose or "").strip()
            if purpose_name.lower() in ["other", "others"]:
                visit_purpose = other_purpose
                if not visit_purpose:
                    messages.error(request, "Please specify the custom purpose.")
                    return redirect('backlog_list_create')
            else:
                visit_purpose = purpose_name

            final_status = "Checked Out" if check_out_time else "Checked In"

            visit_obj.visitor = visitor_obj
            visit_obj.employee = employee_obj
            visit_obj.visitor_card = selected_card
            visit_obj.visit_purpose = visit_purpose
            visit_obj.check_in_time = check_in_time
            visit_obj.check_out_time = check_out_time
            visit_obj.status = final_status
            visit_obj.save()

            messages.success(request, f"Backlog entry #{visit_obj.visit_id} updated successfully!")
        except Exception as e:
            messages.error(request, f"Database Update Error: {str(e)}")

    return redirect('backlog_list_create')


@login_required
@permission_required("visits.can_view_backlogs", raise_exception=True)
def backlog_delete(request, visit_id):
    visit_obj = get_object_or_404(visit, visit_id=visit_id, is_backlog=True)

    if not user_can_access_employee(request, visit_obj.employee):
        messages.error(request, "You do not have permission to delete this backlog entry.")
        return redirect('backlog_list_create')

    if request.method == "POST":
        try:
            visit_id_num = visit_obj.visit_id
            visit_obj.delete()
            messages.success(request, f"Backlog record #{visit_id_num} deleted successfully.")
        except Exception as e:
            messages.error(request, f"Delete Error: {str(e)}")

    return redirect('backlog_list_create')