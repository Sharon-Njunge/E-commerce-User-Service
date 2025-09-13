from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
import random
from auth_service.users.models import CustomUser, UserPreferences, UserRole, UserActivity

class Command(BaseCommand):
    help = 'Seed database with sample users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of users to create'
        )
        parser.add_argument(
            '--admin-count',
            type=int,
            default=2,
            help='Number of admin users to create'
        )
    
    def handle(self, *args, **options):
        fake = Faker()
        count = options['count']
        admin_count = options['admin_count']
        
        self.stdout.write(
            self.style.SUCCESS(f'Creating {count} users with {admin_count} admins...')
        )
        
        with transaction.atomic():
            # Create regular users
            users_created = 0
            
            for i in range(count):
                try:
                    user = CustomUser.objects.create_user(
                        username=fake.user_name() + str(random.randint(1000, 9999)),
                        email=fake.email(),
                        password='password123',
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        phone_number=fake.phone_number()[:20],
                        date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=80),
                        is_email_verified=random.choice([True, False]),
                        auth0_sub=f"auth0|{fake.uuid4()}"
                    )
                    
                    # Create preferences
                    UserPreferences.objects.create(
                        user=user,
                        language=random.choice(['en', 'es', 'fr']),
                        timezone=random.choice(['UTC', 'US/Eastern', 'US/Pacific', 'Europe/London']),
                        email_notifications=random.choice([True, False]),
                        sms_notifications=random.choice([True, False]),
                        marketing_emails=random.choice([True, False]),
                        theme=random.choice(['light', 'dark']),
                        currency=random.choice(['USD', 'EUR', 'GBP'])
                    )
                    
                    # Assign customer role
                    UserRole.objects.create(
                        user=user,
                        role_name='customer'
                    )
                    
                    # Create some user activities
                    for _ in range(random.randint(1, 5)):
                        UserActivity.objects.create(
                            user=user,
                            action=random.choice(['login', 'profile_update', 'preferences_update']),
                            ip_address=fake.ipv4(),
                            user_agent=fake.user_agent(),
                            metadata={'source': 'seed_command'}
                        )
                    
                    users_created += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating user {i}: {str(e)}')
                    )
            
            # Create admin users
            admins_created = 0
            for i in range(admin_count):
                try:
                    admin = CustomUser.objects.create_user(
                        username=f'admin_{i+1}',
                        email=f'admin{i+1}@example.com',
                        password='admin123',
                        first_name='Admin',
                        last_name=f'User {i+1}',
                        is_email_verified=True,
                        is_staff=True,
                        auth0_sub=f"auth0|admin_{fake.uuid4()}"
                    )
                    
                    # Create preferences
                    UserPreferences.objects.create(user=admin)
                    
                    # Assign admin role
                    UserRole.objects.create(
                        user=admin,
                        role_name='admin'
                    )
                    
                    admins_created += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating admin {i}: {str(e)}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {users_created} users and {admins_created} admins'
            )
        )
        
        # Display sample credentials
        self.stdout.write('\n' + '='*50)
        self.stdout.write('SAMPLE CREDENTIALS:')
        self.stdout.write('='*50)
        self.stdout.write('Admin Users:')
        for i in range(admins_created):
            self.stdout.write(f'  Email: admin{i+1}@example.com | Password: admin123')
        self.stdout.write('\nRegular Users:')
        self.stdout.write('  All regular users have password: password123')
        self.stdout.write('='*50)

# auth_service/users/management/commands/create_superuser_with_roles.py
from django.core.management.base import BaseCommand
from django.db import transaction
from auth_service.users.models import CustomUser, UserPreferences, UserRole

class Command(BaseCommand):
    help = 'Create a superuser with roles and preferences'
    
    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Admin email')
        parser.add_argument('--password', required=True, help='Admin password')
        parser.add_argument('--first-name', default='Super', help='First name')
        parser.add_argument('--last-name', default='Admin', help='Last name')
    
    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        
        try:
            with transaction.atomic():
                # Create superuser
                user = CustomUser.objects.create_superuser(
                    username=email.split('@')[0],
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_email_verified=True,
                    auth0_sub=f"auth0|superuser_{email.replace('@', '_').replace('.', '_')}"
                )
                
                # Create preferences
                UserPreferences.objects.create(user=user)
                
                # Assign admin role
                UserRole.objects.create(
                    user=user,
                    role_name='admin'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created superuser: {email}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {str(e)}')
            )