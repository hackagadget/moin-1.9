# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - jabber bot i18n routines

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""
import logging, xmlrpc.client
from jabberbot.config import BotConfig

TRANSLATIONS = None


def get_text(original, lang="en"):
    """ Return a translation of text in the user's language.

        @type original: unicode
    """
    if original == "":
        return ""

    global TRANSLATIONS
    if not TRANSLATIONS:
        init_i18n(BotConfig)

    try:
        return TRANSLATIONS[lang][original]
    except KeyError:
        return original


def init_i18n(config):
    """Prepare i18n

    @type config: jabberbot.config.BotConfig

    """
    global TRANSLATIONS
    TRANSLATIONS = request_translations(config) or {'en': {}}


def request_translations(config):
    """Download translations from wiki using xml rpc

    @type config: jabberbot.config.BotConfig

    """

    wiki = xmlrpc.client.Server(config.wiki_url + "?action=xmlrpc2")
    log = logging.getLogger(__name__)
    log.debug("Initialising i18n...")

    try:
        translations =  wiki.getBotTranslations()
        return translations
    except xmlrpc.client.Fault as fault:
        log.error("XML RPC fault occurred while getting translations: %s" % (str(fault), ))
    except xmlrpc.client.Error as error:
        log.error("XML RPC error occurred while getting translations: %s" % (str(error), ))
    except Exception as exc:
        log.error("Unexpected exception occurred while getting translations: %s" % (str(exc), ))

    log.error("Translations could not be downloaded, is wiki is accesible?")
    return None
