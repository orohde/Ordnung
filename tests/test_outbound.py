"""A redirect to another address does not take the key along."""
import urllib.request

from ordnung.outbound import KeepSecrets


def follow(url: str, to: str) -> urllib.request.Request:
    req = urllib.request.Request(url, headers={"Authorization": "Bearer geheim", "x-api-key": "sk-geheim",
                                               "User-Agent": "test"})
    return KeepSecrets().redirect_request(req, None, 302, "Found", {}, to)


def test_secrets_stay_with_their_origin():
    same = follow("https://ntfy.example/thema", "https://ntfy.example/anders")
    assert same.get_header("Authorization") == "Bearer geheim" and same.get_header("X-api-key") == "sk-geheim"
    for elsewhere in ("https://fremd.example/x", "http://ntfy.example/thema", "https://ntfy.example:8443/thema"):
        new = follow("https://ntfy.example/thema", elsewhere)
        assert new.get_header("Authorization") is None and new.get_header("X-api-key") is None, elsewhere
        assert new.get_header("User-agent") == "test"
