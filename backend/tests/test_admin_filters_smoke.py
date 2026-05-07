import json
import os
import unittest
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, ProxyHandler, Request, build_opener


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


class AdminFiltersSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ADMIN_USERNAME or not ADMIN_PASSWORD:
            raise unittest.SkipTest("ADMIN_USERNAME/ADMIN_PASSWORD are not configured")

        cls.cookie_jar = CookieJar()
        # Disable system proxy usage to avoid false 502 for localhost on Windows.
        cls.opener = build_opener(ProxyHandler({}), HTTPCookieProcessor(cls.cookie_jar))

        login_req = Request(
            url=f"{API_BASE_URL}/api/users/login",
            method="POST",
            data=json.dumps({"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with cls.opener.open(login_req, timeout=10) as resp:
                if resp.status != 200:
                    raise unittest.SkipTest("Cannot login as admin")
        except (URLError, HTTPError):
            raise unittest.SkipTest("API is unavailable or admin login failed")

    def _request(self, path: str):
        req = Request(url=f"{API_BASE_URL}{path}", method="GET")
        with self.opener.open(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}

    def test_admin_users_filter_sort_pagination(self):
        query = urlencode(
            {
                "page": 1,
                "page_size": 10,
                "search": "a",
                "role": "user",
                "sort_by": "created_at",
                "sort_order": "desc",
            }
        )

        status, data = self._request(f"/api/admin/users?{query}")
        self.assertEqual(status, 200)
        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertIn("page", data)
        self.assertIn("page_size", data)


if __name__ == "__main__":
    unittest.main()
