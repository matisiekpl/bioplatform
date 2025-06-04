from django import forms
from core.models import Team, Membership


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "description"]

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        description = cleaned_data.get("description")
        if not name or len(name.strip()) < 3:
            self.add_error("name", "Nazwa zespołu musi mieć co najmniej 3 znaki")
        if not description or not description.strip():
            self.add_error("description", "Opis zespołu nie może być pusty")
        return cleaned_data


class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ["user", "role"]

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        role = cleaned_data.get("role")
        if not user:
            self.add_error("user", "Użytkownik jest wymagany")
        if not role:
            self.add_error("role", "Rola jest wymagana")
        return cleaned_data 