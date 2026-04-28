# public-repo policy rationale

Sibling rationale doc for `policies/public-repo.json`. JSON does not support
inline comments, so the long-form reasoning lives here.

## What this policy is for

`public-repo` is the publish gate for code that is going into a public GitHub
(or similar) repository. It backs `content_guard.git_scan`,
`content_guard.git_commits`, and the staged-file/commit-message stages of
`content_guard.publish_check`.

A technical docs repo is a different surface from a blog or a social post:

- README, CONTRIBUTING, docs/, examples/, and tests routinely have to discuss
  `localhost`, named local ports, and `127.0.0.1` so a reader can run the code.
- Treating those as hard blocks creates noise and trains contributors to bypass
  the gate with `content-guard: allow ...` comments.
- Real leakage in this surface looks like an RFC 1918 office IP, a secret, an
  email, a phone number, or a `Co-authored-by` trailer.

## Action choices

| Rule              | Action | Reason                                                                 |
|-------------------|--------|------------------------------------------------------------------------|
| `private-ipv4`    | block  | RFC 1918 IPs leak office/home network topology and should never ship.  |
| `loopback-ipv4`   | warn   | `127.0.0.1` is baseline tutorial/dev-loop content.                     |
| `localhost-port`  | warn   | `localhost:5204` style endpoints are normal in setup docs.             |
| `localhost-bare`  | warn   | `localhost` as a word is unavoidable in technical docs.                |
| `port-reference`  | warn   | "port 18789" style references are fine in docs; not a leak by itself.  |
| `email`           | block  | Personal email is PII, not technical doc content.                      |
| `us-phone`        | block  | Phone number is PII.                                                   |
| `bearer-token`    | block  | Secret.                                                                |
| `api-key-assignment` | block | Secret.                                                              |
| `private-key-block`  | block | Secret.                                                              |
| `coauthored-by-trailer` | block | Attribution must come from a real human committer.               |

## When to override

Use a per-line allow comment for legitimate examples that trip a `block` rule.
Do not lower a category default in this policy file: if a docs repo can publish
RFC 1918 IPs unguarded, this policy is no longer doing its job.

The stricter `public-content` policy (blog and social posts) does keep the
infrastructure rules at block, because a marketing/blog surface should not
discuss internal addresses or ports at all.
