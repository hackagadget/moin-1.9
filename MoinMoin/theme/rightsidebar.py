# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - rightsidebar theme

    Created by and for crw.
    Later it was rewritten by Nir Soffer for MoinMoin release 1.3.

    @copyright: 2005 Nir Soffer
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.theme import ThemeBase

class Theme(ThemeBase):

    name = "rightsidebar"

    def wikipanel(self, d):
        """ Create wiki panel """
        _ = self.request.getText
        html = [
            '<div class="sidepanel">',
            '<h1>%s</h1>' % _("Wiki"),
            self.navibar(d),
            '</div>',
            ]
        return '\n'.join(html)

    def pagepanel(self, d):
        """ Create page panel """
        _ = self.request.getText
        if self.shouldShowEditbar(d['page']):
            html = [
                '<div class="sidepanel">',
                '<h1>%s</h1>' % _("Page"),
                self.editbar(d),
                '</div>',
                ]
            return '\n'.join(html)
        return ''

    def userpanel(self, d):
        """ Create user panel """
        _ = self.request.getText

        html = [
            '<div class="sidepanel">',
            '<h1>%s</h1>' % _("User"),
            self.username(d),
            '</div>'
            ]
        return '\n'.join(html)

    def header(self, d):
        """
        Assemble page header

        @param d: parameter dictionary
        @rtype: string
        @return: page header html
        """
        _ = self.request.getText

        html = [
            # Custom html above header
            self.emit_custom_html(self.cfg.page_header1),

            # Header
            '<div id="header">',
            self.searchform(d),
            self.logo(),
            '<div id="locationline">',
            self.interwiki(d),
            self.title(d),
            '</div>',
            self.trail(d),
            '</div>',

            # Custom html below header (not recomended!)
            self.emit_custom_html(self.cfg.page_header2),

            # Sidebar
            '<div id="sidebar">',
            self.wikipanel(d),
            self.pagepanel(d),
            self.userpanel(d),
            '</div>',

            self.msg(d),

            # Page
            self.startPage(),
            ]
        return '\n'.join(html)

    def editorheader(self, d):
        """
        Assemble page header for editor

        @param d: parameter dictionary
        @rtype: string
        @return: page header html
        """
        _ = self.request.getText

        html = [
            # Custom html above header
            self.emit_custom_html(self.cfg.page_header1),

            # Header
            #u'<div id="header">',
            #self.searchform(d),
            #self.logo(),
            #u'</div>',

            # Custom html below header (not recomended!)
            self.emit_custom_html(self.cfg.page_header2),

            # Sidebar
            '<div id="sidebar">',
            self.wikipanel(d),
            self.pagepanel(d),
            self.userpanel(d),
            '</div>',

            self.msg(d),

            # Page
            self.startPage(),
            #self.title(d),
            ]
        return '\n'.join(html)

    def footer(self, d, **keywords):
        """ Assemble wiki footer

        @param d: parameter dictionary
        @keyword ...:...
        @rtype: unicode
        @return: page footer html
        """
        page = d['page']
        html = [
            # End of page
            self.pageinfo(page),
            self.endPage(),

            # Pre footer custom html (not recommended!)
            self.emit_custom_html(self.cfg.page_footer1),

            # Footer
            '<div id="footer">',
            self.credits(d),
            self.showversion(d, **keywords),
            '</div>',

            # Post footer custom html
            self.emit_custom_html(self.cfg.page_footer2),
            ]
        return '\n'.join(html)


def execute(request):
    """ Generate and return a theme object

    @param request: the request object
    @rtype: MoinTheme
    @return: Theme object
    """
    return Theme(request)

