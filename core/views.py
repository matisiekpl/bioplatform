from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from .models import Team, Membership, Experiment, Measurement
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm, TeamForm, MembershipForm, ExperimentForm, MeasurementForm
from .utils import detect_cells_from_image
from django.contrib import messages


class TeamRoleRequiredMixin(UserPassesTestMixin):
    required_role = None
    
    def test_func(self):
        # Get the team_id either from kwargs or from the object
        if hasattr(self, 'get_object'):
            try:
                obj = self.get_object()
                if hasattr(obj, 'team_id'):
                    team_id = obj.team_id
                elif hasattr(obj, 'team'):
                    team_id = obj.team.id
                elif hasattr(obj, 'experiment') and hasattr(obj.experiment, 'team'):
                    team_id = obj.experiment.team.id
                else:
                    return False
            except:
                # If we can't get the object (e.g., in CreateView), try from kwargs
                team_id = self.kwargs.get('team_id')
                if not team_id and 'experiment_id' in self.kwargs:
                    experiment = get_object_or_404(Experiment, id=self.kwargs['experiment_id'])
                    team_id = experiment.team_id
        else:
            team_id = self.kwargs.get('team_id')
            if not team_id and 'experiment_id' in self.kwargs:
                experiment = get_object_or_404(Experiment, id=self.kwargs['experiment_id'])
                team_id = experiment.team_id
                
        if not team_id:
            return False
            
        membership = Membership.objects.filter(
            user=self.request.user,
            team_id=team_id
        ).first()
        
        if not membership:
            return False
            
        if self.required_role == Membership.Role.EDITOR:
            return membership.role in [Membership.Role.EDITOR, Membership.Role.ADMIN]
        elif self.required_role == Membership.Role.ADMIN:
            return membership.role == Membership.Role.ADMIN
        
        # By default, always allow (for viewer or when no specific role is required)
        return True


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


class TeamDetailView(LoginRequiredMixin, DetailView):
    model = Team
    template_name = "core/teams/team_detail.html"
    context_object_name = "team"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_object()
        
        # Add user's role to context for template permission checks
        membership = Membership.objects.filter(
            user=self.request.user,
            team=team
        ).first()
        context['user_role'] = membership.role if membership else None
        
        return context


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


class ExperimentListView(LoginRequiredMixin, ListView):
    model = Experiment
    template_name = 'core/experiments/experiment_list.html'
    context_object_name = 'experiments'

    def get_queryset(self):
        team_id = self.kwargs.get('team_id')
        return Experiment.objects.filter(team_id=team_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = Team.objects.get(id=self.kwargs.get('team_id'))
        
        # Add user's role to context for template permission checks
        membership = Membership.objects.filter(
            user=self.request.user,
            team_id=self.kwargs.get('team_id')
        ).first()
        context['user_role'] = membership.role if membership else None
        
        return context


class ExperimentCreateView(LoginRequiredMixin, TeamRoleRequiredMixin, CreateView):
    model = Experiment
    form_class = ExperimentForm
    template_name = 'core/experiments/experiment_form.html'
    required_role = Membership.Role.EDITOR

    def form_valid(self, form):
        form.instance.team_id = self.kwargs.get('team_id')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_id'] = self.kwargs.get('team_id')
        return context

    def get_success_url(self):
        return reverse('experiment_list', kwargs={'team_id': self.kwargs.get('team_id')})


class ExperimentUpdateView(LoginRequiredMixin, TeamRoleRequiredMixin, UpdateView):
    model = Experiment
    form_class = ExperimentForm
    template_name = 'core/experiments/experiment_form.html'
    required_role = Membership.Role.EDITOR

    def get_success_url(self):
        return reverse('experiment_list', kwargs={'team_id': self.object.team_id})


class ExperimentDeleteView(LoginRequiredMixin, TeamRoleRequiredMixin, DeleteView):
    model = Experiment
    template_name = 'core/experiments/experiment_confirm_delete.html'
    required_role = Membership.Role.EDITOR

    def get_success_url(self):
        return reverse('experiment_list', kwargs={'team_id': self.object.team_id})


class MeasurementListView(LoginRequiredMixin, ListView):
    model = Measurement
    template_name = 'core/measurements/measurement_list.html'
    context_object_name = 'measurements'

    def get_queryset(self):
        experiment_id = self.kwargs.get('experiment_id')
        measurement_type = self.request.GET.get('type')
        
        queryset = Measurement.objects.filter(experiment_id=experiment_id).order_by('-timestamp')
        
        if measurement_type:
            queryset = queryset.filter(type=measurement_type)
        elif Measurement.objects.filter(experiment_id=experiment_id).exists():
            # Default to first measurement type if no type is specified and measurements exist
            first_measurement = Measurement.objects.filter(experiment_id=experiment_id).first()
            if first_measurement:
                queryset = queryset.filter(type=first_measurement.type)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experiment = Experiment.objects.get(id=self.kwargs.get('experiment_id'))
        context['experiment'] = experiment
        context['team'] = experiment.team
        
        # Add user's role to context for template permission checks
        membership = Membership.objects.filter(
            user=self.request.user,
            team_id=experiment.team_id
        ).first()
        context['user_role'] = membership.role if membership else None
        
        # Add measurement types for the selector
        context['measurement_types'] = Measurement.Type.choices
        context['selected_type'] = self.request.GET.get('type', '')
        
        # If no type is selected but measurements exist, select the first type
        if not context['selected_type'] and self.get_queryset().exists():
            context['selected_type'] = self.get_queryset().first().type
            
        return context


class MeasurementCreateView(LoginRequiredMixin, TeamRoleRequiredMixin, CreateView):
    model = Measurement
    form_class = MeasurementForm
    template_name = 'core/measurements/measurement_form.html'
    required_role = Membership.Role.EDITOR

    def form_valid(self, form):
        form.instance.experiment_id = self.kwargs.get('experiment_id')
        form.instance.created_by = self.request.user
        
        # If autodetect is checked and it's a CELL_COUNT measurement with an image
        if (form.cleaned_data.get('autodetect') and 
            form.instance.type == Measurement.Type.CELL_COUNT):
            
            # Ensure there's an image
            if not form.cleaned_data.get('image'):
                form.add_error('image', 'An image is required for cell counting with autodetect')
                return self.form_invalid(form)
                
            # Calculate cell count from the uploaded image
            cell_count = detect_cells_from_image(form.cleaned_data['image'])
            form.instance.value = cell_count
            
            # Add success message
            messages.success(self.request, f'Successfully detected {cell_count} cells from the image.')
        
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experiment = Experiment.objects.get(id=self.kwargs.get('experiment_id'))
        context['experiment'] = experiment
        context['team'] = experiment.team
        return context

    def get_success_url(self):
        return reverse('measurement_list', kwargs={'experiment_id': self.kwargs.get('experiment_id')})


class MeasurementUpdateView(LoginRequiredMixin, TeamRoleRequiredMixin, UpdateView):
    model = Measurement
    form_class = MeasurementForm
    template_name = 'core/measurements/measurement_form.html'
    required_role = Membership.Role.EDITOR

    def form_valid(self, form):
        # If autodetect is checked and it's a CELL_COUNT measurement with an image
        if (form.cleaned_data.get('autodetect') and 
            form.instance.type == Measurement.Type.CELL_COUNT):
            
            # Ensure there's an image
            if not form.cleaned_data.get('image'):
                form.add_error('image', 'An image is required for cell counting with autodetect')
                return self.form_invalid(form)
                
            # Calculate cell count from the uploaded image
            cell_count = detect_cells_from_image(form.cleaned_data['image'])
            form.instance.value = cell_count
            
            # Add success message
            messages.success(self.request, f'Successfully detected {cell_count} cells from the image.')
            
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['experiment'] = self.object.experiment
        context['team'] = self.object.experiment.team
        return context

    def get_success_url(self):
        return reverse('measurement_list', kwargs={'experiment_id': self.object.experiment_id})


class MeasurementDeleteView(LoginRequiredMixin, TeamRoleRequiredMixin, DeleteView):
    model = Measurement
    template_name = 'core/measurements/measurement_confirm_delete.html'
    required_role = Membership.Role.EDITOR

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['experiment'] = self.object.experiment
        context['team'] = self.object.experiment.team
        return context

    def get_success_url(self):
        return reverse('measurement_list', kwargs={'experiment_id': self.object.experiment_id})
