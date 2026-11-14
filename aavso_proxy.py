#!/usr/bin/env python3
"""
Local helper for the AAVSO light-curve pages (version 3).

Serves the English page at http://localhost:8765/ (also /en) and the
Ukrainian page at http://localhost:8765/uk, and forwards /vsx?... requests
to https://vsx.aavso.org/index.php?... so the browser does not hit CORS
limits. Only the VSX "api.object" view is forwarded. Standard library only.

Usage:  python aavso_proxy.py [port]
"""
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERSION = 3
VSX = os.environ.get("AAVSO_VSX_URL", "https://vsx.aavso.org/index.php")
HERE = Path(__file__).resolve().parent

# Page files, with patterns that also accept browser-renamed downloads,
# e.g. "aavso_lightcurve_en (1).html".
PAGE_FILES = {
    "en": ("aavso_lightcurve_en.html", re.compile(r"^aavso_lightcurve_en\s*(\(\d+\))?\.html$", re.I)),
    "uk": ("aavso_lightcurve.html", re.compile(r"^aavso_lightcurve\s*(\(\d+\))?\.html$", re.I)),
}
ROUTES = {
    "/": "en", "/index.html": "en", "/en": "en", "/en/": "en", "/aavso_lightcurve_en.html": "en",
    "/uk": "uk", "/uk/": "uk", "/aavso_lightcurve.html": "uk",
}


def find_page(lang):
    """Return the path of the page file for `lang`, or None."""
    name, pattern = PAGE_FILES[lang]
    exact = HERE / name
    if exact.is_file():
        return exact
    candidates = [p for p in HERE.iterdir() if p.is_file() and pattern.match(p.name)]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        if url.path == "/vsx":
            self._proxy(url.query)
            return
        lang = ROUTES.get(url.path)
        if lang:
            page = find_page(lang)
            if page:
                self._send(200, "text/html; charset=utf-8", page.read_bytes())
            else:
                msg = (f"aavso_proxy.py v{VERSION}: page file '{PAGE_FILES[lang][0]}' "
                       f"was not found in\n  {HERE}\n\n"
                       "Put it in the same folder as aavso_proxy.py and reload.")
                self._send(404, "text/plain; charset=utf-8", msg.encode())
            return
        if url.path == "/favicon.ico":
            self._send(204, "text/plain", b"")
            return
        self._send(404, "text/plain; charset=utf-8",
                   f"Not found: {url.path}\nPages: / (English), /uk (Ukrainian)".encode())

    def _proxy(self, query):
        params = urllib.parse.parse_qs(query, keep_blank_values=True)
        if params.get("view") != ["api.object"]:
            self._send(400, "text/plain", b"Only view=api.object is allowed")
            return
        req = urllib.request.Request(
            f"{VSX}?{query}", headers={"User-Agent": f"aavso-lightcurve-local/{VERSION}"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                body = r.read()
                ctype = r.headers.get("Content-Type", "text/xml")
            self._send(200, ctype, body)
        except urllib.error.HTTPError as e:
            self._send(e.code, "text/plain", f"VSX error: {e}".encode())
        except Exception as e:  # network errors, timeouts
            self._send(502, "text/plain", f"Proxy error: {e}".encode())

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s  %s\n" % (self.log_date_time_string(), fmt % args))


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://localhost:{port}/"
    print(f"aavso_proxy.py v{VERSION}, folder: {HERE}")
    for lang, label, addr in (("en", "English page:  ", url), ("uk", "Ukrainian page:", url + "uk")):
        page = find_page(lang)
        status = f"-> {page.name}" if page else f"!! '{PAGE_FILES[lang][0]}' NOT FOUND in this folder"
        print(f"{label} {addr:<28} {status}")
    print("Press Ctrl+C to stop.")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
