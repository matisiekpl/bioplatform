from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["name", "email", "username", "password"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        email = cleaned_data.get("email")
        username = cleaned_data.get("username")

        if password and len(password) < 8:
            self.add_error("password", "Hasło musi mieć co najmniej 8 znaków")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Hasła nie pasują do siebie")
        if email and User.objects.filter(email=email).exists():
            self.add_error("email", "Użytkownik o tym adresie email już istnieje")
        if username and User.objects.filter(username=username).exists():
            self.add_error("username", "Użytkownik o tej nazwie już istnieje")
        return cleaned_data
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user