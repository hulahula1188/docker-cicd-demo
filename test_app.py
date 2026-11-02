"""单元测试 + 真实 HTTP 冒烟测试，全部用标准库，不需要装任何依赖。"""

import json
import threading
import unittest
import urllib.request

from app import greet, make_server


class TestGreet(unittest.TestCase):
    def test_normal_name(self):
        self.assertEqual(greet("Docker"), "Hello, Docker!")

    def test_blank_name(self):
        self.assertEqual(greet("   "), "Hello, stranger!")


class TestHttpSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(port=0)  # 0 = 让系统分配空闲端口
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _get(self, path):
        url = f"http://127.0.0.1:{self.port}{path}"
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_health(self):
        status, body = self._get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")

    def test_hello(self):
        status, body = self._get("/hello?name=CI")
        self.assertEqual(status, 200)
        self.assertEqual(body["message"], "Hello, CI!")


if __name__ == "__main__":
    unittest.main(verbosity=2)
