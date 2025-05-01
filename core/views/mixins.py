from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404
from core.models import Membership, Experiment


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