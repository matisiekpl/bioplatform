from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse
from django.db.models import Q
from datetime import datetime
from core.models import Experiment, Team, Membership
from core.forms import ExperimentForm
from .mixins import TeamRoleRequiredMixin


class ExperimentListView(LoginRequiredMixin, ListView):
    model = Experiment
    template_name = 'core/experiments/experiment_list.html'
    context_object_name = 'experiments'

    def get_queryset(self):
        team_id = self.kwargs.get('team_id')
        queryset = Experiment.objects.filter(team_id=team_id)
        
        # Filter by name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=date_from)
            except ValueError:
                pass
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d')
                # Add one day to include the end date fully
                queryset = queryset.filter(created_at__lte=date_to)
            except ValueError:
                pass
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = Team.objects.get(id=self.kwargs.get('team_id'))
        
        # Add user's role to context for template permission checks
        membership = Membership.objects.filter(
            user=self.request.user,
            team_id=self.kwargs.get('team_id')
        ).first()
        context['user_role'] = membership.role if membership else None
        
        # Add search and date filter parameters to context
        context['search'] = self.request.GET.get('search', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        
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