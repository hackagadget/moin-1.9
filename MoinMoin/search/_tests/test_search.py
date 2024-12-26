# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.search Tests

    We exclude underlay/system pages for some search tests to save time.

    @copyright: 2005 by Nir Soffer <nirs@freeshell.org>,
                2007-2010 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""


import os, io, time

import py

from MoinMoin.search import QueryError, _get_searcher
from MoinMoin.search.queryparser import QueryParser
from MoinMoin.search.builtin import MoinSearch
from MoinMoin._tests import nuke_xapian_index, wikiconfig, become_trusted, create_page, nuke_page, append_page
from MoinMoin.wikiutil import Version
from MoinMoin.action import AttachFile

PY_MIN_VERSION = '1.0.0'
if Version(version=py.version) < Version(version=PY_MIN_VERSION):
    # There are some generative tests, which won't run on older versions!
    # XXX These tests should be refactored to be able to be run with older versions of py.
    py.test.skip('Currently py version %s is needed' % PY_MIN_VERSION)


class TestQueryParsing(object):
    """ search: query parser tests """

    def testQueryParser(self):
        """ search: test the query parser """
        parser = QueryParser()
        for query, wanted in [
            # Even a single term is a and expression (this is needed for xapian because it
            # only has AND_NOT, but not a simple NOT).  This is why we have many many brackets here.
            ("a", '["a"]'),
            ("-a", '[-"a"]'),
            ("a b", '["a" "b"]'),
            ("a -b c", '["a" -"b" "c"]'),
            ("aaa bbb -ccc", '["aaa" "bbb" -"ccc"]'),
            ("title:aaa title:bbb -title:ccc", '[title:"aaa" title:"bbb" -title:"ccc"]'),
            ("title:case:aaa title:re:bbb -title:re:case:ccc", '[title:case:"aaa" title:re:"bbb" -title:re:case:"ccc"]'),
            ("linkto:aaa", '[linkto:"aaa"]'),
            ("category:aaa", '[category:"aaa"]'),
            ("domain:aaa", '[domain:"aaa"]'),
            ("re:case:title:aaa", '[title:re:case:"aaa"]'),
            ("(aaa or bbb) and (ccc or ddd)", '[[[["aaa"] or ["bbb"]]] [[["ccc"] or ["ddd"]]]]'),
            ("(aaa or bbb) (ccc or ddd)", '[[[["aaa"] or ["bbb"]]] [[["ccc"] or ["ddd"]]]]'),
            ("aaa or bbb", '[[["aaa"] or ["bbb"]]]'),
            ("aaa or bbb or ccc", '[[["aaa"] or [[["bbb"] or ["ccc"]]]]]'),
            ("aaa or bbb and ccc", '[[["aaa"] or ["bbb" "ccc"]]]'),
            ("aaa and bbb or ccc", '[[["aaa" "bbb"] or ["ccc"]]]'),
            ("aaa and bbb and ccc", '["aaa" "bbb" "ccc"]'),
            ("aaa or bbb and ccc or ddd", '[[["aaa"] or [[["bbb" "ccc"] or ["ddd"]]]]]'),
            ("aaa or bbb ccc or ddd", '[[["aaa"] or [[["bbb" "ccc"] or ["ddd"]]]]]'),
            ("(HelpOn) (Administration)", '[["HelpOn"] ["Administration"]]'),
            ("(HelpOn) (-Administration)", '[["HelpOn"] [-"Administration"]]'),
            ("(HelpOn) and (-Administration)", '[["HelpOn"] [-"Administration"]]'),
            ("(HelpOn) and (Administration) or (Configuration)", '[[[["HelpOn"] ["Administration"]] or [["Configuration"]]]]'),
            ("(a) and (b) or (c) or -d", '[[[["a"] ["b"]] or [[[["c"]] or [-"d"]]]]]'),
            ("a b c d e or f g h", '[[["a" "b" "c" "d" "e"] or ["f" "g" "h"]]]'),
            ('"no', '[""no"]'),
            ('no"', '["no""]'),
            ("'no", "[\"'no\"]"),
            ("no'", "[\"no'\"]"),
            ('"no\'', '[""no\'"]')]:
            result = parser.parse_query(query)
            assert str(result) == wanted

    def testQueryParserExceptions(self):
        """ search: test the query parser """
        parser = QueryParser()

        def _test(q):
            py.test.raises(QueryError, parser.parse_query, q)

        for query in ['""', '(', ')', '(a or b']:
            yield _test, query


class BaseSearchTest(object):
    """ search: test search """
    doesnotexist = 'jfhsdaASDLASKDJ'

    # key - page name, value - page content. If value is None page
    # will not be created but will be used for a search. None should
    # be used for pages which already exist.
    pages = {'SearchTestPage': 'this is a test page',
             'SearchTestLinks': 'SearchTestPage',
             'SearchTestLinksLowerCase': 'searchtestpage',
             'SearchTestOtherLinks': 'SearchTestLinks',
             'TestEdit': 'TestEdit',
             'TestOnEditing': 'another test page',
             'ContentSearchUpper': 'Find the NEEDLE in the haystack.',
             'ContentSearchLower': 'Find the needle in the haystack.',
             'LanguageSetup': None,
             'CategoryHomepage': None,
             'HomePageWiki': None,
             'FrontPage': None,
             'RecentChanges': None,
             'HelpOnCreoleSyntax': None,
             'HelpIndex': None,
            }

    searcher_class = None

    def _index_update(self):
        pass

    @classmethod
    def setup_class(cls):
        request = cls.request
        become_trusted(request)

        for page, text in cls.pages.items():
            if text:
                create_page(request, page, text)

    def teardown_class(self):
        for page, text in self.pages.items():
            if text:
                nuke_page(self.request, page)

    def get_searcher(self, query):
        raise NotImplementedError

    def search(self, query):
        if isinstance(query, str) or isinstance(query, str):
            query = QueryParser().parse_query(query)

        return self.get_searcher(query).run()

    def test_title_search_simple(self):
        searches = {'title:SearchTestPage': 1,
                    'title:LanguageSetup': 1,
                    'title:HelpIndex': 1,
                    'title:Help': 2,
                    'title:TestOn': 1,
                    'title:SearchTestNotExisting': 0,
                    'title:FrontPage': 1,
                    'title:TestOnEditing': 1,
                   }

        def test(query, res_count):
            result = self.search(query)
            test_result = len(result.hits)
            assert test_result == res_count

        for query, res_count in searches.items():
            yield query, test, query, res_count

    def test_title_search_re(self):
        expected_pages = set(['SearchTestPage', 'SearchTestLinks', 'SearchTestLinksLowerCase', 'SearchTestOtherLinks', ])
        result = self.search(r'-domain:underlay -domain:system title:re:\bSearchTest')
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        result = self.search(r'-domain:underlay -domain:system title:re:\bSearchTest\b')
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

    def test_title_search_case(self):
        expected_pages = set(['SearchTestPage', ])
        result = self.search('-domain:underlay -domain:system title:case:SearchTestPage')
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        result = self.search('-domain:underlay -domain:system title:case:searchtestpage')
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

    def test_title_search_case_re(self):
        expected_pages = set(['SearchTestPage', ])
        result = self.search(r'-domain:underlay -domain:system title:case:re:\bSearchTestPage\b')
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        result = self.search(r'-domain:underlay -domain:system title:case:re:\bsearchtestpage\b')
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

    def test_linkto_search_simple(self):
        expected_pages = set(['SearchTestLinks', ])
        result = self.search('-domain:underlay -domain:system linkto:SearchTestPage')
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        result = self.search('-domain:underlay -domain:system linkto:SearchTestNotExisting')
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

    def test_linkto_search_re(self):
        expected_pages = set(['SearchTestLinks', 'SearchTestOtherLinks', ])
        result = self.search(r'-domain:underlay -domain:system linkto:re:\bSearchTest')
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        result = self.search(r'-domain:underlay -domain:system linkto:re:\bSearchTest\b')
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

    def test_linkto_search_case(self):
        expected_pages = set(['SearchTestLinks', ])
        result = self.search('-domain:underlay -domain:system linkto:case:SearchTestPage')
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        result = self.search('-domain:underlay -domain:system linkto:case:searchtestpage')
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

    def test_linkto_search_case_re(self):
        expected_pages = set(['SearchTestLinks', ])
        result = self.search(r'-domain:underlay -domain:system linkto:case:re:\bSearchTestPage\b')
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        result = self.search(r'-domain:underlay -domain:system linkto:case:re:\bsearchtestpage\b')
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

    def test_category_search_simple(self):
        expected_pages = set(['HomePageWiki', ])
        result = self.search('category:CategoryHomepage')
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        result = self.search('category:CategorySearchTestNotExisting')
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

    def test_category_search_re(self):
        expected_pages = set(['HomePageWiki', ])
        result = self.search(r'category:re:\bCategoryHomepage\b')
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        result = self.search(r'category:re:\bCategoryHomepa\b')
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

    def test_category_search_case(self):
        expected_pages = set(['HomePageWiki', ])
        result = self.search('category:case:CategoryHomepage')
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        result = self.search('category:case:categoryhomepage')
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

    def test_category_search_case_re(self):
        expected_pages = set(['HomePageWiki', ])
        result = self.search(r'category:case:re:\bCategoryHomepage\b')
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        result = self.search(r'category:case:re:\bcategoryhomepage\b')
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

    def test_mimetype_search_simple(self):
        result = self.search('mimetype:text/wiki')
        test_result = len(result.hits)
        assert test_result == 14

    def test_mimetype_search_re(self):
        result = self.search(r'mimetype:re:\btext/wiki\b')
        test_result = len(result.hits)
        assert test_result == 14

        result = self.search(r'category:re:\bCategoryHomepa\b')
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

    def test_language_search_simple(self):
        result = self.search('language:en')
        test_result = len(result.hits)
        assert test_result == 14

    def test_domain_search_simple(self):
        result = self.search('domain:system')
        assert result.hits

    def test_search_and(self):
        """ search: title search with AND expression """
        expected_pages = set(['HelpOnCreoleSyntax', ])
        result = self.search("title:HelpOnCreoleSyntax lang:en")
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        result = self.search("title:HelpOnCreoleSyntax lang:de")
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

        result = self.search("title:Help title:%s" % self.doesnotexist)
        found_pages = set([hit.page_name for hit in result.hits])
        assert not found_pages

    def testTitleSearchOR(self):
        """ search: title search with OR expression """
        expected_pages = set(['FrontPage', 'RecentChanges', ])
        result = self.search("title:FrontPage or title:RecentChanges")
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

    def testTitleSearchNegatedFindAll(self):
        """ search: negated title search for some pagename that does not exist results in all pagenames """
        result = self.search("-title:%s" % self.doesnotexist)
        n_pages = len(self.pages)
        test_result = len(result.hits)
        assert test_result == n_pages

    def testTitleSearchNegativeTerm(self):
        """ search: title search for a AND expression with a negative term """
        result = self.search("-title:FrontPage")
        found_pages = set([hit.page_name for hit in result.hits])
        assert 'FrontPage' not in found_pages
        test_result = len(result.hits)
        n_pages = len(self.pages) - 1
        assert test_result == n_pages

        result = self.search("-title:HelpOn")
        test_result = len(result.hits)
        n_pages = len(self.pages) - 1
        assert test_result == n_pages

    def testFullSearchNegatedFindAll(self):
        """ search: negated full search for some string that does not exist results in all pages """
        result = self.search("-%s" % self.doesnotexist)
        test_result = len(result.hits)
        n_pages = len(self.pages)
        assert test_result == n_pages

    def testFullSearchRegexCaseInsensitive(self):
        """ search: full search for regular expression (case insensitive) """
        search_re = 'ne{2}dle' # matches 'NEEDLE' or 'needle' or ...
        expected_pages = set(['ContentSearchUpper', 'ContentSearchLower', ])
        result = self.search('-domain:underlay -domain:system re:%s' % search_re)
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

    def testFullSearchRegexCaseSensitive(self):
        """ search: full search for regular expression (case sensitive) """
        search_re = 'ne{2}dle' # matches 'needle'
        expected_pages = set(['ContentSearchLower', ])
        result = self.search('-domain:underlay -domain:system re:case:%s' % search_re)
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

    def test_title_search(self):
        expected_pages = set(['FrontPage', ])
        query = QueryParser(titlesearch=True).parse_query('FrontPage')
        result = self.search(query)
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

    def test_create_page(self):
        expected_pages = set(['TestCreatePage', ])
        self.pages['TestCreatePage'] = 'some text' # Moin search must search this page
        try:
            create_page(self.request, 'TestCreatePage', self.pages['TestCreatePage'])
            self._index_update()
            result = self.search('-domain:underlay -domain:system TestCreatePage')
            found_pages = set([hit.page_name for hit in result.hits])
            assert found_pages == expected_pages
        finally:
            nuke_page(self.request, 'TestCreatePage')
            self._index_update()
            del self.pages['TestCreatePage']
            result = self.search('-domain:underlay -domain:system TestCreatePage')
            found_pages = set([hit.page_name for hit in result.hits])
            assert not found_pages

    def test_attachment(self):
        page_name = 'TestAttachment'
        self.pages[page_name] = 'some text' # Moin search must search this page

        filename = "AutoCreatedSillyAttachmentForSearching.png"
        data = "Test content"
        filecontent = io.StringIO(data)

        result = self.search(filename)
        found_attachments = set([(hit.page_name, hit.attachment) for hit in result.hits])
        assert not found_attachments

        try:
            create_page(self.request, page_name, self.pages[page_name])
            AttachFile.add_attachment(self.request, page_name, filename, filecontent, True)
            append_page(self.request, page_name, '[[attachment:%s]]' % filename)
            self._index_update()
            result = self.search(filename)
            found_attachments = set([(hit.page_name, hit.attachment) for hit in result.hits])
            assert (page_name, '') in found_attachments
            assert 1 <= len(found_attachments) <= 2
            # Note: moin search returns (page_name, '') as only result
            #       xapian search returns 2 results: (page_name, '') and (page_name, filename)
            # TODO: make behaviour the same, if possible
        finally:
            nuke_page(self.request, page_name)
            del self.pages[page_name]
            self._index_update()
            result = self.search(filename)
            found_attachments = set([(hit.page_name, hit.attachment) for hit in result.hits])
            assert not found_attachments

    def test_get_searcher(self):
        assert isinstance(_get_searcher(self.request, ''), self.searcher_class)


class TestMoinSearch(BaseSearchTest):
    """ search: test Moin search """
    searcher_class = MoinSearch

    def get_searcher(self, query):
        pages = [{'pagename': page, 'attachment': '', 'wikiname': 'Self', } for page in self.pages]
        return MoinSearch(self.request, query, pages=pages)

    def test_stemming(self):
        expected_pages = set(['TestEdit', 'TestOnEditing', ])
        result = self.search("title:edit")
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        expected_pages = set(['TestOnEditing', ])
        result = self.search("title:editing")
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages


class TestXapianSearch(BaseSearchTest):
    """ search: test Xapian indexing / search """

    class Config(wikiconfig.Config):
        xapian_search = True

    def _index_update(self):
        # for xapian, we queue index updates so they can get indexed later.
        # here we make sure the queue will be processed completely,
        # before we continue:
        from MoinMoin.search.Xapian import XapianIndex
        XapianIndex(self.request).do_queued_updates()

    def get_searcher(self, query):
        from MoinMoin.search.Xapian.search import XapianSearch
        return XapianSearch(self.request, query)

    def get_moin_search_connection(self):
        from MoinMoin.search.Xapian import XapianIndex
        return XapianIndex(self.request).get_search_connection()

    def setup_class(self):
        try:
            from MoinMoin.search.Xapian import XapianIndex
            from MoinMoin.search.Xapian.search import XapianSearch
            self.searcher_class = XapianSearch

        except ImportError as error:
            if not str(error).startswith('Xapian '):
                raise
            py.test.skip('xapian is not installed')

        nuke_xapian_index(self.request)
        index = XapianIndex(self.request)
        # Additionally, pages which were not created but supposed to be searched
        # are indexed.
        pages_to_index = [page for page in self.pages if not self.pages[page]]
        index.indexPages(mode='add', pages=pages_to_index)

        super(TestXapianSearch, self).setup_class()

    def teardown_class(self):
        nuke_xapian_index(self.request)

    def test_get_all_documents(self):
        connection = self.get_moin_search_connection()
        documents = connection.get_all_documents()
        n_pages = len(self.pages)
        test_result = len(documents)
        assert test_result == n_pages
        for document in documents:
            assert document.data['pagename'][0] in list(self.pages.keys())

    def test_xapian_term(self):
        parser = QueryParser()
        connection = self.get_moin_search_connection()

        prefixes = {'': (['', 're:', 'case:', 'case:re:'], 'SearchTestPage'),
                    'title:': (['', 're:', 'case:', 'case:re:'], 'SearchTestPage'),
                    'linkto:': (['', 're:', 'case:', 'case:re:'], 'FrontPage'),
                    'category:': (['', 're:', 'case:', 'case:re:'], 'CategoryHomepage'),
                    'mimetype:': (['', 're:'], 'text/wiki'),
                    'language:': ([''], 'en'),
                    'domain:': ([''], 'system'),
                   }

        def test_query(query):
            query_ = parser.parse_query(query).xapian_term(self.request, connection)
            print(str(query_))
            assert not query_.empty()

        for prefix, data in prefixes.items():
            modifiers, term = data
            for modifier in modifiers:
                query = ''.join([prefix, modifier, term])
                yield query, test_query, query

    def test_stemming(self):
        expected_pages = set(['TestEdit', ])
        result = self.search("title:edit")
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        expected_pages = set(['TestOnEditing', ])
        result = self.search("title:editing")
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages


class TestXapianSearchStemmed(TestXapianSearch):
    """ search: test Xapian indexing / search - with stemming enabled """

    class Config(wikiconfig.Config):
        xapian_search = True
        xapian_stemming = True

    def test_stemming(self):
        py.test.skip("TODO fix TestXapianSearchStemmed - strange effects with stemming")

        expected_pages = set(['TestEdit', 'TestOnEditing', ])
        result = self.search("title:edit")
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages

        expected_pages = set(['TestEdit', 'TestOnEditing', ])
        result = self.search("title:editing")
        found_pages = set([hit.page_name for hit in result.hits])
        assert found_pages == expected_pages


class TestGetSearcher(object):

    class Config(wikiconfig.Config):
        xapian_search = True

    def test_get_searcher(self):
        assert isinstance(_get_searcher(self.request, ''), MoinSearch), 'Xapian index is not created, despite the configuration, MoinSearch must be used!'

coverage_modules = ['MoinMoin.search']

