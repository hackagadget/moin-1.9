# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.text_html_text_moin_wiki Tests

    @copyright: 2005 by Bastian Blank,
                2005,2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py
#py.test.skip("Many broken tests, much broken code, broken, broken, broken.")

from io import StringIO
from MoinMoin.converter import text_html_text_moin_wiki as converter
from MoinMoin.parser.text_moin_wiki import Parser
from MoinMoin.formatter.text_gedit import Formatter
from MoinMoin.util.clock import Clock
from MoinMoin.error import ConvertError

convert = converter.convert
error = ConvertError


class TestBase(object):

    def do_convert_real(self, func_args, successful=True):
        try:
            ret = convert(*func_args)
        except error as e:
            if successful:
                py.test.fail("fails with parse error: %s" % e)
            else:
                return
        if successful:
            return ret
        else:
            py.test.fail("doesn't fail with parse error")


class MinimalPage(object):
    def __init__(self):
        self.hilite_re = None
        self.page_name = "testpage"


class MinimalRequest(object):
    # TODO: do we really need this class? no other test uses a request replacement.

    def __init__(self, request):
        self.request = request
        self.clock = Clock()

        # This is broken - tests that need correct content_lang will fail
        self.content_lang = None
        self.current_lang = None

        self.form = {}
        self._page_headings = {}
        self.result = []

    def getText(self, text, wiki=False, percent=False):
        return text

    def write(self, text):
        self.result.append(text)

    def __getattr__(self, name):
        return getattr(self.request, name)


class TestConvertBlockRepeatable(TestBase):
    def do(self, text, output):
        text = text.lstrip('\n')
        output = output.strip('\n')
        request = MinimalRequest(self.request)
        page = MinimalPage()
        formatter = Formatter(request)
        formatter.setPage(page)
        Parser(text, request).format(formatter)
        repeat = ''.join(request.result).strip('\n')
        #assert repeat == output
        out = self.do_convert_real([request, page.page_name, repeat])
        assert text == out

    def testComment01(self):
        test = r"""
##test
"""
        output = """<pre class="comment">\n##test</pre>"""
        self.do(test, output)

    def testComment02(self):
        test = r"""
##test
##test
"""
        output = """
<pre class="comment">\n##test</pre>
<pre class="comment">\n##test</pre>
"""
        self.do(test, output)

    def testHeading01(self):
        py.test.skip('broken test')
        test = r"""
= test1 =

"""
        output = r"""
<h2>test1</h2>
"""
        self.do(test, output)

    def testHeading02(self):
        py.test.skip('broken test')
        test = r"""
= test1 =

== test2 ==

"""
        output = r"""
<h2>test1</h2>
<h3>test2</h3>
"""
        self.do(test, output)

    def testListSuccess01(self):
        test = r"""
 * test

"""
        output = r"""
<ul>
<li><p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess02(self):
        test = r"""
 1. test

"""
        output = r"""
<ol type="1">
<li><p>test </p>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess03(self):
        test = r"""
 test:: test

"""
        output = r"""
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess04(self):
        test = r"""
 * test
 * test

"""
        output = r"""
<ul>
<li><p>test </p>
</li>
<li><p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess05(self):
        test = r"""
 1. test
 1. test

"""
        output = r"""
<ol type="1">
<li><p>test </p>
</li>
<li><p>test </p>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess06(self):
        test = r"""
 test:: test
 test:: test

"""
        output = r"""
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess07(self):
        test = r"""
 * test

 * test

"""
        output = r"""
<ul>
<li><p>test </p>
</li>
</ul>
<ul>
<li><p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess08(self):
        test = r"""
 1. test

 1. test

"""
        output = r"""
<ol type="1">
<li><p>test </p>
</li>
</ol>
<ol type="1">
<li><p>test </p>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess09(self):
        py.test.skip('broken test')
        test = r"""
 test:: test

 test:: test

"""
        output = r"""
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess10(self):
        py.test.skip('broken test')
        test = r"""
 * test
  * test

"""
        output = r"""
<ul>
<li><p>test </p>
<ul>
<li><p>test </p>
</li>
</ul>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess11(self):
        py.test.skip('broken test')
        test = r"""
 1. test
  1. test

"""
        output = r"""
<ol type="1">
<li><p>test </p>
<ol type="1">
<li><p>test </p>
</li>
</ol>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess12(self):
        py.test.skip('broken test')
        test = r"""
 test:: test
  test:: test

"""
        output = r"""
<dl>
<dt>test</dt>
<dd><p>test </p>
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess13(self):
        test = r"""
 * test
  * test
 * test

"""
        output = r"""
<ul>
<li><p>test </p>
<ul>
<li><p>test </p>
</li>
</ul>
</li>
<li><p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess14(self):
        test = r"""
 1. test
  1. test
 1. test

"""
        output = r"""
<ol type="1">
<li><p>test </p>
<ol type="1">
<li><p>test </p>
</li>
</ol>
</li>
<li><p>test </p>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess15(self):
        test = r"""
 test:: test
  test:: test
 test:: test

"""
        output = r"""
<dl>
<dt>test</dt>
<dd><p>test </p>
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
</dd>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess16(self):
        py.test.skip('broken test')
        test = r"""
 * test

 1. test

"""
        output = r"""
<ul>
<li><p>test </p>
</li>
</ul>
<ol type="1">
<li><p>test </p>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess17(self):
        py.test.skip('broken test')
        test = r"""
 * test

 test:: test

"""
        output = r"""
<ul>
<li><p>test </p>
</li>
</ul>
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess18(self):
        py.test.skip('broken test')
        test = r"""
 1. test

 * test

"""
        output = r"""
<ol type="1">
<li><p>test </p>
</li>
</ol>
<ul>
<li><p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess19(self):
        py.test.skip('broken test')
        test = r"""
 1. test

 test:: test

"""
        output = r"""
<ol type="1">
<li><p>test </p>
</li>
</ol>
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess20(self):
        py.test.skip('broken test')
        test = r"""
 test:: test

 * test

"""
        output = r"""
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
<ul>
<li><p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess21(self):
        py.test.skip('broken test')
        test = r"""
 test:: test

 1. test

"""
        output = r"""
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
<ol type="1">
<li><p>test </p>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess23(self):
        py.test.skip('broken test')
        test = r"""
 1. test
  * test

"""
        output = r"""
<ol type="1">
<li><p>test </p>
<ul>
<li><p>test </p>
</li>
</ul>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess26(self):
        py.test.skip('broken test')
        test = r"""
 * test

test

"""
        output = r"""
<ul>
<li><p>test </p>
</li>
</ul>
<p>test </p>
"""
        self.do(test, output)

    def testListSuccess28(self):
        py.test.skip('broken test')
        test = r"""
 * test

 test

"""
        output = r"""
<ul>
<li><p>test </p>
<p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess29(self):
        py.test.skip('broken test')
        test = r"""
 * test
  * test
 test
"""
        output = r"""
"""
        self.do(test, output)

    def testListSuccess30(self):
        py.test.skip('broken test')
        test = r"""
 * test
  * test
  test
"""
        output = r"""
"""
        self.do(test, output)

    def testParagraph1(self):
        py.test.skip('broken test')
        test = r"""
test

"""
        output = r"""
<p>test </p>
"""
        self.do(test, output)

    def testParagraph2(self):
        py.test.skip('broken test')
        test = r"""
test

test

"""
        output = r"""
<p>test </p>
<p>test </p>
"""
        self.do(test, output)

    def testPreSuccess1(self):
        py.test.skip('broken test')
        test = r"""
{{{
test
}}}

"""
        output = r"""
<pre>
test
</pre>
"""
        self.do(test, output)

    def testPreSuccess2(self):
        py.test.skip('broken test')
        test = r"""
{{{
test
test
}}}

"""
        output = r"""
<pre>
test
test
</pre>
"""
        self.do(test, output)

    def testPreSuccess3(self):
        py.test.skip('broken test')
        test = r"""
{{{
test

test
}}}

"""
        output = r"""
<pre>
test

test
</pre>
"""
        self.do(test, output)

    def testPreSuccess4(self):
        py.test.skip('broken test')
        test = r"""
{{{
 * test
}}}

"""
        output = r"""
<pre>
 * test
</pre>
"""
        self.do(test, output)

    def testPreSuccess5(self):
        py.test.skip('broken test')
        test = r"""
{{{
  }}}

"""
        output = r"""
<pre>
  </pre>
"""
        self.do(test, output)

    def testPreSuccess6(self):
        test = r"""
 * {{{
test
}}}

"""
        output = r"""
<ul>
<li>
<pre>
test
</pre>
</li>
</ul>
"""
        self.do(test, output)

    def testPreSuccess7(self):
        py.test.skip("Broken.")
        test = r"""
 * {{{
   test
   }}}

"""
        output = r"""
<ul>
<li>
<pre>
   test
   </pre>
</li>
</ul>
"""
        self.do(test, output)

    def testPreSuccess8(self):
        test = r"""
 * test
 {{{
test
}}}

"""
        output = r"""
<ul>
<li><p>test
</p>
<pre>
test
</pre>
</li>
</ul>
"""
        self.do(test, output)

    def testPreSuccess9(self):
        py.test.skip('broken test')
        test = r"""
 * test

{{{
test
}}}

"""
        output = r"""
<ul>
<li><p>test </p>
</li>
</ul>

<pre>
test
</pre>
"""
        self.do(test, output)

    def testPreSuccess10(self):
        test = r"""
 * {{{{
{{{
test
}}}
}}}}

"""
        output = r"""
<ul>
<li>
<pre>
{{{
test
}}}
</pre>
</li>
</ul>
"""

    def testPreSuccess11(self):
        test = r"""
 * {{{{
test
}}}
}}}}

"""
        output = r"""
<ul>
<li>
<pre>
test
}}}
</pre>
</li>
</ul>
"""

    def testPreSuccess12(self):
        test = r"""
 * {{{{
{{{
test
}}}}

"""
        output = r"""
<ul>
<li>
<pre>
{{{
test
</pre>
</li>
</ul>
"""

        self.do(test, output)

    def testRule1(self):
        py.test.skip('broken test')
        test = r"""
----

"""
        output = r"""
<hr/>
"""
        self.do(test, output)

    def testTable01(self):
        py.test.skip('broken test')
        test = r"""
|| ||

"""
        output = r"""
<div>
<table>
<tr>
<td>
<p> </p>
</td>
</tr>
</table>
</div>
"""
        self.do(test, output)

    def testTable02(self):
        py.test.skip('broken test')
        test = r"""
||test||

"""
        output = r"""
<div>
<table>
<tr>
<td>
<p>test</p>
</td>
</tr>
</table>
</div>
"""
        self.do(test, output)

    def testTable03(self):
        py.test.skip('broken test')
        test = r"""
||test||test||

"""
        output = r"""
<table>
<tr>
<td>
<p class="line862">
test
</td>
<td>
<p class="line862">test
</td>
</tr>
</table>
"""
        self.do(test, output)

    def testTable04(self):
        py.test.skip('broken test')
        test = r"""
||test||
||test||test||

"""
        output = r"""
<div>
<table>
<tr>
<td>
<p>test</p>
</td>
</tr>
<tr>
<td>
<p>test</p>
</td>
<td>
<p>test</p>
</td>
</tr>
</table>
</div>
"""
        self.do(test, output)

    def testTable05(self):
        py.test.skip('broken test')
        test = r"""
||||test||
||test||test||

"""
        output = r"""
<div>
<table>
<tr>
<td colspan="2" style="text-align: center;">
<p>test</p>
</td>
</tr>
<tr>
<td>
<p>test</p>
</td>
<td>
<p>test</p>
</td>
</tr>
</table>
</div>
"""
        self.do(test, output)

    def testTable06(self):
        py.test.skip('broken test')
        test = r"""
||||test||test||
||test||||test||

"""
        output = r"""
<table><tbody><tr>  <td style="text-align: center;"
colspan="2"><p class="line862">test</p></td>   <td><p class="line862">test</p></td>
</tr> <tr>  <td><p class="line862">test</p></td>   <td style="text-align: center;"
colspan="2"><p class="line862">test</p></td> </tr> </tbody></table>"""
        self.do(test, output)

class TestConvertInlineFormatRepeatable(TestBase):
    def do(self, text, output):
        text = text.lstrip('\n')
        output = output.strip('\n')
        output = "<p>%s </p>" % output
        request = MinimalRequest(self.request)
        page = MinimalPage()
        formatter = Formatter(request)
        formatter.setPage(page)
        Parser(text, request).format(formatter)
        repeat = ''.join(request.result).strip('\n')
        #assert repeat == output
        out = self.do_convert_real([request, page.page_name, repeat])
        out = out.rstrip('\n')
        assert text == out

    def testEmphasis01(self):
        py.test.skip('broken test')
        test = r"''test''"
        output = r"<em>test</em>"
        self.do(test, output)

    def testEmphasis02(self):
        py.test.skip('broken test')
        test = r"'''test'''"
        output = r"<strong>test</strong>"
        self.do(test, output)

    def testEmphasis03(self):
        py.test.skip('broken test')
        test = r"'''''test'''''"
        output = r"<em><strong>test</strong></em>"
        self.do(test, output)

    def testEmphasis04(self):
        py.test.skip('broken test')
        test = r"''test'''test'''''"
        output = r"<em>test<strong>test</strong></em>"
        self.do(test, output)

    def testEmphasis05(self):
        py.test.skip('broken test')
        test = r"'''test''test'''''"
        output = r"<strong>test<em>test</em></strong>"
        self.do(test, output)

    def testEmphasis06(self):
        py.test.skip('broken test')
        test = r"''test'''test'''test''"
        output = r"<em>test<strong>test</strong>test</em>"
        self.do(test, output)

    def testEmphasis07(self):
        py.test.skip('broken test')
        test = r"'''test''test''test'''"
        output = r"<strong>test<em>test</em>test</strong>"
        self.do(test, output)

    def testEmphasis08(self):
        py.test.skip('broken test')
        test = r"''test'''''test'''"
        output = r"<em>test</em><strong>test</strong>"
        self.do(test, output)

    def testEmphasis09(self):
        py.test.skip('broken test')
        test = r"'''test'''''test''"
        output = r"<strong>test</strong><em>test</em>"
        self.do(test, output)

    def testEmphasis10(self):
        py.test.skip('broken test')
        test = r"'''''test''test'''"
        output = r"<strong><em>test</em>test</strong>"
        self.do(test, output)

    def testEmphasis11(self):
        py.test.skip('broken test')
        test = r"'''''test'''test''"
        output = r"<em><strong>test</strong>test</em>"
        self.do(test, output)

    def testFormatBig01(self):
        py.test.skip('broken test')
        test = r"~+test+~"
        output = r"<big>test</big>"
        self.do(test, output)

    def testFormatSmall01(self):
        py.test.skip('broken test')
        test = r"~-test-~"
        output = r"<small>test</small>"
        self.do(test, output)

    def testFormatStrike01(self):
        py.test.skip('broken test')
        test = r"--(test)--"
        output = r"<strike>test</strike>"
        self.do(test, output)

    def testFormatSub01(self):
        py.test.skip('broken test')
        test = r",,test,,"
        output = r"<sub>test</sub>"
        self.do(test, output)

    def testFormatSup01(self):
        py.test.skip('broken test')
        test = r"^test^"
        output = r"<sup>test</sup>"
        self.do(test, output)

    def testFormatUnderline01(self):
        py.test.skip('broken test')
        test = r"__test__"
        output = r"<u>test</u>"
        self.do(test, output)

    def testPre01(self):
        py.test.skip('broken test')
        test = r"{{{test}}}"
        output = r"<tt>test</tt>"
        self.do(test, output)

    def testWhitespace01(self):
        py.test.skip('broken test')
        test = r"''test '''test'''''"
        output = r"<em>test <strong>test</strong></em>"
        self.do(test, output)

class TestConvertInlineItemRepeatable(TestBase):
    def do(self, text, output):
        text = text.lstrip('\n')
        output = output.strip('\n')
        output = "<p>%s </p>" % output
        request = MinimalRequest(self.request)
        page = MinimalPage()
        formatter = Formatter(request)
        formatter.setPage(page)
        Parser(text, request).format(formatter)
        repeat = ''.join(request.result).strip('\n')
        #assert repeat == output
        out = self.do_convert_real([request, page.page_name, repeat])
        out = out.rstrip('\n')
        assert text == out

    def testWikiWord01(self):
        py.test.skip('broken test')
        test = r"WikiWord"
        output = r"""<a class="nonexistent" href="./WikiWord">WikiWord</a>"""
        self.do(test, output)

    def testNoWikiWord01(self):
        py.test.skip('broken test')
        test = r"!WikiWord"
        output = r"WikiWord"
        self.do(test, output)

    def testSmiley01(self):
        py.test.skip('broken test')
        test = r":-)"
        output = r"""<img src="/wiki/modern/img/smile.png" alt=":-)" height="15" width="15">"""
        self.do(test, output)

class TestStrip(object):
    def do(self, cls, text, output):
        tree = converter.parse(self.request, text)
        cls().do(tree)
        out = StringIO()
        try:
            import xml.dom.ext
        except ImportError:
            py.test.skip('xml.dom.ext module is not available')
        xml.dom.ext.Print(tree, out)
        assert "<?xml version='1.0' encoding='UTF-8'?>%s" % output == out.getvalue().decode("utf-8")

class TestStripWhitespace(TestStrip):
    def do(self, text, output):
        super(TestStripWhitespace, self).do(converter.strip_whitespace, text, output)

    def test1(self):
        test = r"""
<t/>
"""
        output = r"""<t/>"""
        self.do(test, output)

    def test2(self):
        py.test.skip('broken test')
        test = r"""
<t>
  <z/>
</t>
"""
        output = r"""<t><z/></t>"""
        self.do(test, output)

    def test3(self):
        py.test.skip('broken test')
        test = r"""
<t>
  <z>test</z>
</t>
"""
        output = r"""<t><z>test</z></t>"""
        self.do(test, output)

    def test4(self):
        test = r"""<p>&nbsp;</p>"""
        output = r""""""
        self.do(test, output)

    def test5(self):
        test = r"""<p>test </p>"""
        output = r"""<p>test</p>"""
        self.do(test, output)

class TestConvertBrokenBrowser(TestBase):
    def do(self, text, output):
        text = text.strip('\n')
        output = output.strip()
        request = MinimalRequest(self.request)
        page = MinimalPage()
        out = self.do_convert_real([request, page.page_name, text])
        out = out.strip()

        assert output == out

    def testList01(self):
        test = r"""
<ul>
<li>test</li>
<ul>
<li>test</li>
</ul>
<li>test</li>
</ul>
"""
        output = r"""
 * test
  * test
 * test

"""
        self.do(test, output)

class TestBlanksInTables(TestBase):
    def do(self, text, output):
        text = text.strip('\n')
        output = output.strip('\n')
        request = MinimalRequest(self.request)
        page = MinimalPage()
        out = self.do_convert_real([request, page.page_name, text])
        out = out.strip()
        assert output == out

    def testTable01(self):
        # tests empty cells
        test = "<table><tbody><tr><td>a</td><td></td></tr></tbody></table>"
        output = "||a|| ||"

        self.do(test, output)

    def testTable02(self):
        # tests empty cells by br (OOo cut and paste)
        test = "<table><tbody><tr><td>a</td><td><br /></td></tr></tbody></table>"
        output = "||a||<<BR>>||"

        self.do(test, output)

    def testTable03(self):
        # tests linebreak in cells by br
        test = "<table><tbody><tr><td>a<br />b</td></tr></tbody></table>"
        output = "||a<<BR>>b||"

        self.do(test, output)

    def testTable04(self):
        # tests linebreak in cells by br and formatting styles
        test = "<table><tbody><tr><td><em>a</em><br /><u>b</u><br /><strike>c</strike></td></tr></tbody></table>"
        output = "||''a''<<BR>>__b__<<BR>>--(c)--||"

        self.do(test, output)

    def testTable05(self):
        # tests empty cells and formatting style strong
        test = """
<table><tbody>
<tr><td><strong>a</strong></td><td></td></tr>
<tr><td></td><td><strong>b</strong></td></tr>
</tbody></table>
"""
        output = """
||'''a'''|| ||
|| ||'''b'''||
"""
        self.do(test, output)

    def testTable06(self):
        # tests linebreak in cells by br
        test = "<table><tbody><tr><td>a<br /></td></tr></tbody></table>"
        output = "||a<<BR>>||"

        self.do(test, output)

    def testTable07(self):
        # tests empty cells from OOo and formatting style strong
        test = """
<table><tbody>
<tr><td><strong>a</strong></td><td><strong><br /></strong></td></tr>
<tr><td><strong><br /></strong></td><td><strong>b</strong></td></tr>
</tbody></table>
"""

        output = """
||'''a'''||''''''||
||''''''||'''b'''||
"""

        self.do(test, output)

    def testTable08(self):
        # tests line break between two lines in formatted text
        test = "<table><tbody><tr><td><strong>first line<br />second line</strong></td></tr></tbody></table>"
        output = "||'''first line<<BR>>second line'''||"

        self.do(test, output)

    def testTable09(self):
        # tests line break at beginning of line and formatted text
        test = "<table><tbody><tr><td><strong><br />line</strong></td></tr></tbody></table>"
        output = "||'''<<BR>>line'''||"

    def testTable10(self):
        # tests line break at end of line and formatted text
        test = "<table><tbody><tr><td><strong>line<br /></strong></td></tr></tbody></table>"
        output = "||'''line<<BR>>'''||"

    def testTable11(self):
        # tests line break at beginning before formatted text
        test = "<table><tbody><tr><td><br /><strong>line</strong></td></tr></tbody></table>"
        output = "||'<<BR>'''line'''||"

    def testTable12(self):
        # tests line break after formatted text
        test = "<table><tbody><tr><td><strong>line</strong><br /></td></tr></tbody></table>"
        output = "||'''line'''<<BR>>||"

    def testTable13(self):
        # tests formatted br
        test = "<table><tbody><tr><td><strong><br /></strong></td></tr></tbody></table>"
        output = "||''''''||"

    def testTable14(self):
        # tests br
        test = "<table><tbody><tr><td><br /></td></tr></tbody></table>"
        output = "||<<BR>>||"

    def testTable15(self):
        # tests many br
        test = "<table><tbody><tr><td><br /><br /><br /></td></tr></tbody></table>"
        output = "||<<BR>><<BR>><<BR>>||"

        self.do(test, output)

coverage_modules = ['MoinMoin.converter.text_html_text_moin_wiki']

