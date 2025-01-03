# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.user Tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>
                2009 by ReimarBauer
                2013 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os
import py

from MoinMoin import user, caching


class TestEncodePassword(object):
    """user: encode passwords tests"""

    def testAscii(self):
        """user: encode ascii password"""
        # u'MoinMoin' and 'MoinMoin' should be encoded to same result
        cfg = self.request.cfg
        tests = [
            ('{PASSLIB}', '12345', "{PASSLIB}$6$rounds=1001$12345$jrPUCzPJt1yiixDbzIgSBoKED0/DlNDTHZN3lVarCtN6IM/.LoAw5pgUQH112CErU6wS8HXTZNpqb7wVjHLs/0"),
            ('{SSHA}', '12345', "{SSHA}xkDIIx1I7A4gC98Vt/+UelIkTDYxMjM0NQ=="),
        ]
        for scheme, salt, expected in tests:
            result = user.encodePassword(cfg, "MoinMoin", salt=salt, scheme=scheme)
            assert result == expected
            result = user.encodePassword(cfg, "MoinMoin", salt=salt, scheme=scheme)
            assert result == expected

    def testUnicode(self):
        """ user: encode unicode password """
        cfg = self.request.cfg
        tests = [
            ('{PASSLIB}', '12345', "{PASSLIB}$6$rounds=1001$12345$5srFB66ZCu2JgGwPgdfb1lHRmqkjnKC/RxdsFlWn2WzoQh3btIjH6Ai1LJV9iYLDa9kLP/VQYa4DHLkRnaBw8."),
            ('{SSHA}', '12345', "{SSHA}YiwfeVWdVW9luqyVn8t2JivlzmUxMjM0NQ=="),
            ]
        for scheme, salt, expected in tests:
            result = user.encodePassword(cfg, 'סיסמה סודית בהחלט', salt=salt, scheme=scheme) # Hebrew
            assert result == expected


class TestLoginWithPassword(object):
    """user: login tests"""

    def setup_method(self, method):
        # Save original user and cookie
        self.saved_cookie = self.request.cookies
        self.saved_user = self.request.user

        # Create anon user for the tests
        self.request.cookies = {}
        self.request.user = user.User(self.request)

        self.user = None
        self.passlib_support = self.request.cfg.passlib_support
        self.password_scheme = self.request.cfg.password_scheme

    def teardown_method(self, method):
        """ Run after each test

        Remove user and reset user listing cache.
        """
        # Remove user file and user
        if self.user is not None:
            try:
                path = self.user._User__filename()
                os.remove(path)
            except OSError:
                pass
            del self.user

        # Restore original user
        self.request.cookies = self.saved_cookie
        self.request.user = self.saved_user

        # Remove user lookup caches, or next test will fail
        user.clearLookupCaches(self.request)

    def testAsciiPassword(self):
        """ user: login with ascii password """
        # Create test user
        name = '__Non Existent User Name__'
        password = name
        self.createUser(name, password)

        # Try to "login"
        theUser = user.User(self.request, name=name, password=password)
        assert theUser.valid

    def testUnicodePassword(self):
        """ user: login with non-ascii password """
        # Create test user
        name = '__שם משתמש לא קיים__' # Hebrew
        password = name
        self.createUser(name, password)

        # Try to "login"
        theUser = user.User(self.request, name=name, password=password)
        assert theUser.valid

    def test_auth_with_apr1_stored_password(self):
        """
        Create user with {APR1} password and check that user can login.
        Also check if auto-upgrade happens and is saved to disk.
        """
        # Create test user
        name = 'Test User'
        password = '12345'
        # generated with "htpasswd -nbm blaze 12345"
        pw_hash = '{APR1}$apr1$NG3VoiU5$PSpHT6tV0ZMKkSZ71E3qg.'
        self.createUser(name, pw_hash, True)

        # Try to "login"
        theuser = user.User(self.request, name=name, password=password)
        assert theuser.valid
        # Check if the stored password was auto-upgraded on login and saved
        theuser = user.User(self.request, name=name, password=password)
        assert theuser.enc_password.startswith(self.password_scheme)

    def test_auth_with_md5_stored_password(self):
        """
        Create user with {MD5} password and check that user can login.
        Also check if auto-upgrade happens and is saved to disk.
        """
        # Create test user
        name = 'Test User'
        password = '12345'
        pw_hash = '{MD5}$1$salt$etVYf53ma13QCiRbQOuRk/'
        self.createUser(name, pw_hash, True)

        # Try to "login"
        theuser = user.User(self.request, name=name, password=password)
        assert theuser.valid
        # Check if the stored password was auto-upgraded on login and saved
        theuser = user.User(self.request, name=name, password=password)
        assert theuser.enc_password.startswith(self.password_scheme)

    def test_auth_with_des_stored_password(self):
        """
        Create user with {DES} password and check that user can login.
        Also check if auto-upgrade happens and is saved to disk.
        """
        # Create test user
        name = 'Test User'
        password = '12345'
        # generated with "htpasswd -nbd blaze 12345"
        pw_hash = '{DES}gArsfn7O5Yqfo'
        self.createUser(name, pw_hash, True)

        try:
            import crypt
            # Try to "login"
            theuser = user.User(self.request, name=name, password=password)
            assert theuser.valid
            # Check if the stored password was auto-upgraded on login and saved
            theuser = user.User(self.request, name=name, password=password)
            assert theuser.enc_password.startswith(self.password_scheme)
        except ImportError:
            py.test.skip("Platform does not provide crypt module!")

    def test_auth_with_sha_stored_password(self):
        """
        Create user with {SHA} password and check that user can login.
        Also check if auto-upgrade happens and is saved to disk.
        """
        # Create test user
        name = 'Test User'
        password = '12345'
        pw_hash = '{SHA}jLIjfQZ5yojbZGTqxg2pY0VROWQ='
        self.createUser(name, pw_hash, True)

        # Try to "login"
        theuser = user.User(self.request, name=name, password=password)
        assert theuser.valid
        # Check if the stored password was auto-upgraded on login and saved
        theuser = user.User(self.request, name=name, password=password)
        assert theuser.enc_password.startswith(self.password_scheme)

    def test_auth_with_ssha_stored_password(self):
        """
        Create user with {SSHA} password and check that user can login.
        Also check if auto-upgrade happens and is saved to disk.
        """
        # Create test user
        name = 'Test User'
        password = '12345'
        pw_hash = '{SSHA}dbeFtH5EGkOI1jgPADlGZgHWq072TIsKqWfHX7zZbUQa85Ze8774Rg=='
        self.createUser(name, pw_hash, True)

        # Try to "login"
        theuser = user.User(self.request, name=name, password=password)
        assert theuser.valid
        # Check if the stored password was auto-upgraded on login and saved
        theuser = user.User(self.request, name=name, password=password)
        assert theuser.enc_password.startswith(self.password_scheme)

    def test_auth_with_passlib_stored_password(self):
        """
        Create user with {PASSLIB} password and check that user can login.
        """
        if not self.passlib_support:
            py.test.skip("test requires passlib, but passlib_support is False")
        # Create test user
        name = 'Test User'
        password = '12345'
        pw_hash = '{PASSLIB}$6$rounds=1001$/AVWSh/RUWpcppfl$8DCRGLaBD3KoV4Ag67sUv6b2QdrUFXk1yWCxqWnBLJ.iHSe4Piv6nqzSQgELeLPIvwTC9APaWv1XCTOHjkLOj/'
        self.createUser(name, pw_hash, True)

        # Try to "login"
        theuser = user.User(self.request, name=name, password=password)
        assert theuser.valid
        # Check if the stored password was auto-upgraded on login and saved
        theuser = user.User(self.request, name=name, password=password)
        assert theuser.enc_password.startswith(self.password_scheme)

    def testSubscriptionSubscribedPage(self):
        """ user: tests isSubscribedTo  """
        pagename = 'HelpMiscellaneous'
        name = '__Jürgen Herman__'
        password = name
        self.createUser(name, password)
        # Login - this should replace the old password in the user file
        theUser = user.User(self.request, name=name, password=password)
        theUser.subscribe(pagename)
        assert theUser.isSubscribedTo([pagename]) # list(!) of pages to check

    def testSubscriptionSubPage(self):
        """ user: tests isSubscribedTo on a subpage """
        pagename = 'HelpMiscellaneous'
        testPagename = 'HelpMiscellaneous/FrequentlyAskedQuestions'
        name = '__Jürgen Herman__'
        password = name
        self.createUser(name, password)
        # Login - this should replace the old password in the user file
        theUser = user.User(self.request, name=name, password=password)
        theUser.subscribe(pagename)
        assert not theUser.isSubscribedTo([testPagename]) # list(!) of pages to check

    def testRenameUser(self):
        """ create user and then rename user and check whether
        the old username is removed (and the lookup cache behaves well)
        """
        # Create test user
        name = '__Some Name__'
        password = name
        self.createUser(name, password)
        # Login - this should replace the old password in the user file
        theUser = user.User(self.request, name=name)
        # Rename user
        theUser.name = '__SomeName__'
        theUser.save()
        theUser = user.User(self.request, name=name, password=password)

        assert not theUser.exists()

    def test_for_email_attribute_by_name(self):
        """
        checks for no access to the email attribute by getting the user object from name
        """
        name = "__TestUser__"
        password = "ekfdweurwerh"
        email = "__TestUser__@moinhost"
        self.createUser(name, password, email=email)
        theuser = user.User(self.request, name=name)
        assert theuser.email == ""

    def test_for_email_attribut_by_uid(self):
        """
        checks access to the email attribute by getting the user object from the uid
        """
        name = "__TestUser2__"
        password = "ekERErwerwerh"
        email = "__TestUser2__@moinhost"
        self.createUser(name, password, email=email)
        uid = user.getUserId(self.request, name)
        theuser = user.User(self.request, uid)
        assert theuser.email == email

    # Helpers ---------------------------------------------------------

    def createUser(self, name, password, pwencoded=False, email=None):
        """ helper to create test user
        """
        # Create user
        self.user = user.User(self.request)
        self.user.name = name
        self.user.email = email
        if not pwencoded:
            password = user.encodePassword(self.request.cfg, password)
        self.user.enc_password = password

        # Validate that we are not modifying existing user data file!
        if self.user.exists():
            self.user = None
            py.test.skip("Test user exists, will not override existing user data file!")

        # Save test user
        self.user.save()

        # Validate user creation
        if not self.user.exists():
            self.user = None
            py.test.skip("Can't create test user")


class TestGroupName(object):

    def testGroupNames(self):
        """ user: isValidName: reject group names """
        test = 'AdminGroup'
        assert not user.isValidName(self.request, test)


class TestIsValidName(object):

    def testNonAlnumCharacters(self):
        """ user: isValidName: reject unicode non alpha numeric characters

        : and , used in acl rules, we might add more characters to the syntax.
        """
        invalid = '! # $ % ^ & * ( ) = + , : ; " | ~ / \\ \u0000 \u202a'.split()
        base = 'User%sName'
        for c in invalid:
            name = base % c
            assert not user.isValidName(self.request, name)

    def testWhitespace(self):
        """ user: isValidName: reject leading, trailing or multiple whitespace """
        cases = (
            ' User Name',
            'User Name ',
            'User   Name',
            )
        for test in cases:
            assert not user.isValidName(self.request, test)

    def testValid(self):
        """ user: isValidName: accept names in any language, with spaces """
        cases = (
            'Jürgen Hermann', # German
            'ניר סופר', # Hebrew
            'CamelCase', # Good old camel case
            '가각간갇갈 갉갊감 갬갯걀갼' # Hangul (gibberish)
            )
        for test in cases:
            assert user.isValidName(self.request, test)


coverage_modules = ['MoinMoin.user']

