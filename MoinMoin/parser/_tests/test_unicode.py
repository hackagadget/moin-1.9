# -*- coding: utf-8 -*-
"""
    MoinMoin - Test if MoinMoin.parser.* do write UNICODE objects

    Comment:
    The test produces an exception in another place, if some routine encodes unicode to UTF8 too early.
    The corresponding bug was found initially in MoinMoin.parser.text_xslt and the test was designed for
    this problem, but the test actually examines all available parsers.

    @copyright: 2007,2008 by Raphael Bossek <raphael.bossek@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import py
import sys, traceback

import MoinMoin.parser
from MoinMoin.Page import Page

class TestParserOutput(object):
    """ Parser has to generate unicode output. """
    def test_ParserOutput(self):
        """ This method aims generally at MoinMoin.parser.text_xslt -
            this parser should encode Unicode input to UTF8 as late as possible.
        """
        request = self.request
        assert not request.cfg.allow_xslt, 'allow_xslt should be disabled'
        errmsg = []

        # Some examples to verify with additional stuff
        parser_raw_input = {
            'text_html': '<html><body><h1>%s</h1></body></html>',
            'text_irssi': "[12:01] <RaphaelBosek> %s",
            'text_moin_wiki': '||<#fefefe> %s ||',
            'text_python': 'if True: print "%s"',
            'text_xslt': '<?xml version="1.0" encoding="ISO-8859-1"?><!-- %s -->',
        }

        # Blacklist for parsers that don't work - this list should be empty !
        parser_blacklist = []

        # Create a page if it doesn't exist already.
        if not 'page' in request.formatter.__dict__ or not request.formatter.page:
            request.formatter.page = Page(request, 'test_parser_unicode_page')
            # this temporarily fixes an error with page-names, should be fixed at a central place some time
            request.page = Page(request, 'test_parser_unicode_page')

        # Check all parsers for UNICODE output.
        for parsername in MoinMoin.parser.modules:
            if parsername in parser_blacklist:
                continue

            module = __import__('MoinMoin.parser', globals(), {}, [parsername])
            parsermodule = getattr(module, parsername)
            if 'Parser' in parsermodule.__dict__:
                # Get the parser_input or use a simple fallback if the parser is not found in parser_raw_input
                i = parser_raw_input.get(parsername, '%s') % '\xC3\x84\xC3\x96\xC3\x9C\xC3\xE2\x82\xAC\x27'
                p = parsermodule.Parser(i, request)

                # This is the actual request that would produce an exception, which would usually look like the following:
                # >  UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3 in position 0: ordinal not in range(128)
                # usually occurring in python/lib/StringIO.py:270
                r = request.redirectedOutput(p.format, request.formatter)

                # This assertion will only be triggered, if the parser does not write unicode at all
                assert isinstance(r, str), 'MoinMoin.parser.%s does not write UNICODE data but %s' % (parsername, type(r), )

coverage_modules = ['MoinMoin.parser']

