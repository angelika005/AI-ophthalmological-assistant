import json
import os
import random
import string
import unittest
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, ProxyHandler, Request, build_opener


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class ApiIntegrationSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cookie_jar = CookieJar()
        # Disable system proxy usage to avoid false 502 for localhost on Windows.
        cls.opener = build_opener(ProxyHandler({}), HTTPCookieProcessor(cls.cookie_jar))

    def _request(self, method: str, path: str, payload=None):
        url = f"{API_BASE_URL}{path}"
        headers = {"Content-Type": "application/json"}
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = Request(url=url, method=method, data=data, headers=headers)
        try:
            with self.opener.open(req, timeout=10) as resp:
                body = resp.read().decode("utf-8")
                return resp.status, json.loads(body) if body else {}
        except HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            try:
                parsed = json.loads(body) if body else {}
            except json.JSONDecodeError:
                parsed = {"raw": body}
            return e.code, parsed

    def test_01_root(self):
        try:
            status, data = self._request("GET", "/")
        except URLError:
            self.skipTest("API server is not running")
            return

        if status == 502:
            self.skipTest("API gateway/backend returned 502; infrastructure is unavailable")

        self.assertEqual(status, 200)
        self.assertIn("message", data)

    def test_02_auth_and_user_images_filters(self):
        # Register a test user
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        username = f"smoke_{suffix}"
        password = "smoke123"
        email = f"{username}@example.com"

        status, _ = self._request(
            "POST",
            "/api/users/register",
            {"username": username, "password": password, "email": email},
        )

        if status == 502:
            self.skipTest("API gateway/backend returned 502; infrastructure is unavailable")

        self.assertIn(status, (201, 400))

        # Login (sets cookies)
        status, login_data = self._request(
            "POST",
            "/api/users/login",
            {"username": username, "password": password},
        )
        self.assertEqual(status, 200)
        self.assertIn("access_token", login_data)

        # Validate image list endpoint with filter/search/sort/pagination params
        query = urlencode(
            {
                "page": 1,
                "page_size": 12,
                "search": "glaucoma",
                "sort_by": "created_at",
                "sort_order": "desc",
            }
        )
        status, images_data = self._request("GET", f"/api/images?{query}")
        self.assertEqual(status, 200)
        self.assertIn("items", images_data)
        self.assertIn("total", images_data)
        self.assertIn("page", images_data)
        self.assertIn("page_size", images_data)

    def test_03_auth_required_for_images(self):
        # Use a fresh opener without cookies to verify access restriction
        opener = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()))
        req = Request(url=f"{API_BASE_URL}/api/images", method="GET")

        try:
            with opener.open(req, timeout=10):
                self.fail("Expected unauthorized response")
        except HTTPError as e:
            if e.code == 502:
                self.skipTest("API gateway/backend returned 502; infrastructure is unavailable")
            self.assertEqual(e.code, 401)
        except URLError:
            self.skipTest("API server is not running")


if __name__ == "__main__":
    unittest.main()
