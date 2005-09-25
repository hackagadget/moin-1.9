# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Action Handlers

    Actions are triggered by the user clicking on special links on the page
    (like the icons in the title, or the "EditText" link at the bottom). The
    name of the action is passed in the "action" CGI parameter.

    The sub-package "MoinMoin.action" contains external actions, you can
    place your own extensions there (similar to extension macros). User
    actions that start with a capital letter will be displayed in a list
    at the bottom of each page.

    User actions starting with a lowercase letter can be used to work
    together with a user macro; those actions a likely to work only if
    invoked BY that macro, and are thus hidden from the user interface.

    @copyright: 2000-2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os, re, time, urllib
from MoinMoin import config, util, wikiutil
from MoinMoin.Page import Page
from MoinMoin.util import MoinMoinNoFooter, pysupport
from MoinMoin.logfile import editlog

#############################################################################
### Misc Actions
#############################################################################

def do_diff(pagename, request):
    """ Handle "action=diff"
        checking for either a "rev=formerrevision" parameter
        or rev1 and rev2 parameters
    """
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page(request)
        return

    try:
        date = request.form['date'][0]
        try:
            date = long(date) # must be long for py 2.2.x
        except StandardError:
            date = 0
    except KeyError:
        date = 0

    try:
        rev1 = request.form['rev1'][0]
        try:
            rev1 = int(rev1)
        except StandardError:
            rev1 = 0
    except KeyError:
        rev1 = -1

    try:
        rev2 = request.form['rev2'][0]
        try:
            rev2 = int(rev2)
        except StandardError:
            rev2 = 0
    except KeyError:
        rev2 = 0

    if rev1 == -1 and rev2 == 0:
        try:
            rev1 = request.form['rev'][0]
            try:
                rev1 = int(rev1)
            except StandardError:
                rev1 = -1
        except KeyError:
            rev1 = -1
 
    # spacing flag?
    try:
        ignorews = int(request.form['ignorews'][0])
    except (KeyError, ValueError, TypeError):
        ignorews = 0

    _ = request.getText
    
    # get a list of old revisions, and back out if none are available
    currentpage = Page(request, pagename)
    revisions = currentpage.getRevList()
    if len(revisions) < 2:
        currentpage.send_page(request, msg=_("No older revisions available!"))
        return

    if date: # this is how we get called from RecentChanges
        rev1 = 0
        log = editlog.EditLog(request, rootpagename=pagename)
        for line in log.reverse():
            if date >= line.ed_time_usecs and int(line.rev) != 99999999:
                rev1 = int(line.rev)
                break
        else:
            rev1 = 1
        rev2 = 0

    # Start output
    # This action generate content in the user language
    request.setContentLanguage(request.lang)

    request.http_headers()
    wikiutil.send_title(request, _('Diff for "%s"') % (pagename,), pagename=pagename, allow_doubleclick=1)
  
    if (rev1>0 and rev2>0 and rev1>rev2) or (rev1==0 and rev2>0):
        rev1,rev2 = rev2,rev1
          
    oldrev1,oldcount1 = None,0
    oldrev2,oldcount2 = None,0
    # get the filename of the version to compare to
    edit_count = 0
    for rev in revisions:
        edit_count += 1
        if rev <= rev1: 
            oldrev1,oldcount1 = rev,edit_count
        if rev2 and rev >= rev2: 
            oldrev2,oldcount2 = rev,edit_count
        if (oldrev1 and oldrev2) or (oldrev1 and not rev2):
            break
    
    if rev1 == -1:
        oldpage = Page(request, pagename, rev=revisions[1])
        oldcount1 = oldcount1 - 1
    elif rev1 == 0:
        oldpage = currentpage
        # oldcount1 is still on init value 0
    else:
        if oldrev1:
            oldpage = Page(request, pagename, rev=oldrev1)
        else:
            oldpage = Page(request, "$EmptyPage$") # hack
            oldpage.set_raw_body("")    # avoid loading from disk
            oldrev1 = 0 # XXX
              
    if rev2 == 0:
        newpage = currentpage
        # oldcount2 is still on init value 0
    else:
        if oldrev2:
            newpage = Page(request, pagename, rev=oldrev2)
        else:
            newpage = Page(request, "$EmptyPage$") # hack
            newpage.set_raw_body("")    # avoid loading from disk
            oldrev2 = 0 # XXX
    
    edit_count = abs(oldcount1 - oldcount2)

    # this should use the formatter, but there is none?
    request.write('<div id="content">\n') # start content div
    request.write('<p class="diff-header">')
    request.write(_('Differences between revisions %d and %d') % (oldpage.get_real_rev(), newpage.get_real_rev()))
    if edit_count > 1:
        request.write(' ' + _('(spanning %d versions)') % (edit_count,))
    request.write('</p>')
  
    if request.user.show_fancy_diff:
        from MoinMoin.util.diff import diff
        request.write(diff(request, oldpage.get_raw_body(), newpage.get_raw_body()))
        newpage.send_page(request, count_hit=0, content_only=1, content_id="content-below-diff")
    else:
        lines = wikiutil.linediff(oldpage.getlines(), newpage.getlines())
        if not lines:
            msg = _("No differences found!")
            if edit_count > 1:
                msg = msg + '<p>' + _('The page was saved %(count)d times, though!') % {
                    'count': edit_count}
            request.write(msg)
        else:
            if ignorews:
                request.write(_('(ignoring whitespace)') + '<br>')
            else:
                qstr = 'action=diff&ignorews=1'
                if rev1: qstr = '%s&rev1=%s' % (qstr, rev1)
                if rev2: qstr = '%s&rev2=%s' % (qstr, rev2)
                request.write(Page(request, pagename).link_to(request,
                    text=_('Ignore changes in the amount of whitespace'),
                    querystr=qstr) + '<p>')

            request.write('<pre>')
            for line in lines:
                if line[0] == "@":
                    request.write('<hr>')
                request.write(wikiutil.escape(line)+'\n')
            request.write('</pre>')

    request.write('</div>\n') # end content div
    wikiutil.send_footer(request, pagename, showpage=1)


def do_info(pagename, request):
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page(request)
        return

    def general(page, pagename, request):
        _ = request.getText

        request.write('<h2>%s</h2>\n' % _('General Information'))
        
        # show page size
        request.write(("<p>%s</p>" % _("Page size: %d")) % page.size())

        # show SHA digest fingerprint
        import sha
        digest = sha.new(page.get_raw_body().encode(config.charset)).hexdigest().upper()
        request.write('<p>%(label)s <tt>%(value)s</tt></p>' % {
            'label': _("SHA digest of this page's content is:"),
            'value': digest,
            })

        # show attachments (if allowed)
        attachment_info = getHandler(request, 'AttachFile', 'info')
        if attachment_info:
            request.write(attachment_info(pagename, request))

        # show subscribers
        subscribers = page.getSubscribers(request,  include_self=1, return_users=1)
        if subscribers:
            request.write('<p>', _('The following users subscribed to this page:'))
            for lang in subscribers.keys():
                request.write('<br>[%s] ' % lang)
                for user in subscribers[lang]:
                    # do NOT disclose email addr, only WikiName
                    userhomepage = Page(request, user.name)
                    if userhomepage.exists():
                        request.write(userhomepage.link_to(request) + ' ')
                    else:
                        request.write(user.name + ' ')
            request.write('</p>')

        # show links
        links = page.getPageLinks(request)
        if links:
            request.write('<p>', _('This page links to the following pages:'), '<br>')
            for linkedpage in links:
                request.write("%s%s " % (Page(request, linkedpage).link_to(request), ",."[linkedpage == links[-1]]))
            request.write("</p>")


    def history(page, pagename, request):
        # show history as default
        _ = request.getText

        # open log for this page
        from MoinMoin.logfile import editlog
        from MoinMoin.util.dataset import TupleDataset, Column

        history = TupleDataset()
        history.columns = [
            Column('rev', label='#', align='right'),
            Column('mtime', label=_('Date'), align='right'),
            Column('size',  label=_('Size'), align='right'),
            Column('diff', label='<input type="submit" value="%s">' % (_("Diff"))),
            Column('editor', label=_('Editor'), hidden=not request.cfg.show_hosts),
            Column('comment', label=_('Comment')),
            Column('action', label=_('Action')),
            ]

        # generate history list
        revisions = page.getRevList()
        versions = len(revisions)

        may_revert = request.user.may.revert(pagename)
        
        # read in the complete log of this page
        log = editlog.EditLog(request, rootpagename=pagename)
        count = 0
        for line in log.reverse():
            rev = int(line.rev)
            actions = ""
            if line.action in ['SAVE','SAVENEW','SAVE/REVERT',]:
                if count == 0: # latest page
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('view'),
                        querystr=''))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('raw'),
                        querystr='action=raw'))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('print'),
                        querystr='action=print'))
                else:
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('view'),
                        querystr='action=recall&rev=%d' % rev))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('raw'),
                        querystr='action=raw&rev=%d' % rev))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('print'),
                        querystr='action=print&rev=%d' % rev))
                    if may_revert:
                        actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                            text=_('revert'),
                            querystr='action=revert&rev=%d' % (rev,)))
                if count == 0:
                    rchecked=' checked="checked"'
                    lchecked = ''
                elif count == 1:
                    lchecked=' checked="checked"'
                    rchecked = ''
                else:
                    lchecked = rchecked = ''
                diff = '<input type="radio" name="rev1" value="%d"%s><input type="radio" name="rev2" value="%d"%s>' % (rev,lchecked,rev,rchecked)
      
                comment = line.comment
                if not comment and line.action.find('/REVERT') != -1:
                        comment = _("Revert to revision %(rev)d.") % {'rev': int(line.extra)}
                size = page.size(rev=rev)
            else: # ATT*
                rev = '-'
                diff = '-'
                
                # TODO: refactor this into the log in 1.5
                # line.extra is urlencoded then converted to unicode.
                # urllib.unquote require ascii - unquote(u'%xx') == u'%xx'
                filename = line.extra.encode('ascii', 'replace')
                filename = unicode(urllib.unquote(filename), config.charset,
                                   'replace')

                comment = "%s: %s %s" % (line.action, filename, line.comment)
                size = 0
                if line.action != 'ATTDEL':
                    from MoinMoin.action import AttachFile
                    page_dir = AttachFile.getAttachDir(request, pagename)
                    filepath = os.path.join(page_dir, filename)
                    try:
                        # FIXME, wrong path on non-std names
                        size = os.path.getsize(filepath)
                    except:
                        pass
                    if line.action == 'ATTNEW':
                        actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                            text=_('view'),
                            querystr='action=AttachFile&do=view&target=%s' % filename))
                    elif line.action == 'ATTDRW':
                        actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                            text=_('edit'),
                            querystr='action=AttachFile&drawing=%s' % filename.replace(".draw","")))

                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('get'),
                        querystr='action=AttachFile&do=get&target=%s' % filename))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('del'),
                        querystr='action=AttachFile&do=del&target=%s' % filename))
                    # XXX use?: wikiutil.escape(filename)

            history.addRow((
                rev,
                request.user.getFormattedDateTime(wikiutil.version2timestamp(line.ed_time_usecs)),
                str(size),
                diff,
                line.getEditor(request) or _("N/A"),
                wikiutil.escape(comment) or '&nbsp;',
                actions,
            ))
            count += 1
            if count >= 100:
                break

        # print version history
        from MoinMoin.widget.browser import DataBrowserWidget

        request.write('<h2>%s</h2>\n' % _('Revision History'))

        if not count: # there was no entry in logfile
            request.write(_('No log entries found.'))
            return

        # TODO: this form activates revert, which should use POST, but
        # other actions should use get. Maybe we should put the revert
        # into the page view itself, and not in this form.
        request.write('<form method="GET" action="">\n')
        request.write('<div id="page-history">\n')
        request.write('<input type="hidden" name="action" value="diff">\n')

        history_table = DataBrowserWidget(request)
        history_table.setData(history)
        history_table.render()
        request.write('</div>\n')
        request.write('</form>\n')


    _ = request.getText
    page = Page(request, pagename)
    qpagename = wikiutil.quoteWikinameURL(pagename)
    title = page.split_title(request)

    request.http_headers()

    # This action uses page or wiki language TODO: currently
    # page.language is broken and not available now, when we fix it,
    # this will be automatically fixed.
    lang = page.language or request.cfg.default_lang
    request.setContentLanguage(lang)
    
    wikiutil.send_title(request, _('Info for "%s"') % (title,), pagename=pagename)

    historylink =  wikiutil.link_tag(request, '%s?action=info' % qpagename,
        _('Show "%(title)s"') % {'title': _('Revision History')})
    generallink =  wikiutil.link_tag(request, '%s?action=info&amp;general=1' % qpagename,
        _('Show "%(title)s"') % {'title': _('General Page Infos')})
    hitcountlink = wikiutil.link_tag(request, '%s?action=info&amp;hitcounts=1' % qpagename,
        _('Show chart "%(title)s"') % {'title': _('Page hits and edits')})
    
    request.write('<div id="content">\n') # start content div
    request.write("<p>[%s]  [%s]  [%s]</p>" % (historylink, generallink, hitcountlink))

    show_hitcounts = int(request.form.get('hitcounts', [0])[0]) != 0
    show_general = int(request.form.get('general', [0])[0]) != 0
    
    if show_hitcounts:
        from MoinMoin.stats import hitcounts
        request.write(hitcounts.linkto(pagename, request, 'page=' + urllib.quote_plus(pagename.encode(config.charset))))
    elif show_general:
        general(page, pagename, request)
    else:
        history(page, pagename, request)
        
    request.write('</div>\n') # end content div
    wikiutil.send_footer(request, pagename, showpage=1)


def do_recall(pagename, request):
    # We must check if the current page has different ACLs.
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page(request)
        return
    if request.form.has_key('rev'):
        try:
            rev = request.form['rev'][0]
            try:
                rev = int(rev)
            except StandardError:
                rev = 0
        except KeyError:
            rev = 0
        Page(request, pagename, rev=rev).send_page(request)
    else:
        Page(request, pagename).send_page(request)


def do_show(pagename, request):
    # We must check if the current page has different ACLs.
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page(request)
        return
    if request.form.has_key('rev'):
        try:
            rev = request.form['rev'][0]
            try:
                rev = int(rev)
            except StandardError:
                rev = 0
        except KeyError:
            rev = 0
        Page(request, pagename, rev=rev).send_page(request, count_hit=1)
    else:
        request.cacheable = 1
        Page(request, pagename).send_page(request, count_hit=1)


def do_refresh(pagename, request):
    """ Handle refresh action """
    # Without arguments, refresh action will refresh the page text_html
    # cache.
    arena = request.form.get('arena', ['Page.py'])[0]
    if arena == 'Page.py':
        arena = Page(request, pagename)
    key = request.form.get('key', ['text_html'])[0]

    # Remove cache entry (if exists), and send the page
    from MoinMoin import caching
    caching.CacheEntry(request, arena, key).remove()
    caching.CacheEntry(request, arena, "pagelinks").remove()
    do_show(pagename, request)


def do_print(pagename, request):
    do_show(pagename, request)


def do_content(pagename, request):
    request.http_headers()
    page = Page(request, pagename)
    request.write('<!-- Transclusion of %s -->' % request.getQualifiedURL(page.url(request)))
    page.send_page(request, count_hit=0, content_only=1)
    raise MoinMoinNoFooter


def do_revert(pagename, request):
    from MoinMoin.PageEditor import PageEditor
    _ = request.getText

    if not request.user.may.revert(pagename):
        return Page(request, pagename).send_page(request,
            msg = _('You are not allowed to revert this page!'))

    rev = int(request.form['rev'][0])
    revstr = '%08d' % rev
    oldpg = Page(request, pagename, rev=rev)
    pg = PageEditor(request, pagename)

    try:
        savemsg = pg.saveText(oldpg.get_raw_body(), 0, extra=revstr,
                              action="SAVE/REVERT")
    except pg.SaveError, msg:
        # msg contain a unicode string
        savemsg = unicode(msg)
    request.reset()
    pg.send_page(request, msg=savemsg)
    return None

def do_edit(pagename, request):
    _ = request.getText

    if not request.user.may.write(pagename):
        Page(request, pagename).send_page(request,
            msg = _('You are not allowed to edit this page.'))
        return

    valideditors = ['text', 'gui',]
    editor = ''
    if request.user.valid:
        editor = request.user.editor_default
    if editor not in valideditors:
        editor = request.cfg.editor_default
    
    editor = lasteditor = request.form.get('editor', [editor])[0]

    if request.cfg.editor_force:
        editor = request.cfg.editor_default

    # if it is still nothing valid, we just use the text editor
    if editor not in valideditors:
        editor = 'text'
            
    savetext = request.form.get('savetext', [None])[0]
    rev = int(request.form.get('rev', ['0'])[0])
    comment = request.form.get('comment', [u''])[0]
    category = request.form.get('category', [None])[0]
    rstrip = int(request.form.get('rstrip', ['0'])[0])
    trivial = int(request.form.get('trivial', ['0'])[0])

    if request.form.has_key('button_switch'):
        if editor == 'text':
            editor = 'gui'
        else: # 'gui'
            editor = 'text'

    # load right editor class
    if editor == 'gui':
        from MoinMoin.PageGraphicalEditor import PageGraphicalEditor
        pg = PageGraphicalEditor(request, pagename)
    else: # 'text'
        from MoinMoin.PageEditor import PageEditor
        pg = PageEditor(request, pagename)

    # Edit was canceled
    if request.form.has_key('button_cancel'):
        pg.sendCancel(savetext, rev)
        return

    # is invoked without savetext start editing
    if savetext is None:
        pg.sendEditor()
        return

    # convert input from Graphical editor
    if lasteditor == 'gui':
        from MoinMoin.converter.text_html_text_x_moin import convert
        savetext = convert(request, pagename, savetext) # XXX error handling

    # IMPORTANT: normalize text from the form. This should be done in
    # one place before we manipulate the text.
    savetext = pg.normalizeText(savetext, stripspaces=rstrip)

    # Add category

    # TODO: this code does not work with extended links, and is doing
    # things behind your back, and in general not needed. Either we have
    # a full interface for categories (add, delete) or just add them by
    # markup.
    
    if category:
        # strip trailing whitespace
        savetext = savetext.rstrip()

        # Add category separator if last non-empty line contains
        # non-categories.
        lines = filter(None, savetext.splitlines())
        if lines:
            
            #TODO: this code is broken, will not work for extended links
            #categories, e.g ["category hebrew"]
            categories = lines[-1].split()
            
            if categories:
                confirmed = wikiutil.filterCategoryPages(request, categories)
                if len(confirmed) < len(categories):
                    # This was not a categories line, add separator
                    savetext += u'\n----\n'

        # Add new category
        if savetext and savetext[-1] != u'\n':
            savetext += ' '
        savetext += category + u'\n' # Should end with newline!

    # Clean comment - replace CR, LF, TAB by whitespace, delete control chars
    # TODO: move this to config, create on first call then return cached.
    remap_chars = {
        ord(u'\t'): u' ',
        ord(u'\r'): u' ',
        ord(u'\n'): u' ',
    }
    control_chars = u'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f' \
                    '\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
    for c in control_chars:
        remap_chars[c] = None
    comment = comment.translate(remap_chars)

    # Preview, spellcheck or spellcheck add new words
    if (request.form.has_key('button_preview') or
        request.form.has_key('button_spellcheck') or
        request.form.has_key('button_newwords')):
        pg.sendEditor(preview=savetext, comment=comment)
    
    # Preview with mode switch
    elif request.form.has_key('button_switch'):
        pg.sendEditor(preview=savetext, comment=comment, staytop=1)
    
    # Save new text
    else:
        try:
            savemsg = pg.saveText(savetext, rev, trivial=trivial, comment=comment)
        except pg.EditConflict, msg:
            # Handle conflict and send editor

            # TODO: conflict messages are duplicated from PageEditor,
            # refactor to one place only.
            conflict_msg = _('Someone else changed this page while you were editing!')
            pg.set_raw_body(savetext, modified=1)
            if pg.mergeEditConflict(rev):
                conflict_msg = _("""Someone else saved this page while you were editing!
Please review the page and save then. Do not save this page as it is!
Have a look at the diff of %(difflink)s to see what has been changed.""") % {
                    'difflink': pg.link_to(pg.request,
                                           querystr='action=diff&rev=%d' % rev)
                    }
                # We don't send preview when we do merge conflict
                pg.sendEditor(msg=conflict_msg, comment=comment)
                return
            else:
                savemsg = conflict_msg
        
        except pg.SaveError, msg:
            # msg contain a unicode string
            savemsg = unicode(msg)

        # Send new page after save or after unsuccessful conflict merge.
        request.reset()
        backto = request.form.get('backto', [None])[0]
        if backto:
            pg = Page(request, backto)

        pg.send_page(request, msg=savemsg)
        

def do_quicklink(pagename, request):
    """ Add the current wiki page to the quicklinks property in
        current user profile.
    """
    _ = request.getText
    cfg = request.cfg
    msg = ''

    # check whether the user has a profile
    if not request.user.valid:
        msg = _('''You didn't create a user profile yet. '''
                '''Select UserPreferences in the upper right corner to create a profile.''')

    # check whether already quicklinked
    elif request.user.isQuickLinkedTo([pagename]):
        if request.user.quicklinkPage(pagename, remove=True):
            request.user.save()
            msg = _('Your quicklink to this page has been removed.')
            
    # quicklink to current page
    else:
        if request.user.quicklinkPage(pagename):
            request.user.save()
        msg = _('A quicklink to this page has been added for you.')

    Page(request, pagename).send_page(request, msg=msg)


def do_subscribe(pagename, request):
    """ Add the current wiki page to the subscribed_page property in
        current user profile.
    """
    _ = request.getText
    cfg = request.cfg

    if not request.user.may.read(pagename):
        msg = _("You are not allowed to subscribe to a page you can't read.")

    # check config
    elif not cfg.mail_enabled:
        msg = _('''This wiki is not enabled for mail processing. '''
                '''Contact the owner of the wiki, who can either enable email, or remove the "Subscribe" icon.''')

    # check whether the user has a profile
    elif not request.user.valid:
        msg = _('''You didn't create a user profile yet. '''
                '''Select UserPreferences in the upper right corner to create a profile.''')

    # check whether the user has an email address
    elif not request.user.email:
        msg = _('''You didn't enter an email address in your profile. '''
                '''Select your name (UserPreferences) in the upper right corner and enter a valid email address.''')

    # check whether already subscribed
    elif request.user.isSubscribedTo([pagename]):
        if request.user.subscribePage(pagename, remove=True):
            request.user.save()
            msg = _('Your subscribtion to this page has been removed.')
        else:
            msg = _("Can't remove regular expression subscription!") + u' ' + \
                  _('To unsubscribe, go to your profile and delete this page from the subscription list.')
            
    # subscribe to current page
    else:
        if request.user.subscribePage(pagename):
            request.user.save()
        msg = _('You have been subscribed to this page.') + u' ' + \
              _('To unsubscribe, go to your profile and delete this page from the subscription list.')

    Page(request, pagename).send_page(request, msg=msg)


def do_userform(pagename, request):
    from MoinMoin import userform
    savemsg = userform.savedata(request)
    Page(request, pagename).send_page(request, msg=savemsg)

def do_bookmark(pagename, request):
    if request.form.has_key('time'):
        if request.form['time'][0] == 'del':
            tm = None
        else:
            try:
                tm = long(request.form["time"][0]) # must be long for py 2.2.x
            except StandardError:
                tm = wikiutil.timestamp2version(time.time())
    else:
        tm = wikiutil.timestamp2version(time.time())
  
    if tm is None:
        request.user.delBookmark()
    else:
        request.user.setBookmark(tm)
    Page(request, pagename).send_page(request)
  

def do_formtest(pagename, request):
    # test a user defined form
    from MoinMoin import wikiform
    wikiform.do_formtest(pagename, request)


# def do_macro(pagename, request):
#     """ Execute a helper action within a macro.
#     """

#     from MoinMoin import wikimacro
#     from MoinMoin.formatter.text_html import Formatter
#     from MoinMoin.parser.wiki import Parser
#     from MoinMoin.Page import Page
#     macro_name = request.form["macro"][0]
#     args = request.form.get('args', [''])[0]
    
#     parser = Parser('', request)
#     parser.formatter = Formatter(request)
#     parser.formatter.page = Page(request, 'dummy')
#     request.http_headers()
#     request.write(wikimacro.Macro(parser).execute(macro_name, args))
#     request.finish()
    
#############################################################################
### Special Actions
#############################################################################

def do_raw(pagename, request):
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page(request)
        return

    request.http_headers(["Content-type: text/plain;charset=%s" % config.charset])

    if request.form.has_key('rev'):
        try:
            rev = request.form['rev'][0]
            try:
                rev = int(rev)
            except StandardError:
                rev = 0
        except KeyError:
            rev = 0
        page = Page(request, pagename, rev=rev)
    else:
        page = Page(request, pagename)

    text = page.get_raw_body()
    text = page.encodeTextMimeType(text)
    request.write(text)
    raise MoinMoinNoFooter


def do_format(pagename, request):
    # get the MIME type
    if request.form.has_key('mimetype'):
        mimetype = request.form['mimetype'][0]
    else:
        mimetype = u"text/plain"

    # try to load the formatter
    Formatter = wikiutil.importPlugin(request.cfg, "formatter",
        mimetype.translate({ord(u'/'): u'_', ord(u'.'): u'_'}), "Formatter")
    if Formatter is None:
        # default to plain text formatter
        del Formatter
        mimetype = "text/plain"
        from formatter.text_plain import Formatter

    if "xml" in mimetype:
        mimetype = "text/xml"
    request.http_headers(["Content-Type: %s; charset=%s" % (mimetype, config.charset)])

    Page(request, pagename, formatter=Formatter(request)).send_page(request)
    raise MoinMoinNoFooter


def do_chart(pagename, request):
    if request.user.may.read(pagename) and request.cfg.chart_options:
        chart_type = request.form['type'][0]
        func = pysupport.importName("MoinMoin.stats." + chart_type, "draw")
        func(pagename, request)
    raise MoinMoinNoFooter


def do_dumpform(pagename, request):
    data = util.dumpFormData(request.form)

    request.http_headers()
    request.write("<html><body>%s</body></html>" % data)
    raise MoinMoinNoFooter


def do_export(pagename, request):
    import shutil, StringIO
    from MoinMoin.wikixml import wikiexport

    # Protect this with ACLs, when ready!

    # get parameters
    compression = request.form.get('compression', None)

    # prepare output stream
    fileid = time.strftime("%Y-%m-%d", request.user.getTime(time.time()))
    filename = "wiki-export-%s.xml" % fileid 
    outbuff = StringIO.StringIO()
    mimetype, out = 'text/xml', outbuff
    if compression == "gzip":
        import gzip
        mimetype, out = 'application/x-gzip', gzip.GzipFile(
            filename, "wb", 9, outbuff)
        filename = filename + '.gz'

    # create export document
    export = wikiexport.WikiExport(out, public=1)
    export.run()

    # send http headers
    headers = [
        "Content-Type: %s" % mimetype,
        "Content-Length: %d" % len(outbuff.getvalue()),
    ]
    if mimetype != 'text/xml':
        headers.append("Content-Disposition: attachment; filename=%s" % filename)
    request.http_headers(headers)

    # copy the body
    outbuff.seek(0)
    shutil.copyfileobj(outbuff, request, 8192)
    raise MoinMoinNoFooter


def do_test(pagename, request):
    from MoinMoin.wikitest import runTest
    request.http_headers(["Content-type: text/plain;charset=%s" % config.charset])
    request.write('MoinMoin Diagnosis\n======================\n\n')
    runTest(request)
    raise MoinMoinNoFooter


#############################################################################
### Dispatching
#############################################################################

def getPlugins(request):
    dir = os.path.join(request.cfg.plugin_dir, 'action')
    plugins = []
    if os.path.isdir(dir):
        plugins = pysupport.getPackageModules(os.path.join(dir, 'dummy'))
    return dir, plugins


def getHandler(request, action, identifier="execute"):
    # check for excluded actions
    if action in request.cfg.actions_excluded:
        return None

    from MoinMoin.formatter.text_html import Formatter
    request.formatter = Formatter(request)

    handler = wikiutil.importPlugin(request.cfg, "action", action, identifier)
    if handler is None:
        handler = globals().get('do_' + action)
        
    return handler

    
 

