"""Requests to other servers: a key or token goes only to the address it was given for.

urllib follows redirects and takes every header along – also to another host, or from https down
to http. This handler drops the headers that carry a secret as soon as a redirect leaves the
origin (scheme, host and port) of the request. install() puts it under every urlopen().
"""
from __future__ import annotations

import urllib.request
from urllib.parse import urlsplit

SECRET_HEADERS = {"authorization", "proxy-authorization", "cookie", "x-api-key", "api-key"}


def _origin(url: str) -> tuple[str, str, int | None]:
    parts = urlsplit(url)
    return parts.scheme.lower(), (parts.hostname or "").lower(), parts.port


class KeepSecrets(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and _origin(newurl) != _origin(req.full_url):
            for name in list(new.headers):
                if name.lower() in SECRET_HEADERS:
                    del new.headers[name]
        return new


def install() -> None:
    urllib.request.install_opener(urllib.request.build_opener(KeepSecrets))
