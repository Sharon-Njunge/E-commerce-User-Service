from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class CustomUser(AbstractUser):
    """Extended User model with additional fields"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    auth0_sub = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["auth0_sub"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.email} ({self.first_name} {self.last_name})"

    def is_account_locked(self):
        """Check if account is locked due to failed login attempts"""
        if self.locked_until:
            return timezone.now() < self.locked_until
        return False

    def reset_failed_attempts(self):
        """Reset failed login attempts and unlock account"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=["failed_login_attempts", "locked_until"])


class UserPreferences(models.Model):
    """User preferences and settings"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="preferences"
    )
    language = models.CharField(max_length=10, default="en")
    timezone = models.CharField(max_length=50, default="UTC")
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    marketing_emails = models.BooleanField(default=False)
    theme = models.CharField(
        max_length=10, choices=[("light", "Light"), ("dark", "Dark")], default="light"
    )
    currency = models.CharField(max_length=3, default="USD")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_preferences"

    def __str__(self):
        return f"Preferences for {self.user.email}"


class UserSession(models.Model):
    """User session tracking"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="sessions"
    )
    session_token = models.CharField(max_length=255, unique=True)
    auth0_session_id = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_sessions"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["session_token"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["last_activity"]),
        ]

    def __str__(self):
        return f"Session for {self.user.email}"

    def is_expired(self):
        """Check if session is expired"""
        return timezone.now() > self.expires_at

    def deactivate(self):
        """Deactivate session"""
        self.is_active = False
        self.save(update_fields=["is_active"])


class UserRole(models.Model):
    """User roles for authorization"""

    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("admin", "Admin"),
        ("staff", "Staff"),
        ("moderator", "Moderator"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="roles")
    role_name = models.CharField(max_length=20, choices=ROLE_CHOICES)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="assigned_roles"
    )

    class Meta:
        db_table = "user_roles"
        unique_together = ["user", "role_name"]
        indexes = [
            models.Index(fields=["user", "role_name"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.role_name}"


class UserActivity(models.Model):
    """Track user activities for audit purposes"""

    ACTION_CHOICES = [
        ("login", "Login"),
        ("logout", "Logout"),
        ("password_change", "Password Change"),
        ("profile_update", "Profile Update"),
        ("preferences_update", "Preferences Update"),
        ("failed_login", "Failed Login"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="activities"
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_activities"
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["action", "timestamp"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user.email} - {self.action} at {self.timestamp}"
