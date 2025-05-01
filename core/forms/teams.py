from django import forms
from core.models import Team, Membership


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "description"]


class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ["user", "role"] 