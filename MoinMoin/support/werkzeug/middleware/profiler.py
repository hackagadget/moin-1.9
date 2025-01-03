"""
Application Profiler
====================

This module provides a middleware that profiles each request with the
:mod:`cProfile` module. This can help identify bottlenecks in your code
that may be slowing down your application.

.. autoclass:: ProfilerMiddleware

:copyright: 2007 Pallets
:license: BSD-3-Clause
"""


import os.path
import sys
import time
from pstats import Stats

try:
    from cProfile import Profile
except ImportError:
    from profile import Profile


class ProfilerMiddleware(object):
    """Wrap a WSGI application and profile the execution of each
    request. Responses are buffered so that timings are more exact.

    If ``stream`` is given, :class:`pstats.Stats` are written to it
    after each request. If ``profile_dir`` is given, :mod:`cProfile`
    data files are saved to that directory, one file per request.

    The filename can be customized by passing ``filename_format``. If
    it is a string, it will be formatted using :meth:`str.format` with
    the following fields available:

    -   ``{method}`` - The request method; GET, POST, etc.
    -   ``{path}`` - The request path or 'root' should one not exist.
    -   ``{elapsed}`` - The elapsed time of the request.
    -   ``{time}`` - The time of the request.

    If it is a callable, it will be called with the WSGI ``environ``
    dict and should return a filename.

    :param app: The WSGI application to wrap.
    :param stream: Write stats to this stream. Disable with ``None``.
    :param sort_by: A tuple of columns to sort stats by. See
        :meth:`pstats.Stats.sort_stats`.
    :param restrictions: A tuple of restrictions to filter stats by. See
        :meth:`pstats.Stats.print_stats`.
    :param profile_dir: Save profile data files to this directory.
    :param filename_format: Format string for profile data file names,
        or a callable returning a name. See explanation above.

    .. code-block:: python

        from werkzeug.middleware.profiler import ProfilerMiddleware
        app = ProfilerMiddleware(app)

    .. versionchanged:: 0.15
        Stats are written even if ``profile_dir`` is given, and can be
        disable by passing ``stream=None``.

    .. versionadded:: 0.15
        Added ``filename_format``.

    .. versionadded:: 0.9
        Added ``restrictions`` and ``profile_dir``.
    """

    def __init__(
        self,
        app,
        stream=sys.stdout,
        sort_by=("time", "calls"),
        restrictions=(),
        profile_dir=None,
        filename_format="{method}.{path}.{elapsed:.0f}ms.{time:.0f}.prof",
    ):
        self._app = app
        self._stream = stream
        self._sort_by = sort_by
        self._restrictions = restrictions
        self._profile_dir = profile_dir
        self._filename_format = filename_format

    def __call__(self, environ, start_response):
        response_body = []

        def catching_start_response(status, headers, exc_info=None):
            start_response(status, headers, exc_info)
            return response_body.append

        def runapp():
            app_iter = self._app(environ, catching_start_response)
            response_body.extend(app_iter)

            if hasattr(app_iter, "close"):
                app_iter.close()

        profile = Profile()
        start = time.time()
        profile.runcall(runapp)
        body = b"".join(response_body)
        elapsed = time.time() - start

        if self._profile_dir is not None:
            if callable(self._filename_format):
                filename = self._filename_format(environ)
            else:
                filename = self._filename_format.format(
                    method=environ["REQUEST_METHOD"],
                    path=(
                        environ.get("PATH_INFO").strip("/").replace("/", ".") or "root"
                    ),
                    elapsed=elapsed * 1000.0,
                    time=time.time(),
                )
            filename = os.path.join(self._profile_dir, filename)
            profile.dump_stats(filename)

        if self._stream is not None:
            stats = Stats(profile, stream=self._stream)
            stats.sort_stats(*self._sort_by)
            print("-" * 80, file=self._stream)
            print("PATH: {!r}".format(environ.get("PATH_INFO", "")), file=self._stream)
            stats.print_stats(*self._restrictions)
            print("-" * 80 + "\n", file=self._stream)

        return [body]
