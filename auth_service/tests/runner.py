import os
import sys
import pytest
from django.test.utils import get_runner
from django.conf import settings

def run_tests():
    os.environ['TESTING'] = 'True'
    os.environ['DJANGO_SETTINGS_MODULE'] = 'auth_service.settings'
    
    test_args = ['tests/', '--verbose', '--capture=no']
    
    exit_code = pytest.main(test_args)
    sys.exit(exit_code)

if __name__ == '__main__':
    run_tests()