# LinkedIn announcement: AssetCare is live

Drafted 2026-09-23. Facts checked against the repository and the live host on that date. Post manually; nothing here is
published automatically. Attach the social image `assets/og/assetcare.png` or a screenshot of the dashboard.

Links to use:

- Live: https://assetcare.janaka.me
- Case study: https://janaka.me/lab/assetcare/
- Article: https://janaka.me/blog/posts/assetcare-idea-to-production.html
- Source: https://github.com/Janaka2/spring-angular-production-blueprint
- Portfolio: https://janaka.me

Hashtags (pick five to seven): #Java #SpringBoot #Angular #Kubernetes #CloudNative #SoftwareArchitecture #AIAssistedEngineering

---

## 1. Full post

AssetCare is now live.

It is an asset-maintenance application: people own things, things need servicing, someone has to prove what was done and when. A modest domain on purpose. The point was never the CRUD.

The point was to take one complete system through the whole production path, and to execute every step rather than describe it:

Java 25 and Spring Boot 4.1, clean architecture enforced by an ArchUnit test
Angular 22 with a strict Content-Security-Policy in the production build
PostgreSQL 18 with Liquibase changesets, validated by Hibernate
Keycloak, OpenID Connect with PKCE, the API as a resource server
Multi-arch, non-root container images, scanned and signed
A Helm chart, K3s, Traefik, cert-manager with a Let's Encrypt certificate
One Hetzner Cloud server created from Terraform, with a cloud firewall and backups
GitHub Actions: tests at every level, a restore drill, CodeQL, Trivy, gitleaks, a signed v1.0.0
Health probes, a runbook, and a verification report that only says PASS when something was run

It is a production-style reference deployment, not a commercial product: one node, a public demo account, sample data, and a written list of what an enterprise would replace.

This project also became an experiment in how far AI-assisted engineering can accelerate a senior engineer without removing engineering discipline. The honest answer, after twenty-two years of enterprise Java: a long way on implementation, debugging, migration analysis, Kubernetes troubleshooting and documentation. Not at all on architecture, security, trade-offs, validation and the production decisions. The assistant worked inside a ten-line CLAUDE.md of non-negotiables and had to pass the same tests and scans as I do. AI raised the velocity. The discipline is what made the result worth putting behind a public URL.

The demo account and the full write-up, including what broke on the way, are on my site.

Live: https://assetcare.janaka.me
Case study: https://janaka.me/lab/assetcare/
Portfolio: https://janaka.me

#Java #SpringBoot #Angular #Kubernetes #CloudNative #SoftwareArchitecture

---

## 2. Short version

AssetCare is now live: https://assetcare.janaka.me

A complete Java 25 + Spring Boot 4.1 + Angular 22 application, taken all the way to production: PostgreSQL and Liquibase, Keycloak, non-root container images, Helm, K3s, cert-manager with Let's Encrypt, Terraform on Hetzner, GitHub Actions with scans and signed releases, health probes, backups, a runbook.

Not the CRUD; the path. Every step executed, verified from outside, and documented with what an enterprise would replace.

It was also a test of AI-assisted engineering on a real system: the assistant accelerated implementation, debugging and documentation a great deal; architecture, security, validation and every production decision stayed with me. Velocity from AI, production-worthiness from discipline.

Demo account and case study: https://janaka.me/lab/assetcare/
Portfolio: https://janaka.me

#Java #SpringBoot #Kubernetes #CloudNative #AIAssistedEngineering

---

## 3. Technical version

AssetCare is live at https://assetcare.janaka.me. For the engineers: what is actually running, and what was verified today from outside the server.

Runtime
- Traefik (bundled with K3s) is the only door: TLS termination, rate limit on /api, routes for the SPA, the API, Keycloak under /auth, and only /actuator/health and /actuator/info from the actuator.
- Angular 22 on unprivileged nginx, runtime config.json rendered from the environment, strict CSP without inline scripts.
- Spring Boot 4.1 on Java 25: Problem Details (RFC 9457), If-Match with 428/409, Idempotency-Key on creates, an audit event per write in the same transaction, authorization as one policy object.
- PostgreSQL 18 with Liquibase changesets and rollbacks; Hibernate on validate only.
- Keycloak 26, Authorization Code + PKCE; roles USER / ADMIN / AUDITOR from the token.
- MinIO behind the S3 API for attachments; SHA-256 recorded.

Delivery
- Multi-arch (amd64 + arm64) non-root images, Trivy gate, CycloneDX SBOM, keyless cosign signature and provenance on v1.0.0.
- Helm chart with enterprise switches (external DB, IdP, object storage, existingSecret), linted and rendered in CI for both value sets.
- Terraform (hcloud) for one CX33 with a cloud firewall, cloud-init user and server backups. Moved off Oracle's free tier after repeated "out of host capacity"; the chart and images were provider-neutral, so it was a change of VM, not of architecture.
- ci / security / release workflows: Testcontainers, ArchUnit, Playwright against the production image, a backup-damage-restore drill, helm lint, terraform validate, CodeQL, gitleaks.

Verified 23 Sep 2026
- 200 with a Let's Encrypt certificate and security headers on /
- 401 on an anonymous GET /api/v1/assets
- /actuator/health UP with liveness, readiness and dependency groups
- Keycloak discovery served behind the same host; /actuator/prometheus not routed

Honest boundary: one node, Kubernetes Secrets rather than a vault, Keycloak in dev mode in the chart, and the observability profile (Prometheus, Grafana, Loki, Tempo, OTel Collector) instrumented and runnable locally but not deployed on an 8 GB server. All of it is written down in PRODUCTION-GAPS.md.

AI-assisted engineering was used throughout, inside a CLAUDE.md of non-negotiables and project skills. It accelerated implementation, Spring Boot 4.1 migration debugging, Kubernetes troubleshooting and the operations documentation. Architecture, security, trade-offs, validation and deployment decisions stayed engineering-led, and the verification report only records what I ran.

Source (Apache-2.0): https://github.com/Janaka2/spring-angular-production-blueprint
Case study and demo account: https://janaka.me/lab/assetcare/
Article: https://janaka.me/blog/posts/assetcare-idea-to-production.html

#Java #SpringBoot #Angular #Kubernetes #Helm #PostgreSQL #CloudNative

---

## Posting note

- Best as a document post or with one image; the first line "AssetCare is now live." stays above the fold.
- Reply to comments with the demo credentials (demo / AssetCare-Demo-2026) rather than putting them in the post, so the account can be reset without editing the post.
- Do not add user numbers, uptime or performance figures; none are measured.
