# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.search.Xapian.tokenizer Tests

    @copyright: 2009 MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.
"""

import py
from MoinMoin._tests import wikiconfig

try:
    from MoinMoin.search.Xapian.tokenizer import WikiAnalyzer
except ImportError:
    py.test.skip('xapian is not installed')

class TestWikiAnalyzer(object):

    word = 'HelpOnMoinTesting'
    words = {word.lower(): '',
             'help': '',
             'on': '',
             'moin': '',
             'testing': ''}

    def setup_class(self):
        self.analyzer = WikiAnalyzer(request=self.request, language=self.request.cfg.language_default)

    def test_tokenize(self):
        words = self.words
        tokens = list(self.analyzer.tokenize(self.word))

        assert len(tokens) == len(words)

        for token, stemmed in tokens:
            assert token in words
            assert words[token] == stemmed


class TestWikiAnalyzerStemmed(TestWikiAnalyzer):

    word = 'HelpOnMoinTesting'
    words = {word.lower(): 'helponmointest',
             'help': '',
             'on': '',
             'moin': '',
             'testing': 'test'}

    class Config(wikiconfig.Config):

        xapian_stemming = True


class TestWikiAnalyzerSeveralWords(TestWikiAnalyzer):

    word = 'HelpOnMoinTesting OtherWikiWord'
    words = {'helponmointesting': '',
             'help': '',
             'on': '',
             'moin': '',
             'testing': '',
             'otherwikiword': '',
             'other': '',
             'wiki': '',
             'word': ''}


class TestWikiAnalyzerStemmedSeveralWords(TestWikiAnalyzer):

    word = 'HelpOnMoinTesting OtherWikiWord'
    words = {'helponmointesting': 'helponmointest',
             'help': '',
             'on': '',
             'moin': '',
             'testing': 'test',
             'otherwikiword': '',
             'other': '',
             'wiki': '',
             'word': ''}

    class Config(wikiconfig.Config):

        xapian_stemming = True


class TestWikiAnalyzerStemmedHelpOnEditing(TestWikiAnalyzer):

    word = 'HelpOnEditing'
    words = {'helponediting': 'helponedit',
             'help': '',
             'on': '',
             'editing': 'edit'}

    class Config(wikiconfig.Config):

        xapian_stemming = True


class TestWikiAnalyzerStemmedCategoryHomepage(TestWikiAnalyzer):

    word = 'CategoryHomepage'
    words = {'categoryhomepage': 'categoryhomepag',
             'category': 'categori',
             'homepage': 'homepag'}

    class Config(wikiconfig.Config):

        xapian_stemming = True
