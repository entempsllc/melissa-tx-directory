import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = (ROOT / "CNAME").read_text(encoding="utf-8").strip()


def local_path(url: str) -> Path:
    path = urlparse(url).path
    if path == "/":
        return ROOT / "index.html"
    if path.endswith("/"):
        return ROOT / path.lstrip("/") / "index.html"
    return ROOT / path.lstrip("/")


class SearchIdentityContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = ET.parse(ROOT / "sitemap.xml").getroot()
        cls.urls = [node.text.strip() for node in root.findall("{*}url/{*}loc")]

    def test_sitemap_pages_exist_and_use_https_self_canonicals(self):
        self.assertTrue(self.urls)
        for url in self.urls:
            with self.subTest(url=url):
                self.assertTrue(url.startswith(f"https://{DOMAIN}/"))
                page = local_path(url)
                self.assertTrue(page.is_file(), f"Missing sitemap file: {page}")
                html = page.read_text(encoding="utf-8")
                canonicals = re.findall(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', html, re.I)
                self.assertEqual(canonicals, [url])

    def test_sitemap_pages_disclose_independent_non_government_identity(self):
        for url in self.urls:
            with self.subTest(url=url):
                html = local_path(url).read_text(encoding="utf-8").lower()
                self.assertIn('class="identity-notice"', html)
                self.assertIn("not an official", html)

    def test_admin_is_crawlable_noindex(self):
        admin = (ROOT / "admin.html").read_text(encoding="utf-8").lower()
        self.assertRegex(admin, r'<meta[^>]+name=["\']robots["\'][^>]+noindex')
        robots = (ROOT / "robots.txt").read_text(encoding="utf-8").lower()
        self.assertNotIn("disallow: /admin.html", robots)


if __name__ == "__main__":
    unittest.main()
