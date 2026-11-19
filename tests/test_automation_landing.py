"""Minimal acceptance checks for the automation portfolio landing.

Run: python tests/test_automation_landing.py
"""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUTOMATION = ROOT / "automation" / "index.html"
MAIN = ROOT / "index.html"


class LinkImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.links = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img":
            self.images.append(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def parse(path):
    parser = LinkImageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def local_target_exists(base_file, href):
    href = href.split("#", 1)[0].split("?", 1)[0]
    if not href or href.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
        return True
    if href.startswith("/"):
        target = ROOT / href.lstrip("/")
    else:
        target = base_file.parent / href
    return target.exists()


class AutomationLandingTests(unittest.TestCase):
    def test_automation_page_exists_and_is_russian(self):
        self.assertTrue(AUTOMATION.exists(), "automation/index.html must exist")
        html = AUTOMATION.read_text(encoding="utf-8")
        self.assertIn('<html lang="ru"', html)

    def test_automation_title_is_industry_neutral(self):
        self.assertTrue(AUTOMATION.exists(), "automation/index.html must exist")
        title = parse(AUTOMATION).title.lower()
        self.assertIn("ai", title)
        self.assertNotIn("автобизнес", title)

    def test_automation_has_no_whatsapp_and_has_telegram_cta(self):
        self.assertTrue(AUTOMATION.exists(), "automation/index.html must exist")
        html = AUTOMATION.read_text(encoding="utf-8").lower()
        self.assertNotIn("whatsapp", html)
        self.assertNotIn("wa.me", html)
        self.assertIn("t.me/samlliik", html)

    def test_automation_local_assets_and_links_resolve(self):
        self.assertTrue(AUTOMATION.exists(), "automation/index.html must exist")
        parsed = parse(AUTOMATION)
        for image in parsed.images:
            src = image.get("src")
            self.assertTrue(src, "every img needs src")
            self.assertTrue(local_target_exists(AUTOMATION, src), f"missing image: {src}")
            self.assertIn("alt", image, f"img needs alt: {src}")
        for href in parsed.links:
            self.assertTrue(local_target_exists(AUTOMATION, href), f"broken link: {href}")

    def test_automation_has_case_and_contact_sections(self):
        self.assertTrue(AUTOMATION.exists(), "automation/index.html must exist")
        html = AUTOMATION.read_text(encoding="utf-8")
        self.assertIn('id="cases"', html)
        self.assertIn('id="contact"', html)

    def test_automation_assets_use_root_paths(self):
        self.assertTrue(AUTOMATION.exists(), "automation/index.html must exist")
        parsed = parse(AUTOMATION)
        for image in parsed.images:
            src = image.get("src", "")
            if not src.startswith(("http://", "https://", "data:")):
                self.assertTrue(src.startswith("/assets/"), f"nested page asset must use /assets/: {src}")

    def test_en_landing_stays_without_automation_entry(self):
        en = ROOT / "en" / "index.html"
        self.assertTrue(en.exists(), "en/index.html must remain present")
        self.assertNotIn("/automation/", en.read_text(encoding="utf-8"))

    def test_main_landing_links_to_automation_and_keeps_core_identity(self):
        html = MAIN.read_text(encoding="utf-8")
        self.assertIn("AI-агенты вместо ручной работы", html)
        self.assertIn("Опыт в автобизнесе", html)
        self.assertTrue(
            'href="/automation/"' in html or 'href="automation/"' in html,
            "main landing must expose the automation audience switcher",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)