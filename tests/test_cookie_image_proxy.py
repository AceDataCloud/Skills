"""Portable image transport must work without local DNS behind a trusted proxy."""
from __future__ import annotations

import importlib.util
import socket
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parents[1]


def load(skill):
    path = ROOT / 'skills' / skill / 'scripts' / f'{skill}.py'
    spec = importlib.util.spec_from_file_location(f'{skill}_proxy_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULES = [(name, load(name)) for name in ('csdn', 'bilibili', 'medium')]
PUBLIC = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 0))]
PRIVATE = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 0))]


class CookieImageProxyTests(unittest.TestCase):
    def test_selected_proxy_defers_hostname_dns(self):
        for name, module in MODULES:
            with self.subTest(skill=name), \
                 patch.object(module.urllib.request, 'getproxies', return_value={'https': 'http://127.0.0.1:8080'}), \
                 patch.object(module.urllib.request, 'proxy_bypass', return_value=False), \
                 patch.object(module.socket, 'getaddrinfo', side_effect=AssertionError('must not use local DNS')):
                module._assert_public_url('https://images.example.com/photo.png')

    def test_proxy_bypass_uses_authority_including_port(self):
        for name, module in MODULES:
            with self.subTest(skill=name), \
                 patch.object(module.urllib.request, 'getproxies', return_value={'https': 'http://proxy:8080'}), \
                 patch.object(module.urllib.request, 'proxy_bypass', return_value=True) as bypass, \
                 patch.object(module.socket, 'getaddrinfo', return_value=PUBLIC):
                module._assert_public_url('https://images.example.com:443/photo.png')
                bypass.assert_called_once_with('images.example.com:443')

    def test_private_literal_rejected_even_with_proxy(self):
        for name, module in MODULES:
            for host in ('127.0.0.1', '10.0.0.1', '169.254.169.254', '[::1]', '[fc00::1]', '224.0.0.1'):
                with self.subTest(skill=name, host=host), \
                     patch.object(module.urllib.request, 'getproxies', return_value={'https': 'http://127.0.0.1:8080'}), \
                     patch.object(module.socket, 'getaddrinfo', side_effect=AssertionError('literal needs no DNS')):
                    with self.assertRaisesRegex(RuntimeError, 'blocked non-public'):
                        module._assert_public_url(f'https://{host}/photo.png')

    def test_no_proxy_or_bypass_preserves_local_dns_validation(self):
        for name, module in MODULES:
            for proxies, bypass in (({}, False), ({'http': 'http://proxy:8080'}, False), ({'https': 'http://proxy:8080'}, True)):
                with self.subTest(skill=name, proxies=proxies, bypass=bypass), \
                     patch.object(module.urllib.request, 'getproxies', return_value=proxies), \
                     patch.object(module.urllib.request, 'proxy_bypass', return_value=bypass), \
                     patch.object(module.socket, 'getaddrinfo', return_value=PRIVATE) as resolve:
                    with self.assertRaisesRegex(RuntimeError, 'blocked non-public'):
                        module._assert_public_url('https://images.example.com/photo.png')
                    resolve.assert_called_once_with('images.example.com', None)

    def test_direct_public_hostname_passes(self):
        for name, module in MODULES:
            with self.subTest(skill=name), \
                 patch.object(module.urllib.request, 'getproxies', return_value={}), \
                 patch.object(module.socket, 'getaddrinfo', return_value=PUBLIC):
                module._assert_public_url('https://images.example.com/photo.png')

    def test_mixed_public_private_dns_answer_rejected(self):
        for name, module in MODULES:
            with self.subTest(skill=name), \
                 patch.object(module.urllib.request, 'getproxies', return_value={}), \
                 patch.object(module.socket, 'getaddrinfo', return_value=PUBLIC + PRIVATE):
                with self.assertRaisesRegex(RuntimeError, 'blocked non-public'):
                    module._assert_public_url('https://images.example.com/photo.png')

    def test_unsupported_url_never_reaches_dns(self):
        for name, module in MODULES:
            for url in ('file:///etc/passwd', 'ftp://images.example.com/a', 'https://user:pass@images.example.com/a'):
                with self.subTest(skill=name, url=url), patch.object(module.socket, 'getaddrinfo', side_effect=AssertionError('must not resolve')):
                    with self.assertRaisesRegex(RuntimeError, 'unsupported image URL'):
                        module._assert_public_url(url)


if __name__ == '__main__':
    unittest.main()
