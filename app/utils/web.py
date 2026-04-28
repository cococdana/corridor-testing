from __future__ import annotations

import html
import ipaddress
import re
import socket
import urllib.request
from urllib.parse import urlparse, urljoin


class FetchError(RuntimeError):
    pass


def _is_ip_disallowed(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return bool(
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def _resolve_host_ips(host: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception as e:
        raise FetchError(f"DNS resolution failed: {e}") from e
    ips: list[str] = []
    for family, _, _, _, sockaddr in infos:
        if family == socket.AF_INET:
            ips.append(sockaddr[0])
        elif family == socket.AF_INET6:
            ips.append(sockaddr[0])
    return sorted(set(ips))


def validate_url_for_fetch(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise FetchError("URL must start with http:// or https://")
    if not parsed.netloc:
        raise FetchError("URL host is missing")

    host = parsed.hostname or ""
    if not host:
        raise FetchError("URL host is missing")
    if host.lower() in {"localhost"} or host.lower().endswith(".local"):
        raise FetchError("Refusing to fetch localhost/.local URLs")

    ips = _resolve_host_ips(host)
    if not ips:
        raise FetchError("DNS resolution returned no IPs")
    if any(_is_ip_disallowed(ip) for ip in ips):
        raise FetchError("Refusing to fetch private/loopback/link-local/reserved IPs")


def fetch_url(
    url: str,
    timeout_s: float = 15.0,
    max_bytes: int = 2_000_000,
    max_redirects: int = 5,
) -> str:
    validate_url_for_fetch(url)

    try:
        current = url
        redirects = 0
        while True:
            req = urllib.request.Request(
                current,
                headers={
                    "User-Agent": "job-ops-agent/1.0 (+https://fastapi.tiangolo.com)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.7",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                status = int(getattr(resp, "status", None) or getattr(resp, "code", None) or 200)

                if status in {301, 302, 303, 307, 308}:
                    loc = resp.headers.get("Location", "") if hasattr(resp, "headers") else ""
                    if not loc:
                        raise FetchError(f"Redirect ({status}) missing Location header")
                    redirects += 1
                    if redirects > max_redirects:
                        raise FetchError("Too many redirects")
                    current = urljoin(current, loc)
                    validate_url_for_fetch(current)
                    continue

                if status >= 400:
                    raise FetchError(f"Fetch failed with status {status}")

                content_type = resp.headers.get("Content-Type", "") if hasattr(resp, "headers") else ""
                charset = "utf-8"
                m = re.search(r"charset=([A-Za-z0-9_\-]+)", content_type)
                if m:
                    charset = m.group(1)

                raw = resp.read(max_bytes + 1) or b""
                if len(raw) > max_bytes:
                    raise FetchError("Response too large")
                return raw.decode(charset, errors="replace")
    except FetchError:
        raise
    except Exception as e:
        raise FetchError(f"Failed to fetch URL: {e}") from e


def html_to_text(raw: str) -> str:
    # Remove scripts/styles.
    s = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", raw)
    s = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", s)
    # Remove nav/header/footer/aside blocks (best-effort).
    s = re.sub(r"(?is)<(nav|header|footer|aside)[^>]*>.*?</\1>", " ", s)

    # Keep line breaks for block-ish elements.
    s = re.sub(r"(?i)</(p|div|br|li|h1|h2|h3|h4|h5|h6)>", "\n", s)

    # Strip remaining tags.
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)

    # Normalize whitespace.
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r"\n\s*\n\s*\n+", "\n\n", s)
    return s.strip()


def fetch_job_posting_text(url: str) -> str:
    body = fetch_url(url)
    # If it doesn't look like HTML, treat as plain text.
    if "<html" not in body.lower() and "<body" not in body.lower() and "<div" not in body.lower():
        return body.strip()
    return html_to_text(body)

