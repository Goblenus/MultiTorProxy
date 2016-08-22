import unittest
import MultiTorProxy
import time
import requests

class TestMultiTorProxy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.multi_tor_proxy = MultiTorProxy.MultiTorProxy()
        cls.multi_tor_proxy.start()
        time.sleep(15)

    def test_get_data(self):
        for i in range(0, 4):
            data = requests.get("http://sony.com", proxies=dict(http='socks5://localhost:53000',
                                                                https='socks5://localhost:53000'))

            self.assertEqual(data.status_code, 200)
            self.assertGreater(len(data.text), 0)