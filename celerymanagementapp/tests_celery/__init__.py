"""
    This testing package is for tests that require a running Celery daemon
    (celeryd).  The database that Django creates specifically for its tests is 
    separate from the *real* database and therefore external processes--like 
    celeryd and celeryev--cannot access it.  This package avoids Django's 
    testing infrastructure and therefore avoids this problem.  
    
    However, since an actual on-disk database is accessed, these tests will run 
    slower than the Django tests that use a sqlite in-memory database.  So any 
    tests that do not need celeryd should use the normal Django tests.
"""
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from celerymanagementapp.tests_celery import base

#==============================================================================#
# Test modules...
from celerymanagementapp.tests_celery import misc

# List of all test modules containing tests.  
_testmodules = [misc]

# Import all test cases so they appear in this module.  This appears to be 
# needed for Hudson automated testing.  Do this instead of just: 
#       from <module> import *
# so we don't import *all* names from the modules.
for m in _testmodules:
    for name,val in m.__dict__.iteritems():
        if name.endswith('_TestCase') and issubclass(val, base.CeleryManagement_TestCaseBase):
            globals()[name] = val

#==============================================================================#

def suite():
    test_suite = unittest.TestSuite()
    for m in _testmodules:
        s = base.autogenerate_testsuite(m.__dict__)
        test_suite.addTest(s)
    return test_suite

#==============================================================================#