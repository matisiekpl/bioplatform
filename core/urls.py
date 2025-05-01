from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("", RedirectView.as_view(url='/teams/', permanent=True), name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("teams/", views.TeamListView.as_view(), name="team_list"),
    path("teams/<int:pk>/", views.TeamDetailView.as_view(), name="team_detail"),
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
    path('teams/<int:team_id>/experiments/', views.ExperimentListView.as_view(), name='experiment_list'),
    path('teams/<int:team_id>/experiments/create/', views.ExperimentCreateView.as_view(), name='experiment_create'),
    path('experiments/<int:pk>/update/', views.ExperimentUpdateView.as_view(), name='experiment_update'),
    path('experiments/<int:pk>/delete/', views.ExperimentDeleteView.as_view(), name='experiment_delete'),
    path('experiments/<int:experiment_id>/measurements/', views.MeasurementListView.as_view(), name='measurement_list'),
    path('experiments/<int:experiment_id>/measurements/create/', views.MeasurementCreateView.as_view(), name='measurement_create'),
    path('measurements/<int:pk>/update/', views.MeasurementUpdateView.as_view(), name='measurement_update'),
    path('measurements/<int:pk>/delete/', views.MeasurementDeleteView.as_view(), name='measurement_delete'),
    
    path('experiments/<int:experiment_id>/analyze-image/', views.analyze_image_form, name='analyze_image_form'),
    path('analyze-image-results/', views.analyze_image_results, name='analyze_image_results'),
]
