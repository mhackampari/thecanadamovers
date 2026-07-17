# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**The Canada Movers** — a serverless, single-page marketing and lead-capture site for a Toronto-based specialized moving company. Target: $0/month hosting via AWS Free Tier. Target PageSpeed: 100/100 mobile.

**Live domain:** `the-canada-movers.com`  
**Contact:** `thecanadamovers@gmail.com` | `1-647-885-0450`  
**Address:** `301-3 Goldfinch Ct, Toronto ON M2R2C2`

---

## Architecture

```
Browser
 ├── GET  → S3 + CloudFront (static HTML/CSS/JS)
 └── POST → API Gateway (CORS: the-canada-movers.com only)
                └── Lambda (Python 3.12)
                        ├── Honeypot + Turnstile check
                        ├── XSS sanitization + regex validation
                        └── SES → thecanadamovers@gmail.com + client auto-confirm
```

No databases. No servers. All lead data flows through SES email only.

---

## Key Constraints

- **Total page size must stay under 3MB** (100/100 Mobile PageSpeed requirement).
- **No SQL/RDS/DynamoDB** — out of scope for Phase 1.
- **No Google Maps API** on the frontend — route data collected as plain text, estimated manually.
- **Images:** WebP format only, lazy-loaded. Client provides source images.
- **CORS:** API Gateway must only accept requests from `https://the-canada-movers.com` and its subdomains.

---

## Frontend Structure

Single HTML page. No framework required — vanilla JS or lightweight bundler (Vite) acceptable.

### Page Section Order
1. **Header** — Logo left, red click-to-call CTA right (`📞 1-647-885-0450`)
2. **Hero** — Headline + two CTAs: `[Call Now]` (red solid) and `[Get a Quote Online]` (white/red border, scrolls to form)
3. **Image Carousel** — Horizontal swipeable WebP gallery, lazy-loaded
4. **Services Grid** — 8 blocks: Piano, Pool Table + Refurbishing, Fitness Equipment, Fish Tanks, Long Distance (Canada & US), Household, Office, Vending Machines
5. **Reviews** — Static Google/Homestars testimonial cards with `schema.org/Review` markup, linked to live platforms
6. **Quote Wizard** — 4-slide horizontal form (see below)
7. **FAQ & Dos/Don'ts** — Accordion FAQ + high-contrast pre-move checklist grid
8. **About Us** — Dense semantic text block for AI agent crawling (address, values, Toronto base)
9. **Footer** — Copyright, address, email, phone

### Color Palette
| Role | Value |
|---|---|
| Primary (60%) | White |
| Secondary (30%) | Charcoal Black |
| Accent (10%) | Canadian Red |

---

## 4-Slide Quote Wizard Logic

**Slide 1 — Services:** Multi-checkbox service selection.

**Slide 2 — Dynamic Details** (conditional on Slide 1):
- Household/Office selected → box count dropdown (1-10, 10-30, 30-50, 50+)
- Pool Table selected → checkbox for refurbishing add-on
- Heavy items selected (Piano/Pool Table/Fitness/Fish Tank/Vending) → number of heavy items + stair checkbox → if stairs, text field for flights/steps

**Slide 3 — Route:** Origin City + Postal Code, Destination City + Postal Code.

**Slide 4 — Contact:** Native date picker, Name, Email, Phone, Special Instructions. Submit → JSON POST to API Gateway.

**Navigation rules:** Back/Next buttons. Validate inputs before advancing slides.

---

## Backend (Lambda — Python 3.12)

Security pipeline (in order):
1. Honeypot field check (`middle_name` — if filled, silently drop)
2. Cloudflare Turnstile token verification
3. XSS escape all text fields
4. Regex validation on phone and email
5. Max-length enforcement on all strings
6. SES send: lead email to `thecanadamovers@gmail.com` + auto-confirm to client

---

## Security Requirements

- `middle_name` honeypot field — hidden via CSS, never via `display:none` or `visibility:hidden` (bots read those)
- Cloudflare Turnstile (invisible, zero-cost)
- API Gateway CORS locked to `the-canada-movers.com`
- SES domain: SPF, DKIM, DMARC must be configured on `the-canada-movers.com`

---

## SEO & AI Agent Readiness

- All content must use semantic HTML (`<article>`, `<section>`, `<address>`, etc.)
- Reviews marked up with `schema.org/Review`
- About Us block must include full address, phone, email, service area as plain readable text
- FAQs structured for featured-snippet capture
- No JavaScript-rendered content for primary copy (must be in raw HTML for crawlers)

---

## IaC: AWS CDK (TypeScript)

All infrastructure is defined and deployed via AWS CDK. CDK language: **TypeScript**. Lambda runtime: **Python 3.12**.

### Repository Layout

```
thecanadamovers/
├── cdk/                          # CDK app (TypeScript)
│   ├── bin/app.ts                # CDK entry point
│   ├── lib/
│   │   ├── static-site-stack.ts  # S3 bucket + CloudFront + ACM + S3Deploy
│   │   ├── api-stack.ts          # API Gateway (HTTP API) + Lambda
│   │   └── email-stack.ts        # SES identity + DKIM config
│   ├── cdk.json
│   └── package.json
├── frontend/                     # Static site source
│   ├── index.html
│   ├── css/style.css
│   ├── js/main.js
│   └── assets/                   # WebP images (client-supplied)
├── lambda/                       # Python 3.12 Lambda
│   ├── handler.py
│   └── requirements.txt
└── BRD.md
```

### CDK Stacks

| Stack | Constructs |
|---|---|
| `StaticSiteStack` | `aws_s3`, `aws_s3_deployment`, `aws_cloudfront`, `aws_cloudfront_origins`, `aws_certificatemanager` |
| `ApiStack` | `aws_apigatewayv2` (HTTP API), `aws_lambda`, `aws_lambda_python_alpha` (or bundling) |
| `EmailStack` | `aws_ses` (EmailIdentity, DkimRecord) |

Use **HTTP API** (API Gateway v2) — cheaper than REST API, sufficient for a single POST endpoint.

### CDK Deploy Commands

```bash
cd cdk
npm install
cdk bootstrap          # first time only, per account/region
cdk synth              # preview CloudFormation template
cdk deploy --all       # deploy all stacks
cdk diff               # preview changes before deploy
```

### AWS Infrastructure (Free Tier)

| Service | Purpose | Free Tier Limit |
|---|---|---|
| S3 | Static file hosting | 5GB / 20K GET / 2K PUT |
| CloudFront | CDN + HTTPS | 1TB transfer / 10M req (12 mo) |
| API Gateway v2 | HTTPS POST endpoint | 1M calls/mo (12 mo) |
| Lambda | Python form handler | 1M req/mo + 400K GB-sec |
| SES | Email delivery | 3,000 msg/day |
| ACM | Free SSL cert | Free with CloudFront |
| Route 53 | DNS (optional) | ~$0.50/hosted zone |

---

## Business Context

Services offered: Piano Moving, Pool Table Moving & Refurbishing, Fitness Equipment, Large Fish Tanks, Long Distance (Canada & US), Household, Office, Vending Machines.

Target conversion: 15%+ on paid ad traffic via "Call Now" or "Get Quote" form submissions.
