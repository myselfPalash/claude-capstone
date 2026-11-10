"""Static checks on the front-end files (design-review M4).

These checks do NOT prove browser rendering; the manual browser check
(stored HTML such as <b>x</b> displays literally) remains separate.
"""
import re
from html.parser import HTMLParser
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent.parent / "app" / "static"

FORBIDDEN_JS = [
    "innerHTML",
    "outerHTML",
    "insertAdjacentHTML",
    "document.write",  # also covers document.writeln
    "eval(",
    "new Function",
    "setTimeout(\"",
    "setTimeout('",
    "setInterval(\"",
    "setInterval('",
]


def strip_js_comments(src):
    """Remove // and /* */ comments while leaving string/template literals intact.

    Comments are removed so a comment merely mentioning a forbidden API does
    not fail the test. Code and string contents are still checked.
    """
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if c in "\"'`":
            quote = c
            out.append(c)
            i += 1
            while i < n:
                ch = src[i]
                out.append(ch)
                i += 1
                if ch == "\\" and i < n:
                    out.append(src[i])
                    i += 1
                elif ch == quote:
                    break
        elif c == "/" and nxt == "/":
            while i < n and src[i] != "\n":
                i += 1
        elif c == "/" and nxt == "*":
            end = src.find("*/", i + 2)
            i = n if end == -1 else end + 2
            out.append(" ")
        else:
            out.append(c)
            i += 1
    return "".join(out)


class _HtmlScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []  # (attrs dict, inline body)
        self.links = []
        self.handler_attrs = []
        self._in_script = False
        self._body = ""
        self._attrs = {}

    def _check_attrs(self, tag, attrs):
        for name, _ in attrs:
            if name.lower().startswith("on"):
                self.handler_attrs.append((tag, name))

    def handle_starttag(self, tag, attrs):
        self._check_attrs(tag, attrs)
        if tag == "script":
            self._in_script = True
            self._attrs = dict(attrs)
            self._body = ""
        elif tag == "link":
            self.links.append(dict(attrs))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        if self._in_script:
            self._body += data

    def handle_endtag(self, tag):
        if tag == "script" and self._in_script:
            self.scripts.append((self._attrs, self._body))
            self._in_script = False


def _scan_index():
    parser = _HtmlScan()
    parser.feed((STATIC_DIR / "index.html").read_text(encoding="utf-8"))
    parser.close()
    return parser


def test_app_js_has_no_dangerous_apis():
    code = strip_js_comments((STATIC_DIR / "app.js").read_text(encoding="utf-8"))
    found = [p for p in FORBIDDEN_JS if p in code]
    assert not found, f"forbidden APIs in app.js: {found}"


def test_comment_stripper_behaviour():
    sample = 'a(); // innerHTML here\n/* eval( */ var u = "http://x"; b.innerHTML = 1;'
    stripped = strip_js_comments(sample)
    assert stripped.count("innerHTML") == 1  # only the code use remains
    assert "eval(" not in stripped
    assert "http://x" in stripped


def test_app_js_uses_textcontent():
    code = strip_js_comments((STATIC_DIR / "app.js").read_text(encoding="utf-8"))
    assert "textContent" in code


def test_index_has_no_inline_script_bodies():
    scan = _scan_index()
    assert scan.scripts, "index.html should load a script"
    for attrs, body in scan.scripts:
        assert "src" in attrs, "inline <script> without src"
        assert body.strip() == "", "inline <script> body found"


def test_index_has_no_inline_event_handlers():
    assert _scan_index().handler_attrs == []
    raw = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert not re.search(r"\son[a-z]+\s*=", raw, re.IGNORECASE)
    assert "javascript:" not in raw.lower()


def test_index_references_app_js_and_styles_css():
    scan = _scan_index()
    assert any(a.get("src") == "/static/app.js" for a, _ in scan.scripts)
    assert any(l.get("href") == "/static/styles.css" for l in scan.links)


def test_index_served_at_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"/static/app.js" in resp.data


def test_static_assets_served(client):
    for path in ("/static/app.js", "/static/styles.css"):
        resp = client.get(path)
        assert resp.status_code == 200, path
        resp.close()
