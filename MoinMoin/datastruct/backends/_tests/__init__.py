# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.datastruct.backends base test classes.

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
                2008 by MoinMoin:MelitaMihaljevic
                2009 by MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.

"""

from py.test import raises

from MoinMoin import security
from MoinMoin.datastruct import GroupDoesNotExistError


class GroupsBackendTest(object):

    test_groups = {'EditorGroup': ['AdminGroup', 'John', 'JoeDoe', 'Editor1', 'John'],
                   'AdminGroup': ['Admin1', 'Admin2', 'John'],
                   'OtherGroup': ['SomethingOther'],
                   'RecursiveGroup': ['Something', 'OtherRecursiveGroup'],
                   'OtherRecursiveGroup': ['RecursiveGroup', 'Anything', 'NotExistingGroup'],
                   'ThirdRecursiveGroup': ['ThirdRecursiveGroup', 'Banana'],
                   'EmptyGroup': [],
                   'CheckNotExistingGroup': ['NotExistingGroup']}


    expanded_groups = {'EditorGroup': ['Admin1', 'Admin2', 'John',
                                        'JoeDoe', 'Editor1'],
                       'AdminGroup': ['Admin1', 'Admin2', 'John'],
                       'OtherGroup': ['SomethingOther'],
                       'RecursiveGroup': ['Anything', 'Something', 'NotExistingGroup'],
                       'OtherRecursiveGroup': ['Anything', 'Something', 'NotExistingGroup'],
                       'ThirdRecursiveGroup': ['Banana'],
                       'EmptyGroup': [],
                       'CheckNotExistingGroup': ['NotExistingGroup']}

    def test_contains(self):
        """
        Test group_wiki Backend and Group containment methods.
        """
        groups = self.request.groups

        for group, members in self.expanded_groups.items():
            assert group in groups
            for member in members:
                assert member in groups[group]

        raises(GroupDoesNotExistError, lambda: groups['NotExistingGroup'])

    def test_contains_group(self):
        groups = self.request.groups

        assert 'AdminGroup' in groups['EditorGroup']
        assert 'EditorGroup' not in groups['AdminGroup']

    def test_iter(self):
        groups = self.request.groups

        for group, members in self.expanded_groups.items():
            returned_members = list(groups[group])
            assert len(returned_members) == len(members)
            for member in members:
                assert member in returned_members

    def test_get(self):
        groups = self.request.groups

        assert groups.get('AdminGroup')
        assert 'NotExistingGroup' not in groups
        assert groups.get('NotExistingGroup') is None
        assert groups.get('NotExistingGroup', []) == []

    def test_groups_with_member(self):
        groups = self.request.groups

        john_groups = list(groups.groups_with_member('John'))
        assert 2 == len(john_groups)
        assert 'EditorGroup' in john_groups
        assert 'AdminGroup' in john_groups
        assert 'ThirdGroup' not in john_groups

    def test_backend_acl_allow(self):
        """
        Test if the wiki group backend works with acl code.
        Check user which has rights.
        """
        request = self.request

        acl_rights = ["AdminGroup:admin,read,write"]
        acl = security.AccessControlList(request.cfg, acl_rights)

        for user in self.expanded_groups['AdminGroup']:
            for permission in ["read", "write", "admin"]:
                assert acl.may(request, "Admin1", permission), '%s must have %s permission because he is member of the AdminGroup' % (user, permission)

    def test_backend_acl_deny(self):
        """
        Test if the wiki group backend works with acl code.
        Check user which does not have rights.
        """
        request = self.request

        acl_rights = ["AdminGroup:read,write"]
        acl = security.AccessControlList(request.cfg, acl_rights)

        assert "SomeUser" not in request.groups['AdminGroup']
        for permission in ["read", "write"]:
            assert not acl.may(request, "SomeUser", permission), 'SomeUser must not have %s permission because he is not listed in the AdminGroup' % permission

        assert 'Admin1' in request.groups['AdminGroup']
        assert not acl.may(request, "Admin1", "admin")

    def test_backend_acl_with_all(self):
        request = self.request

        acl_rights = ["EditorGroup:read,write,delete,admin All:read"]
        acl = security.AccessControlList(request.cfg, acl_rights)

        for member in self.expanded_groups['EditorGroup']:
            for permission in ["read", "write", "delete", "admin"]:
                assert acl.may(request, member, permission)

        assert acl.may(request, "Someone", "read")
        for permission in ["write", "delete", "admin"]:
            assert not acl.may(request, "Someone", permission)

    def test_backend_acl_not_existing_group(self):
        request = self.request
        assert 'NotExistingGroup' not in request.groups

        acl_rights = ["NotExistingGroup:read,write,delete,admin All:read"]
        acl = security.AccessControlList(request.cfg, acl_rights)

        assert not acl.may(request, "Someone", "write")


class DictsBackendTest(object):

    dicts = {'SomeTestDict': {'First': 'first item',
                               'text with spaces': 'second item',
                               'Empty string': '',
                               'Last': 'last item'},
             'SomeOtherTestDict': {'One': '1',
                                    'Two': '2'}}

    def test_getitem(self):
        expected_dicts = self.dicts
        dicts = self.request.dicts

        for dict_name, expected_dict in list(expected_dicts.items()):
            test_dict = dicts[dict_name]
            assert len(test_dict) == len(expected_dict)
            for key, value in list(expected_dict.items()):
                assert test_dict[key] == value

    def test_contains(self):
        dicts = self.request.dicts

        for key in self.dicts:
            assert key in dicts

        assert 'SomeNotExistingDict' not in dicts

    def test_update(self):
        dicts = self.request.dicts

        d = {}
        d.update(dicts['SomeTestDict'])

        assert 'First' in d

    def test_get(self):
        dicts = self.request.dicts

        for dict_name in self.dicts:
            assert dicts.get(dict_name)

        assert 'SomeNotExistingDict' not in dicts
        assert dicts.get('SomeNotExistingDict') is None
        assert dicts.get('SomeNotExistingDict', {}) == {}


        for dict_name, expected_dict in list(self.dicts.items()):
            test_dict = dicts[dict_name]
            for key, value in list(expected_dict.items()):
                assert 'SomeNotExistingKey' not in test_dict
                assert test_dict.get('SomeNotExistingKey') is None
                assert test_dict.get('SomeNotExistingKey', {}) == {}

