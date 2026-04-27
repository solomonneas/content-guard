from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from content_guard.engine import scan_text
from content_guard.policy import Policy, load_policy
from content_guard.types import Rule, ScanOptions


class EngineTests(unittest.TestCase):
    def test_blocks_infrastructure_but_warns_pii_by_default(self) -> None:
        # content-guard: allow all
        result = scan_text("Reach me at alice@example.com via localhost:5204")

        actions = {(f.rule_id, f.action) for f in result.findings}
        self.assertIn(("localhost-port", "block"), actions)
        self.assertIn(("email", "warn"), actions)
        self.assertTrue(result.blocked)

    def test_redacts_policy_redact_actions(self) -> None:
        policy = Policy(defaults={"infrastructure": "redact", "secret": "redact", "pii": "warn"})
        # content-guard: allow private-ipv4
        result = scan_text("Service is 192.168.1.25", policy=policy)

        self.assertFalse(result.blocked)
        self.assertEqual(result.redacted_text, "Service is [redacted-ip]")

    def test_allow_comment_applies_to_next_line(self) -> None:
        text = "<!-- content-guard: allow localhost-bare -->\nUse localhost as an example."
        result = scan_text(text)

        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].action, "allow")
        self.assertFalse(result.blocked)

    def test_frontmatter_is_skipped_by_default(self) -> None:
        # content-guard: allow localhost-port
        text = "---\nsource: localhost:5204\n---\nBody is clean.\n"
        result = scan_text(text)

        self.assertEqual(result.findings, [])

    def test_can_skip_code_blocks(self) -> None:
        # content-guard: allow localhost-port
        text = "```\ncurl http://localhost:5204\n```\n"
        result = scan_text(text, options=ScanOptions(scan_code_blocks=False))

        self.assertEqual(result.findings, [])

    def test_custom_rule(self) -> None:
        policy = Policy(
            custom_rules=[
                Rule(
                    id="project-codename",
                    category="business",
                    pattern=r"\bProject Nightshade\b",
                    replacement="[redacted-project]",
                )
            ]
        )
        result = scan_text("Project Nightshade launches later.", policy=policy)

        self.assertEqual(result.findings[0].rule_id, "project-codename")
        self.assertEqual(result.findings[0].action, "warn")

    def test_pr_draft_policy_blocks_pii(self) -> None:
        policy_path = Path(__file__).resolve().parents[1] / "policies" / "pr-draft.json"
        # content-guard: allow all
        result = scan_text("PR note with alice@example.com and localhost:5204", policy=load_policy(policy_path))

        actions = {(f.rule_id, f.action) for f in result.findings}
        self.assertIn(("email", "block"), actions)
        self.assertIn(("localhost-port", "block"), actions)
        self.assertTrue(result.blocked)

    def test_public_repo_policy_blocks_pii_and_secrets(self) -> None:
        policy_path = Path(__file__).resolve().parents[1] / "policies" / "public-repo.json"
        # content-guard: allow all
        result = scan_text("token = abcdefghijklmnopqrstuvwxyz123456 and alice@example.com", policy=load_policy(policy_path))

        actions = {(f.rule_id, f.action) for f in result.findings}
        self.assertIn(("api-key-assignment", "block"), actions)
        self.assertIn(("email", "block"), actions)
        self.assertTrue(result.blocked)

    def test_secret_assignment_preserves_sentence_punctuation(self) -> None:
        # content-guard: allow api-key-assignment
        result = scan_text("Temporary token=abc123abc123abc123abc123abc123.")

        # content-guard: allow api-key-assignment
        self.assertEqual(result.findings[0].match, "token=abc123abc123abc123abc123abc123")
        self.assertEqual(result.redacted_text, "Temporary [redacted-secret].")

    def test_coauthor_trailer_blocks_and_removes_line(self) -> None:
        # content-guard: allow email
        result = scan_text("feat: change\n\nCo-authored-by: Example User <user@example.com>\n")

        self.assertEqual(result.findings[0].rule_id, "coauthored-by-trailer")
        self.assertTrue(result.blocked)
        self.assertEqual(result.redacted_text, "feat: change\n\n")

    def test_policy_can_enable_opf_backend(self) -> None:
        with TemporaryDirectory() as tmp:
            opf_bin = Path(tmp) / "opf"
            policy_path = Path(tmp) / "policy.json"
            opf_bin.write_text(
                "#!/usr/bin/env python3\n"
                "import pathlib, sys\n"
                "text = pathlib.Path(sys.argv[-1]).read_text()\n"
                "print(text.replace('Alice Example', '<PRIVATE_PERSON>'), end='')\n"
            )
            opf_bin.chmod(0o755)
            policy_path.write_text(
                '{'
                '"backends":{"opf":{"enabled":true,"action":"redact","bin":"'
                + str(opf_bin)
                + '"}}'
                '}'
            )

            result = scan_text("Alice Example wrote the draft.", policy=load_policy(policy_path))

        self.assertIn(("opf-pii", "redact"), {(f.rule_id, f.action) for f in result.findings})
        self.assertEqual(result.redacted_text, "<PRIVATE_PERSON> wrote the draft.")


if __name__ == "__main__":
    unittest.main()
