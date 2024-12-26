# -*- coding: utf-8 -*-
"""
parsedatetime/warns.py

All subclasses inherited from `Warning` class

"""


import warnings


class pdtDeprecationWarning(DeprecationWarning):
    pass


class pdtPendingDeprecationWarning(PendingDeprecationWarning):
    pass


class pdt20DeprecationWarning(pdtPendingDeprecationWarning):
    pass


warnings.simplefilter('default', pdtDeprecationWarning)
warnings.simplefilter('ignore', pdtPendingDeprecationWarning)
