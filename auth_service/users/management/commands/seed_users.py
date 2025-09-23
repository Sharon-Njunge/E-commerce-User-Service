import random
import uuid
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from auth_service.users.models import (LoginAttempt, User, UserPreferences,
                                       UserRole, UserSession)

fake = Faker()


class Command(BaseCommand):
    help = 'Seed database with sample test users and related data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create (default: 20)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            User.objects.all().delete()
            UserPreferences.objects.all().delete()
            UserRole.objects.all().delete()
            UserSession.objects.all().delete()
            LoginAttempt.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        num_users = options['users']
        self.stdout.write(f'Creating {num_users} test users...')

        # Create admin user first
        admin_user = self.create_admin_user()
        self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_user.email}'))

        # Create regular users
        users_created = 0
        for i in range(num_users):
            try:
                user = self.create_user()
                self.create_user_preferences(user)
                self.create_user_role(user)
                
                # Create some sessions for active users (60% chance)
                if random.random() < 0.6:
                    self.create_user_session(user)
                
                # Create login attempts for some users
                if random.random() < 0.4:
                    self.create_login_attempts(user.email)
                
                users_created += 1
                
                if users_created % 5 == 0:
                    self.stdout.write(f'Created {users_created} users...')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating user {i+1}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded database with {users_created + 1} users '
                f'(including 1 admin)'
            )
        )

    def create_admin_user(self):
        """Create an admin user with known credentials"""
        admin_email = 'admin@ecommerce.com'
        
        try:
            admin = User.objects.get(email=admin_email)
            self.stdout.write(f'Admin user already exists: {admin_email}')
            return admin
        except User.DoesNotExist:
            pass

        admin = User.objects.create(
            email=admin_email,
            first_name='Admin',
            last_name='User',
            phone_number='+1234567890',
            is_active=True,
            is_staff=True,
            is_superuser=True,
            email_verified=True,
            auth0_user_id=f'auth0|admin_{uuid.uuid4().hex[:8]}',
            password=make_password('admin123!'),
        )
        
        # Create admin preferences
        self.create_user_preferences(admin)
        
        # Create admin role
        UserRole.objects.create(
            user=admin,
            role_name='admin',
            assigned_by=admin
        )
        
        return admin

    def create_user(self):
        """Create a regular user with random data"""
        email = fake.email()
        
        # Ensure unique email
        while User.objects.filter(email=email).exists():
            email = fake.email()

        user = User.objects.create(
            email=email,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone_number=fake.phone_number()[:20] if random.random() > 0.3 else None,
            is_active=random.choice([True, True, True, False]),  
            email_verified=random.choice([True, False]),
            auth0_user_id=f'auth0|{uuid.uuid4().hex[:16]}',
            password=make_password('password123'),
        )
        
        # Set random join date (within last 2 years)
        user.date_joined = fake.date_time_between(
            start_date='-2y', 
            end_date='now', 
            tzinfo=timezone.get_current_timezone()
        )
        
        # Set last login for active users
        if user.is_active and random.random() > 0.2:
            user.last_login = fake.date_time_between(
                start_date=user.date_joined,
                end_date='now',
                tzinfo=timezone.get_current_timezone()
            )
        
        user.save()
        return user

    def create_user_preferences(self, user):
        """Create user preferences"""
        preferences = UserPreferences.objects.create(
            user=user,
            language=random.choice(['en', 'es', 'fr', 'de']),
            timezone=random.choice([
                'UTC', 'America/New_York', 'Europe/London', 
                'Asia/Tokyo', 'Australia/Sydney'
            ]),
            theme=random.choice(['light', 'dark', 'auto']),
            currency=random.choice(['USD', 'EUR', 'GBP', 'JPY']),
            order_notifications=random.choice(['email', 'sms', 'push', 'none']),
            payment_notifications=random.choice(['email', 'sms', 'push']),
            marketing_emails=random.choice([True, False]),
            security_alerts=random.choice(['email', 'sms', 'push']),
            profile_visibility=random.choice([True, False]),
            data_sharing_consent=random.choice([True, False]),
            custom_preferences={
                'newsletter': random.choice([True, False]),
                'two_factor_enabled': random.choice([True, False]),
                'product_recommendations': random.choice([True, False]),
            }
        )
        return preferences

    def create_user_role(self, user):
        """Create user role"""
        # Most users are customers, some are support staff
        if user.is_staff:
            role_name = 'admin'
        elif random.random() < 0.05:  # 5% managers
            role_name = 'manager'
        elif random.random() < 0.1:   # 10% support
            role_name = 'support'
        else:
            role_name = 'customer'

        role = UserRole.objects.create(
            user=user,
            role_name=role_name,
        )
        return role

    def create_user_session(self, user):
        """Create user session"""
        session = UserSession.objects.create(
            user=user,
            session_token=f'sess_{uuid.uuid4().hex}',
            device_info={
                'device_type': random.choice(['desktop', 'mobile', 'tablet']),
                'os': random.choice(['Windows', 'macOS', 'Linux', 'iOS', 'Android']),
                'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge'])
            },
            ip_address=fake.ipv4(),
            user_agent=fake.user_agent(),
            created_at=fake.date_time_between(
                start_date='-30d',
                end_date='now',
                tzinfo=timezone.get_current_timezone()
            ),
            expires_at=timezone.now() + timedelta(hours=random.randint(1, 168)),  # 1-168 hours
            is_active=random.choice([True, False]),
        )
        return session

    def create_login_attempts(self, email):
        """Create login attempts for a user"""
        num_attempts = random.randint(1, 5)
        
        for i in range(num_attempts):
            success = random.choice([True, False, False, True, True])  # More successes
            
            attempt = LoginAttempt.objects.create(
                email=email,
                ip_address=fake.ipv4(),
                user_agent=fake.user_agent(),
                success=success,
                failure_reason=None if success else random.choice([
                    'Invalid password',
                    'Account locked',
                    'Email not verified',
                    'Too many attempts'
                ]),
                attempted_at=fake.date_time_between(
                    start_date='-30d',
                    end_date='now',
                    tzinfo=timezone.get_current_timezone()
                )
            )


# auth_service/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import LoginAttempt, User, UserPreferences, UserRole, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'email_verified', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Auth0 Integration', {'fields': ('auth0_user_id', 'email_verified')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'language', 'theme', 'currency', 'marketing_emails']
    list_filter = ['language', 'theme', 'currency', 'marketing_emails']
    search_fields = ['user__email']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'created_at', 'expires_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['session_token']


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role_name', 'assigned_at', 'is_active']
    list_filter = ['role_name', 'is_active', 'assigned_at']
    search_fields = ['user__email']


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['email', 'ip_address', 'success', 'attempted_at']
    list_filter = ['success', 'attempted_at']
    search_fields = ['email', 'ip_address']
    readonly_fields = ['attempted_at']