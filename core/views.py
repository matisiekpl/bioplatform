from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import Team, Membership
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm, TeamForm, MembershipForm


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("team_list")
    else:
        form = UserRegistrationForm()
    return render(request, "core/auth/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("team_list")
    else:
        form = AuthenticationForm()
    return render(request, "core/auth/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = "core/teams/team_list.html"
    context_object_name = "teams"

    def get_queryset(self):
        return Team.objects.filter(memberships__user=self.request.user)


class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = "core/teams/team_form.html"
    success_url = reverse_lazy("team_list")

    def form_valid(self, form):
        team = form.save()
        Membership.objects.create(
            user=self.request.user, team=team, role=Membership.Role.ADMIN
        )
        return super().form_valid(form)


class TeamUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Team
    form_class = TeamForm
    template_name = "core/teams/team_form.html"
    success_url = reverse_lazy("team_list")

    def test_func(self):
        team = self.get_object()
        return Membership.objects.filter(
            user=self.request.user, team=team, role=Membership.Role.ADMIN
        ).exists()


class TeamDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Team
    template_name = "core/teams/team_confirm_delete.html"
    success_url = reverse_lazy("team_list")

    def test_func(self):
        team = self.get_object()
        return Membership.objects.filter(
            user=self.request.user, team=team, role=Membership.Role.ADMIN
        ).exists()


@login_required
def team_members(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if not Membership.objects.filter(
        user=request.user, team=team, role=Membership.Role.ADMIN
    ).exists():
        return redirect("team_list")

    if request.method == "POST":
        form = MembershipForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            if Membership.objects.filter(user=user, team=team).exists():
                form.add_error("user", "This user is already a member of this team.")
            else:
                membership = form.save(commit=False)
                membership.team = team
                membership.save()
                return redirect("team_members", pk=team.pk)
    else:
        form = MembershipForm()

    memberships = Membership.objects.filter(team=team)
    return render(
        request,
        "core/teams/team_members.html",
        {"team": team, "memberships": memberships, "form": form, "is_admin": True},
    )


@login_required
def remove_team_member(request, team_pk, membership_pk):
    team = get_object_or_404(Team, pk=team_pk)
    if not Membership.objects.filter(
        user=request.user, team=team, role=Membership.Role.ADMIN
    ).exists():
        return JsonResponse({"error": "Permission denied"}, status=403)

    membership = get_object_or_404(Membership, pk=membership_pk, team=team)
    if (
        membership.role == Membership.Role.ADMIN
        and Membership.objects.filter(team=team, role=Membership.Role.ADMIN).count()
        == 1
    ):
        return JsonResponse({"error": "Cannot remove the last admin"}, status=400)

    membership.delete()
    return redirect("team_members", pk=team_pk)


@login_required
def update_member_role(request, team_pk, membership_pk):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    team = get_object_or_404(Team, pk=team_pk)
    if not Membership.objects.filter(
        user=request.user, team=team, role=Membership.Role.ADMIN
    ).exists():
        return JsonResponse({"error": "Permission denied"}, status=403)

    membership = get_object_or_404(Membership, pk=membership_pk, team=team)
    new_role = request.POST.get("role")

    if new_role not in [role[0] for role in Membership.Role.choices]:
        return JsonResponse({"error": "Invalid role"}, status=400)

    # Check if this would remove the last admin
    if membership.role == Membership.Role.ADMIN and new_role != Membership.Role.ADMIN:
        if (
            Membership.objects.filter(team=team, role=Membership.Role.ADMIN).count()
            == 1
        ):
            return JsonResponse({"error": "Cannot remove the last admin"}, status=400)

    membership.role = new_role
    membership.save()
    return redirect("team_members", pk=team_pk)
