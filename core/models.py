from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator


class User(AbstractUser):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, validators=[MinLengthValidator(8)])

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "name"]


class Team(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        VIEWER = "VIEWER", "Viewer"
        EDITOR = "EDITOR", "Editor"
        ADMIN = "ADMIN", "Admin"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "team")

    def __str__(self):
        return f"{self.user.name} - {self.team.name} ({self.role})"


class Experiment(models.Model):
    class Type(models.TextChoices):
        CELL_LINE = "CELL_LINE", "Cell Line"

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.CELL_LINE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="experiments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Measurement(models.Model):
    class Type(models.TextChoices):
        CELL_COUNT = "CELL_COUNT", "Cell Count"
        ADHESION_RATE = "ADHESION_RATE", "Adhesion Rate"

    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=20, choices=Type.choices)
    value = models.FloatField()
    timestamp = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="measurements")
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="measurements")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.value}"
