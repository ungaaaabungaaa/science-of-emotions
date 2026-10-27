# Security and privacy

This static aggregate viewer has no account, backend storage, analytics, remote fonts, or user-text input. It requests local app files and the aggregate JSON. External source links open only when selected.

The development server binds to loopback, checks Host, serves five allowlisted files, and sends restrictive content-security/no-cache headers. It is not a production web server. Host only `dist/` output for a public static deployment.

The downloader uses four explicit pinned official URLs, refuses redirects, bounds responses, checks hashes, and refuses to overwrite changed files. The parser rejects symlinks, malformed records, and oversized inputs. This is a local research tool, not a service accepting arbitrary filesystem paths. Keep raw downloads out of public hosting directories.

Use private repository vulnerability reporting if available. Otherwise describe impact in an issue without secret data or an active exploit. Never include tokens, personal information, or raw comments.
