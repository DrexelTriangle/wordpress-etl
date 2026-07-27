"""Tests for Utils.MediaURL canonicalization. Run from the repo root:

    .venv/bin/python -m unittest tests.test_media_url
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Utils.MediaURL import canonicalize_media_url, rewrite_media_urls_in_html

BASE = "https://media.example.net"


class CanonicalizeMediaURL(unittest.TestCase):
    def test_variants_all_map_to_base(self):
        want = f"{BASE}/wp-content/uploads/2016/03/image.jpg"
        for src in [
            "wp-content/uploads/2016/03/image.jpg",
            "/wp-content/uploads/2016/03/image.jpg",
            "www.thetriangle.org/wp-content/uploads/2016/03/image.jpg",
            "//www.thetriangle.org/wp-content/uploads/2016/03/image.jpg",
            "https://www.thetriangle.org/wp-content/uploads/2016/03/image.jpg",
            "https://www.thetriangle.org/proxy/wp-content/uploads/2016/03/image.jpg",
            "https://thetriangle.org/wp-content/uploads/2016/03/image.jpg",
        ]:
            self.assertEqual(canonicalize_media_url(src, base=BASE), want, src)

    def test_passthrough(self):
        for src in [
            "https://images.unsplash.com/photo-123.jpg",  # other host
            "images/logo.png",                             # relative non-wp
            "",                                             # empty
        ]:
            self.assertEqual(canonicalize_media_url(src, base=BASE), src, src)

    def test_non_string(self):
        self.assertIsNone(canonicalize_media_url(None, base=BASE))

    def test_default_base_is_proxy(self):
        # With no override, the default preserves today's working /proxy URLs.
        self.assertEqual(
            canonicalize_media_url("wp-content/uploads/x.jpg"),
            "https://www.thetriangle.org/proxy/wp-content/uploads/x.jpg",
        )


class RewriteMediaURLsInHTML(unittest.TestCase):
    def test_img_and_srcset_and_anchor(self):
        html = (
            '<p>Text</p>'
            '<img src="https://www.thetriangle.org/wp-content/uploads/2020/01/a.jpg" '
            'srcset="https://www.thetriangle.org/proxy/wp-content/uploads/2020/01/a-300x200.jpg 300w">'
            '<a href="https://thetriangle.org/wp-content/uploads/2020/01/a.jpg">full</a>'
        )
        out = rewrite_media_urls_in_html(html, base=BASE)
        self.assertNotIn("thetriangle.org", out)
        self.assertIn(f'src="{BASE}/wp-content/uploads/2020/01/a.jpg"', out)
        self.assertIn(f"{BASE}/wp-content/uploads/2020/01/a-300x200.jpg 300w", out)
        self.assertIn(f'href="{BASE}/wp-content/uploads/2020/01/a.jpg"', out)

    def test_leaves_external_images_alone(self):
        html = '<img src="https://images.unsplash.com/photo-9.jpg">'
        self.assertEqual(rewrite_media_urls_in_html(html, base=BASE), html)

    def test_no_wp_content_is_noop(self):
        html = "<p>No images here.</p>"
        self.assertEqual(rewrite_media_urls_in_html(html, base=BASE), html)


if __name__ == "__main__":
    unittest.main()
