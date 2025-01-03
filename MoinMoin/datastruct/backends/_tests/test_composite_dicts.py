# -*- coding: iso-8859-1 -*-

"""
MoinMoin.datastruct.backends.composite_dicts test

@copyright: 2009 MoinMoin:DmitrijsMilajevs
            2008 MoinMoin: MelitaMihaljevic
@license: GPL, see COPYING for details
"""

from py.test import raises

from MoinMoin.datastruct.backends._tests import DictsBackendTest
from MoinMoin.datastruct import ConfigDicts, CompositeDicts, DictDoesNotExistError
from MoinMoin._tests import wikiconfig
from MoinMoin import security


class TestCompositeDict(DictsBackendTest):

    class Config(wikiconfig.Config):

        one_dict = {'SomeTestDict': {'First': 'first item',
                                      'text with spaces': 'second item',
                                      'Empty string': '',
                                      'Last': 'last item'}}

        other_dict = {'SomeOtherTestDict': {'One': '1',
                                             'Two': '2'}}

        def dicts(self, request):
            return CompositeDicts(request,
                                  ConfigDicts(request, self.one_dict),
                                  ConfigDicts(request, self.other_dict))


coverage_modules = ['MoinMoin.datastruct.backends.composite_dicts']
