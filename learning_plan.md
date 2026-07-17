# Learning Plan — AWS + CDK + Backend + DevOps
**Project:** the-canada-movers.com — build the AWS infrastructure hands-on

**Approach:** Console first (understand what you're building) → CDK second (automate it).
Each stack has two phases: manual console work, then CDK implementation.

**Order override:** all console phases (Stacks 1-5) get done first across the whole infra, then all CDK phases (1B-4B) get done last as one batch — not interleaved stack-by-stack as originally laid out.

**Practice domain:** `the-canada-movers.com` (registered via Route 53) used for hands-on steps below instead of `the-canada-movers.com`, faster DNS validation since it's already in Route 53. Swap to real domain when going to prod.

---

## Progress Summary

| Stack | Console | CDK | Done |
|-------|---------|-----|------|
| 0 — IAM Setup | ✅ | — | ✅ |
| 1 — S3 + CloudFront + ACM | ✅ | ⬜ | ⬜ |
| 2 — Lambda + API Gateway | ✅ | ⬜ | ⬜ |
| 3 — SES (Email) | ⬜ | ⬜ | ⬜ |
| 4 — DNS (Route 53) | ⬜ | ⬜ | ⬜ |
| 5 — DevOps & Observability | ⬜ | — | ⬜ |

---

## Stack 0 — IAM Setup
*Prereq for everything. No CDK phase.*

- [x] Create IAM user with `AdministratorAccess`
- [x] Enable MFA on the IAM user
- [x] Generate access key → run `aws configure` (region: `us-east-1`)
- [x] Verify: `aws sts get-caller-identity` returns IAM user ARN (not root)
- [x] Stop using root for daily work

---

## Stack 1 — Static Hosting (S3 + CloudFront + ACM)
**CDK file:** `cdk/lib/static-site-stack.ts`

### Phase A — Console
- [x] Create S3 bucket `thecanadamovers-frontend` in `us-east-2`, block all public access
- [x] Upload `frontend/index.html` manually, confirm object URL returns 403
- [x] Request ACM cert for `the-canada-movers.com` + `www.the-canada-movers.com` in **us-east-1** (CloudFront hard requirement, different region than bucket) (DNS validation via Route 53 — use "Create records in Route 53" button, near-instant)
- [x] Create CloudFront distribution — OAC origin, apply generated bucket policy to S3
- [x] Set default root object `index.html`, error pages 403+404 → `/index.html` HTTP 200
- [x] Add alternate domain names + attach ACM cert
- [x] Wait for distribution deploy, confirm site loads via `*.cloudfront.net`
- [x] Confirm direct S3 URL still returns 403

### Phase B — CDK
- [ ] Run `cdk init app --language typescript` inside `cdk/`
- [ ] Write `cdk/lib/static-site-stack.ts` (S3 + OAC + CloudFront + ACM + BucketDeployment)
- [ ] `cdk synth StaticSiteStack` — read the generated OAC bucket policy in output
- [ ] `cdk deploy StaticSiteStack` — site loads via new CDK-managed CloudFront URL
- [ ] Delete the manually-created distribution

---

## Stack 2 — Serverless Backend (Lambda + API Gateway v2)
**CDK file:** `cdk/lib/api-stack.ts` | **Lambda:** `lambda/handler.py`

### Phase A — Console
- [x] Create Lambda function `thecanadamovers-quote` (Python 3.12), new execution role
- [x] Paste stub handler, create v2 test event, run it, read CloudWatch logs
- [x] Replace stub with `lambda/handler.py` content, re-run test — confirm pipeline executes (SES will fail, that's expected)
- [x] Create HTTP API `thecanadamovers-api` in API Gateway
- [x] Add route `POST /quote` → Lambda integration
- [x] Configure CORS: origin `https://the-canada-movers.com`, methods `POST OPTIONS`, headers `Content-Type cf-turnstile-response`
- [x] Deploy to `$default` stage, test with curl
- [x] Read API GW v2 event envelope in CloudWatch logs

### Phase B — CDK
- [ ] Install `@aws-cdk/aws-lambda-python-alpha` (requires Docker)
- [ ] Write `cdk/lib/api-stack.ts` (PythonFunction + HttpApi + CORS + route)
- [ ] `cdk deploy ApiStack` — test quote form end-to-end via CloudFront
- [ ] Honeypot test: submit with `middle_name` filled → 200, no SES call in logs

---

## Stack 3 — Email (SES)
**CDK file:** `cdk/lib/email-stack.ts`

### Phase A — Console
- [x] Create SES email identity for `the-canada-movers.com`
- [x] Add 3 DKIM CNAMEs to DNS registrar
- [x] Add SPF TXT: `v=spf1 include:amazonses.com ~all`
- [x] Add DMARC TXT: `v=DMARC1; p=none; rua=mailto:thecanadamovers@gmail.com` (start with `p=none` monitor-only, tighten to `quarantine` later once DKIM+SPF confirmed passing)
- [x] Wait for domain identity to go green in SES console
- [x] Add `ses:SendEmail` inline policy to Lambda execution role
- [ ] Re-run Lambda test → email arrives at `thecanadamovers@gmail.com`
- [ ] Submit AWS Support case to exit SES sandbox

### Phase B — CDK
- [ ] Write `cdk/lib/email-stack.ts` (EmailIdentity + CfnOutput for DKIM records)
- [ ] Update `ApiStack` to accept SES identity ARN prop + grant `ses:SendEmail`
- [ ] `cdk deploy EmailStack ApiStack`
- [ ] End-to-end: fill quote wizard → email arrives

---

## Stack 4 — DNS (Route 53 + Custom Domain)

### Phase A — Console
- [ ] Create Route 53 hosted zone for `the-canada-movers.com`
- [ ] Update registrar NS records to Route 53 nameservers (or transfer domain)
- [ ] Add ACM validation CNAME → cert turns green
- [ ] Add 3 DKIM CNAMEs
- [ ] Create ALIAS A record: `the-canada-movers.com` → CloudFront distribution
- [ ] Create CNAME: `www.the-canada-movers.com` → CloudFront domain
- [ ] Verify: `curl -I https://the-canada-movers.com` returns 200 + `x-cache: Hit from cloudfront`

### Phase B — CDK (optional)
- [ ] Add Route 53 ALIAS + CNAME records in CDK for automation practice

---

## Stack 5 — DevOps & Observability
*No CDK phase — console + CLI work.*

- [ ] Set $5/month budget alert in AWS Budgets
- [ ] Create CloudWatch Alarm: Lambda `Errors` > 0 → SNS → email
- [ ] Run `cdk deploy --all` — observe stack dependency order
- [ ] Run `cdk diff` after a small change, confirm output before applying
- [ ] Replace `REPLACE_WITH_SITE_KEY` in `index.html` with real Cloudflare Turnstile key
- [ ] Check `mail-tester.com` — aim for 10/10

---

## Final Verification Checklist

- [ ] `https://the-canada-movers.com` loads (CloudFront + S3)
- [ ] Direct S3 URL returns 403
- [ ] SSL cert valid for `the-canada-movers.com`
- [ ] Quote wizard → email at `thecanadamovers@gmail.com` + client auto-confirm
- [ ] Honeypot: `middle_name` filled → 200, no email
- [ ] DKIM/SPF/DMARC: 10/10 on mail-tester.com
- [ ] Turnstile site key active
- [ ] CloudWatch alarm configured
- [ ] $5/month budget alert set
- [ ] SES sandbox exit request submitted

---

## Progress Log

| Date | Milestone |
|------|-----------|
| — | *(log entries will be added here as stacks are completed)* |
