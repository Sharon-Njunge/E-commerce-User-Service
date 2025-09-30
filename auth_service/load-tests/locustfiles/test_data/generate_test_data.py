#!/usr/bin/env python3
import json
import csv
import random
from faker import Faker

fake = Faker()

def generate_test_users(count=1000):
    """Generate test users for performance testing"""
    users = []
    for i in range(count):
        user = {
            'id': i + 1,
            'email': f'loadtest_user_{i}@example.com',
            'password': f'password_{i}',
            'username': f'loadtest_user_{i}',
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'auth0_user_id': f'auth0|{random.randint(1000000, 9999999)}'
        }
        users.append(user)
    
    # Save as JSON
    with open('load_tests/test_data/users.json', 'w') as f:
        json.dump(users, f, indent=2)
    
    # Save as CSV for potential external use
    with open('load_tests/test_data/users.csv', 'w', newline='') as f:
        if users:
            writer = csv.DictWriter(f, fieldnames=users[0].keys())
            writer.writeheader()
            writer.writerows(users)
    
    print(f"Generated {count} test users")
    return users

def generate_auth_tokens(count=100):
    """Generate mock auth tokens for testing"""
    tokens = []
    for i in range(count):
        token = {
            'access_token': f'mock_access_token_{i}',
            'refresh_token': f'mock_refresh_token_{i}',
            'expires_in': 3600,
            'token_type': 'Bearer'
        }
        tokens.append(token)
    
    with open('load_tests/test_data/tokens.json', 'w') as f:
        json.dump(tokens, f, indent=2)
    
    return tokens

if __name__ == '__main__':
    generate_test_users(1000)
    generate_auth_tokens(100)
    print("Test data generation complete!")