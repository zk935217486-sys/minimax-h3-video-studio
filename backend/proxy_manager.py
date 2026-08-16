from __future__ import annotations

from urllib.parse import urlparse


class ProxyManager:
    def __init__(self, proxies: list[str] | None = None):
        self.proxies = list(proxies or [])
        self.index = 0

    def set_proxies(self, proxies: list[str]) -> None:
        self.proxies = list(proxies)
        self.index = 0

    def get_next_proxy(self) -> str | None:
        if not self.proxies:
            return None
        proxy = self.proxies[self.index % len(self.proxies)]
        self.index += 1
        return proxy

    @staticmethod
    def is_valid_proxy(proxy: str) -> bool:
        parsed = urlparse(proxy)
        return parsed.scheme in {"http", "https", "socks5"} and bool(parsed.hostname and parsed.port)
