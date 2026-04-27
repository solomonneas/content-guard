from __future__ import annotations

import re

from .types import Rule

DEFAULT_RULES: tuple[Rule, ...] = (
    Rule(
        id="ssh-private-target",
        category="infrastructure",
        pattern=r"\b[\w.-]+@(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|127\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\S+)?",
        replacement="[redacted-target]",
        description="SSH or SCP target on a private IP address.",
    ),
    Rule(
        id="private-ipv4",
        category="infrastructure",
        pattern=r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|127\.\d{1,3}\.\d{1,3}\.\d{1,3})\b",
        replacement="[redacted-ip]",
        description="RFC 1918 or loopback IPv4 address.",
    ),
    Rule(
        id="localhost-port",
        category="infrastructure",
        pattern=r"\blocalhost:\d+\b",
        replacement="[redacted-service]",
        description="Local service endpoint.",
        flags=re.IGNORECASE,
    ),
    Rule(
        id="localhost-bare",
        category="infrastructure",
        pattern=r"(?<![\w.-])local" r"host(?![\w.-])",
        replacement="[redacted-service]",
        description="Bare local host reference.",
        flags=re.IGNORECASE,
    ),
    Rule(
        id="port-reference",
        category="infrastructure",
        pattern=r"\bport\s+\d{4,5}\b",
        replacement="port [redacted]",
        description="Likely internal service port reference.",
        flags=re.IGNORECASE,
    ),
    Rule(
        id="coauthored-by-trailer",
        category="attribution",
        pattern=r"^Co-authored-by:\s*.+(?:\r?\n)?",
        replacement="",
        description="Git co-author trailer.",
        flags=re.IGNORECASE | re.MULTILINE,
    ),
    Rule(
        id="email",
        category="pii",
        pattern=r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        replacement="<PRIVATE_EMAIL>",
        description="Email address.",
        flags=re.IGNORECASE,
    ),
    Rule(
        id="us-phone",
        category="pii",
        pattern=r"\b(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}\b",
        replacement="<PRIVATE_PHONE>",
        description="US-style phone number.",
    ),
    Rule(
        id="bearer-token",
        category="secret",
        pattern=r"\bBearer\s+[A-Za-z0-9_~+/=-](?:[A-Za-z0-9._~+/=-]{18,}[A-Za-z0-9_~+/=-])\b",
        replacement="Bearer [redacted-secret]",
        description="Bearer token.",
        flags=re.IGNORECASE,
    ),
    Rule(
        id="api-key-assignment",
        category="secret",
        pattern=r"\b(?:api[_-]?key|token|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_~+/=-](?:[A-Za-z0-9._~+/=-]{18,}[A-Za-z0-9_~+/=-])['\"]?",
        replacement="[redacted-secret]",
        description="Likely API key, token, or secret assignment.",
        flags=re.IGNORECASE,
    ),
    Rule(
        id="private-key-block",
        category="secret",
        pattern=r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
        replacement="[redacted-private-key]",
        description="PEM private key block.",
    ),
)
