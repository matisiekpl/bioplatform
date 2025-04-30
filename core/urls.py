from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("teams/", views.TeamListView.as_view(), name="team_list"),
    path("teams/create/", views.TeamCreateView.as_view(), name="team_create"),
    path("teams/<int:pk>/update/", views.TeamUpdateView.as_view(), name="team_update"),
    path("teams/<int:pk>/delete/", views.TeamDeleteView.as_view(), name="team_delete"),
    path("teams/<int:pk>/members/", views.team_members, name="team_members"),
    path(
        "teams/<int:team_pk>/members/<int:membership_pk>/remove/",
        views.remove_team_member,
        name="remove_team_member",
    ),
    path(
        "teams/<int:team_pk>/members/<int:membership_pk>/update-role/",
        views.update_member_role,
        name="update_member_role",
    ),
]
