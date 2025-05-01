from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from core.forms import UserRegistrationForm


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