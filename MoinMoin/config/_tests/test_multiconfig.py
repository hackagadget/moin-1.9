# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.config.multiconfig Tests

    @copyright: 2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py


class TestPasswordChecker:
    username = "SomeUser"
    tests_builtin = [
        ('', False), # empty
        ('1966', False), # too short
        ('asdfghjk', False), # keyboard sequence
        ('QwertZuiop', False), # german keyboard sequence, with uppercase
        ('mnbvcx', False), # reverse keyboard sequence
        ('12345678', False), # keyboard sequence, too easy
        ('aaaaaaaa', False), # not enough different chars
        ('BBBaaaddd', False), # not enough different chars
        (username, False), # username == password
        (username[1:-1], False), # password in username
        ("XXX%sXXX" % username, False), # username in password
        ('Moin-2007', True), # this should be OK
    ]
    def testBuiltinPasswordChecker(self):
        pw_checker = self.request.cfg.password_checker
        if not pw_checker:
            py.test.skip("password_checker is disabled in the configuration, not testing it")
        else:
            for pw, result in self.tests_builtin:
                pw_error = pw_checker(self.request, self.username, pw)
                print("%r: %s" % (pw, pw_error))
                assert result == (pw_error is None)

coverage_modules = ['MoinMoin.config.multiconfig']

