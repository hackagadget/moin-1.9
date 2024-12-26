# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.Page Tests

    @copyright: 2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py

from MoinMoin.Page import Page

class TestPage:
    def testMeta(self):
        page = Page(self.request, 'FrontPage')
        meta = page.meta
        for k, v in meta:
            if k == 'format':
                assert v == 'wiki'
            elif k == 'language':
                assert v == 'en'

    def testBody(self):
        page = Page(self.request, 'FrontPage')
        body = page.body
        assert type(body) is str
        assert 'MoinMoin' in body
        assert body.endswith('\n')
        assert '\r' not in body

    def testExists(self):
        assert Page(self.request, 'FrontPage').exists()
        assert not Page(self.request, 'ThisPageDoesNotExist').exists()
        assert not Page(self.request, '').exists()

    def testEditInfoSystemPage(self):
        # system pages have no edit-log (and only 1 revision),
        # thus edit_info will return None
        page = Page(self.request, 'RecentChanges')
        edit_info = page.edit_info()
        assert edit_info == {}

    def testSplitTitle(self):
        page = Page(self.request, "FrontPage")
        assert page.split_title(force=True) == 'Front Page'

    def testGetRevList(self):
        page = Page(self.request, "FrontPage")
        assert 1 in page.getRevList()

    def testGetPageLinks(self):
        page = Page(self.request, "FrontPage")
        assert 'WikiSandBox' in page.getPageLinks(self.request)

    def testSendPage(self):
        page = Page(self.request, "FrontPage")
        import io
        out = io.StringIO()
        self.request.redirect(out)
        page.send_page(msg='Done', emit_headers=False)
        result = out.getvalue()
        self.request.redirect()
        del out
        assert result.strip().endswith('</html>')
        assert result.strip().startswith('<!DOCTYPE HTML PUBLIC')

class TestRootPage:
    def testPageList(self):
        rootpage = self.request.rootpage
        pagelist = rootpage.getPageList()
        assert len(pagelist) > 100
        assert 'FrontPage' in pagelist
        assert '' not in pagelist


coverage_modules = ['MoinMoin.Page']

