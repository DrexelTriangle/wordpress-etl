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

    def test_legacy_therectangle_domain_is_rewritten(self):
        # therectangle.org is a defunct predecessor domain; 2011-era articles
        # still link to it and those files live in the same media tree, so
        # leaving them alone means permanently broken images.
        want = f"{BASE}/wp-content/uploads/2011/04/image.jpg"
        for src in [
            "http://new.therectangle.org/wp-content/uploads/2011/04/image.jpg",
            "https://therectangle.org/wp-content/uploads/2011/04/image.jpg",
            "//www.therectangle.org/wp-content/uploads/2011/04/image.jpg",
        ]:
            self.assertEqual(canonicalize_media_url(src, base=BASE), want, src)

    def test_unrelated_host_with_wp_content_is_untouched(self):
        # Other sites run WordPress too. Matching on the path alone would
        # rewrite genuine third-party links onto our media host.
        for src in [
            "https://mediajustice.org/wp-content/uploads/2020/04/doc.pdf",
            "https://activeminds.org/wp-content/uploads/2020/04/chart.png",
            "http://phlcouncil.com/wp-content/uploads/2019/04/testimony.pdf",
        ]:
            self.assertEqual(canonicalize_media_url(src, base=BASE), src, src)


class RewriteMediaURLsInHTML(unittest.TestCase):
    def test_img_and_srcset_and_anchor(self):
        html = (
            '<p>Text</p>'
            '<img src="https://www.thetriangle.org/wp-content/uploads/2020/01/a.jpg" '
            'srcset="https://www.thetriangle.org/proxy/wp-content/uploads/2020/01/a-300x200.jpg 300w">'
            '<a href="https://thetriangle.org/wp-content/uploads/2020/01/a.jpg">full</a>'
            '<a href="www.thetriangle.org/wp-content/uploads/2020/01/b.jpg">scheme-less</a>'
        )
        out = rewrite_media_urls_in_html(html, base=BASE)
        self.assertNotIn("thetriangle.org", out)
        self.assertIn(f'src="{BASE}/wp-content/uploads/2020/01/a.jpg"', out)
        self.assertIn(f"{BASE}/wp-content/uploads/2020/01/a-300x200.jpg 300w", out)
        self.assertIn(f'href="{BASE}/wp-content/uploads/2020/01/a.jpg"', out)
        self.assertIn(f'href="{BASE}/wp-content/uploads/2020/01/b.jpg"', out)

    def test_relative_img_srcset_and_unquoted_url(self):
        html = (
            '<img src="/wp-content/uploads/2020/01/a.jpg" '
            'srcset="/wp-content/uploads/2020/01/a-300x200.jpg 300w, '
            'wp-content/uploads/2020/01/a-600x400.jpg 600w">'
            '<a href=wp-content/uploads/2020/01/a.jpg>full</a>'
        )
        out = rewrite_media_urls_in_html(html, base=BASE)
        self.assertIn(f'src="{BASE}/wp-content/uploads/2020/01/a.jpg"', out)
        self.assertIn(f"{BASE}/wp-content/uploads/2020/01/a-300x200.jpg 300w", out)
        self.assertIn(f"{BASE}/wp-content/uploads/2020/01/a-600x400.jpg 600w", out)
        self.assertIn(f"href={BASE}/wp-content/uploads/2020/01/a.jpg", out)

    def test_leaves_external_images_alone(self):
        html = '<img src="https://images.unsplash.com/photo-9.jpg">'
        self.assertEqual(rewrite_media_urls_in_html(html, base=BASE), html)

    def test_leaves_external_wp_content_path_alone(self):
        html = '<img src="https://cdn.example.com/wp-content/uploads/photo.jpg">'
        self.assertEqual(rewrite_media_urls_in_html(html, base=BASE), html)

    def test_no_wp_content_is_noop(self):
        html = "<p>No images here.</p>"
        self.assertEqual(rewrite_media_urls_in_html(html, base=BASE), html)


if __name__ == "__main__":
    unittest.main()
