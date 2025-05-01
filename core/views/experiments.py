from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse
from core.models import Experiment, Team, Membership
from core.forms import ExperimentForm
from .mixins import TeamRoleRequiredMixin


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