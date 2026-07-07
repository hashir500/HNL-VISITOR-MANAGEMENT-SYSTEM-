from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserProfile
from .forms import UserManagementForm


from django.db.models import Count, Q

@login_required
@permission_required("users.view_users", raise_exception=True)
def user_list(request):

    search = request.GET.get("search", "")
    role = request.GET.get("role", "")
    account_type = request.GET.get("account_type", "")
    status = request.GET.get("status", "")

    users = (
        User.objects
        .select_related("profile")
        .prefetch_related("groups")
        .order_by("username")
    )

    if search:
        users = users.filter(
            Q(username__icontains=search)
            | Q(email__icontains=search)
        )

    if role:
        users = users.filter(groups__id=role)

    if account_type:
        users = users.filter(profile__account_type=account_type)

    if status == "active":
        users = users.filter(is_active=True)

    elif status == "inactive":
        users = users.filter(is_active=False)

    context = {
        "users": users,

        "roles": Group.objects.all(),

        "search": search,
        "role": role,
        "account_type": account_type,
        "status": status,

        "total_users": User.objects.count(),

        "local_users":
            UserProfile.objects.filter(account_type="local").count(),

        "m365_users":
            UserProfile.objects.filter(account_type="m365").count(),

        "inactive_users":
            User.objects.filter(is_active=False).count(),
    }

    return render(
        request,
        "users/user_list.html",
        context,
    )


@login_required
@permission_required("users.add_users", raise_exception=True)
def user_create(request):
    if request.method == "POST":
        form = UserManagementForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect("user_list")
    else:
        form = UserManagementForm()

    return render(
        request,
        "users/user_form.html",
        {
            "form": form,
            "title": "Create User",
        },
    )


@login_required
@permission_required("users.change_users", raise_exception=True)
def user_update(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        form = UserManagementForm(request.POST, instance=user)

        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect("user_list")

    else:
        form = UserManagementForm(
            instance=user,
            initial={
                "account_type": profile.account_type,
                "groups": user.groups.first(),
            },
        )

    return render(
        request,
        "users/user_form.html",
        {
            "form": form,
            "title": "Edit User",
        },
    )


@login_required
@permission_required("users.delete_users", raise_exception=True)
def user_delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    if request.method == "POST":
        user.delete()
        messages.success(request, "User deleted successfully.")
        return redirect("user_list")

    return render(
        request,
        "users/user_delete.html",
        {
            "user_obj": user,
        },
    )