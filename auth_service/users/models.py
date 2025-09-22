from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model for e-commerce platform"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    auth0_user_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['auth0_user_id']),
            models.Index(fields=['date_joined']),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class UserSession(models.Model):
    """Track user sessions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_token = models.CharField(max_length=255, unique=True, db_index=True)
    device_info = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['session_token']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
        ]
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Session for {self.user.email} - {self.created_at}"


class UserPreferences(models.Model):
    """Store user preferences and settings"""
    
    NOTIFICATION_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('none', 'None'),
    ]
    
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    currency = models.CharField(max_length=3, default='USD')
    
    # Notification preferences
    order_notifications = models.CharField(max_length=10, choices=NOTIFICATION_CHOICES, default='email')
    payment_notifications = models.CharField(max_length=10, choices=NOTIFICATION_CHOICES, default='email')
    marketing_emails = models.BooleanField(default=True)
    security_alerts = models.CharField(max_length=10, choices=NOTIFICATION_CHOICES, default='email')
    
    # Privacy settings
    profile_visibility = models.BooleanField(default=True)
    data_sharing_consent = models.BooleanField(default=False)
    
    # Additional preferences as JSON
    custom_preferences = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'
        
    def __str__(self):
        return f"Preferences for {self.user.email}"


class UserRole(models.Model):
    """User roles and permissions"""
    
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('support', 'Support Staff'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='roles')
    role_name = models.CharField(max_length=20, choices=ROLE_CHOICES)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_roles')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_roles'
        unique_together = ['user', 'role_name']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['role_name']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.role_name}"


class LoginAttempt(models.Model):
    """Track login attempts for security"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField()
    failure_reason = models.CharField(max_length=255, blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_attempts'
        indexes = [
            models.Index(fields=['email', 'attempted_at']),
            models.Index(fields=['ip_address', 'attempted_at']),
            models.Index(fields=['success', 'attempted_at']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{status} login attempt for {self.email} at {self.attempted_at}"