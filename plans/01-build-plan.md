# The Canada Movers — Build Plan
## AWS CDK (TypeScript) + Vanilla JS SPA + Python 3.12 Lambda

---

## Phase 0: Documentation Discovery — COMPLETE ✅

### Allowed APIs (confirmed from CDK v2 docs)

| Concern | Package | Key Class |
|---|---|---|
| S3 | `aws-cdk-lib/aws-s3` | `Bucket`, `BlockPublicAccess` |
| CloudFront | `aws-cdk-lib/aws-cloudfront` | `Distribution`, `S3OriginAccessControl` |
| S3 OAC origin | `aws-cdk-lib/aws-cloudfront-origins` | `S3BucketOrigin.withOriginAccessControl()` |
| ACM cert | `aws-cdk-lib/aws-certificatemanager` | `Certificate`, `CertificateValidation` |
| S3 Deploy | `aws-cdk-lib/aws-s3-deployment` | `BucketDeployment`, `Source.asset()` |
| HTTP API | `aws-cdk-lib/aws-apigatewayv2` | `HttpApi`, `CorsHttpMethod`, `HttpMethod` |
| Lambda integration | `aws-cdk-lib/aws-apigatewayv2-integrations` | `HttpLambdaIntegration` |
| Python Lambda | `@aws-cdk/aws-lambda-python-alpha` (npm install separately) | `PythonFunction` |
| SES | `aws-cdk-lib/aws-ses` | `EmailIdentity`, `Identity` |
| IAM | `aws-cdk-lib/aws-iam` | `PolicyStatement` |

### Anti-patterns to avoid
- **DO NOT** use `S3Origin` — it uses legacy OAI. Use `S3BucketOrigin.withOriginAccessControl()`.
- **DO NOT** use `DnsValidatedCertificate` — deprecated. Use `Certificate` with `CertificateValidation.fromDns()`.
- **DO NOT** enable `websiteIndexDocument` on S3 bucket — OAC requires REST endpoint, not website endpoint.
- **DO NOT** use `@aws-cdk/aws-apigatewayv2-alpha` — merged into `aws-cdk-lib` stable.
- **DO NOT** use `requests` in Lambda — use `urllib.request` (stdlib) for Turnstile to avoid Lambda layers.
- ACM cert **MUST** be in `us-east-1` for CloudFront — even if all other resources are in `ca-central-1`.

---

## Phase 1: Project Scaffold

### Goal
Initialize the monorepo structure and CDK app.

### Tasks

1. Create directory structure:
```
thecanadamovers/
├── cdk/
├── frontend/
│   ├── assets/        (placeholder — client provides WebP images)
│   ├── css/
│   └── js/
├── lambda/
│   ├── handler.py
│   └── requirements.txt
├── plans/
├── BRD.md
└── CLAUDE.md
```

2. Initialize CDK app inside `cdk/`:
```bash
cd cdk && npx cdk init app --language typescript
```

3. Install CDK dependencies:
```bash
cd cdk && npm install @aws-cdk/aws-lambda-python-alpha
```

4. Configure `cdk/cdk.json`:
```json
{
  "app": "npx ts-node --prefer-ts-exts bin/app.ts",
  "context": {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "domainName": "the-canada-movers.com",
    "recipientEmail": "thecanadamovers@gmail.com",
    "senderEmail": "noreply@the-canada-movers.com"
  }
}
```

5. Initialize git:
```bash
git init && git add . && git commit -m "chore: initial scaffold"
```

### Verification
- `cdk synth` runs without errors from `cdk/`
- Directory structure matches above

---

## Phase 1.5: Local Testing & CI Preview

### Goal
Enable full-stack local development (Docker Compose + nginx proxy + mock API) and visual client preview (GitHub Pages via GitHub Actions). No AWS credentials required for local dev.

### Directory additions

```
thecanadamovers/
├── docker/
│   ├── nginx.conf            # nginx proxy config for local dev
│   └── mock-api/
│       ├── Dockerfile
│       └── mock_api.py       # Python stdlib HTTP server, returns {"ok":true}
├── .github/
│   └── workflows/
│       └── pages.yml         # Deploy frontend/ to GitHub Pages on push to main
├── frontend/
│   └── js/
│       └── config.js         # API endpoint config (overwritten per environment)
└── Makefile                  # Convenience targets: dev, serve, sam-local
```

### How it works

```
Browser (localhost:3000)
  │
  └── nginx (docker)
        ├── GET /*       → serves frontend/ files
        └── POST /quote  → proxies to mock-api:3001
                                └── returns {"ok": true} (no SES, no AWS)
```

Frontend JS always calls `/quote` (relative URL). nginx routes it locally; API Gateway handles it in production. No code change between environments — only `config.js` changes.

### config.js pattern

`frontend/js/config.js` is the single environment switch:

```javascript
// Default: local mock via nginx proxy
window.CONFIG = {
  API_ENDPOINT: '/quote',
  ENV: 'local'
};
```

| Environment | API_ENDPOINT value |
|---|---|
| Local (Docker) | `/quote` (nginx proxies to mock-api) |
| GitHub Pages preview | Full API Gateway URL (injected by GitHub Actions) |
| Production (CloudFront) | Full API Gateway URL (injected by CDK BucketDeployment) |

### Files to create

#### `docker-compose.yml`
```yaml
services:
  frontend:
    image: nginx:alpine
    ports:
      - "3000:80"
    volumes:
      - ./frontend:/usr/share/nginx/html:ro
      - ./docker/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - mock-api

  mock-api:
    build:
      context: ./docker/mock-api
    expose:
      - "3001"
    environment:
      - PORT=3001
```

#### `docker/nginx.conf`
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location /quote {
        proxy_pass http://mock-api:3001;
        proxy_set_header Content-Type application/json;
        add_header Access-Control-Allow-Origin *;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

#### `docker/mock-api/mock_api.py`
```python
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import os

class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        print(f"[mock-api] received: {body.decode()}")

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'ok': True}).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[mock-api] {format % args}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    print(f"[mock-api] listening on :{port}")
    HTTPServer(('', port), MockHandler).serve_forever()
```

#### `docker/mock-api/Dockerfile`
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY mock_api.py .
CMD ["python", "mock_api.py"]
```

#### `.github/workflows/pages.yml`
```yaml
name: Deploy Preview to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Inject API endpoint
        run: |
          cat > frontend/js/config.js << 'EOF'
          window.CONFIG = {
            API_ENDPOINT: '${{ vars.API_ENDPOINT }}',
            ENV: 'preview'
          };
          EOF

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend
          cname: ''   # leave empty unless using custom domain for preview
```

Set `API_ENDPOINT` in GitHub repo → Settings → Variables → Actions → New repository variable.

#### `Makefile`
```makefile
.PHONY: dev serve sam-local clean

dev:                          ## Full stack: nginx + mock API via Docker Compose
	docker compose up --build

serve:                        ## Frontend only (no backend needed)
	npx serve frontend/ -l 3000

sam-local:                    ## Real Lambda via SAM (requires Docker + AWS CDK synth)
	cd cdk && cdk synth --no-staging > ../template.yaml
	sam local start-api --template template.yaml --port 3001 &
	npx serve frontend/ -l 3000

clean:
	docker compose down --volumes --remove-orphans
	rm -f template.yaml
```

### SAM local alternative (real Lambda, no mock)

For testing the actual Python handler locally before deploy:
```bash
make sam-local
```

This runs `cdk synth` to generate `template.yaml`, then SAM pulls the Lambda Docker image and serves the real handler at `localhost:3001/quote`. Update `frontend/js/config.js` to `API_ENDPOINT: 'http://localhost:3001/quote'` temporarily.

### Verification
- `docker compose up` → `http://localhost:3000` loads the site
- POST to `http://localhost:3000/quote` via DevTools → response `{"ok": true}` logged by mock-api
- Push to `main` → GitHub Actions deploys to `https://<user>.github.io/<repo>/`
- GitHub Pages URL loads the frontend with correct API endpoint injected

---

## Phase 2: StaticSiteStack — S3 + CloudFront + ACM

### Goal
Private S3 bucket served via CloudFront with OAC and HTTPS on `the-canada-movers.com`.

### Key pattern (from docs)
```typescript
// cdk/lib/static-site-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as path from 'path';

// Stack MUST be deployed to us-east-1 (ACM + CloudFront requirement)
// env: { region: 'us-east-1' }

const bucket = new s3.Bucket(this, 'FrontendBucket', {
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
  encryption: s3.BucketEncryption.S3_MANAGED,
  enforceSSL: true,
  removalPolicy: cdk.RemovalPolicy.RETAIN,
  // NO websiteIndexDocument — OAC requires REST endpoint
});

const hostedZone = route53.HostedZone.fromLookup(this, 'Zone', {
  domainName: 'the-canada-movers.com',
});

const cert = new acm.Certificate(this, 'Cert', {
  domainName: 'the-canada-movers.com',
  subjectAlternativeNames: ['www.the-canada-movers.com'],
  validation: acm.CertificateValidation.fromDns(hostedZone),
});

const distribution = new cloudfront.Distribution(this, 'Distribution', {
  defaultBehavior: {
    origin: origins.S3BucketOrigin.withOriginAccessControl(bucket),
    viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
    cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
  },
  defaultRootObject: 'index.html',
  certificate: cert,
  domainNames: ['the-canada-movers.com', 'www.the-canada-movers.com'],
  errorResponses: [
    // SPA fallback — serve index.html for all 403/404
    { httpStatus: 403, responseHttpStatus: 200, responsePagePath: '/index.html' },
    { httpStatus: 404, responseHttpStatus: 200, responsePagePath: '/index.html' },
  ],
});

new s3deploy.BucketDeployment(this, 'DeployFrontend', {
  sources: [s3deploy.Source.asset(path.join(__dirname, '../../frontend'))],
  destinationBucket: bucket,
  distribution,
  distributionPaths: ['/*'],
});
```

### Gotchas
- Pin this stack's `env.region` to `us-east-1` — cert + CloudFront both require it.
- `HostedZone.fromLookup()` requires AWS credentials at `cdk synth` time (context lookup). If Route 53 is NOT used, import cert ARN manually via `Certificate.fromCertificateArn()` and remove Route 53 dependency.
- `S3BucketOrigin.withOriginAccessControl()` auto-creates the S3 bucket policy — do not add `bucket.grantRead()` manually.

### Outputs
- `CfnOutput`: CloudFront distribution URL
- `CfnOutput`: S3 bucket name

### Verification
- `cdk synth` produces a valid CloudFormation template
- CloudFront URL serves `index.html` (even a placeholder) over HTTPS
- HTTP redirects to HTTPS

---

## Phase 3: EmailStack — SES Domain Identity

### Goal
Register `the-canada-movers.com` as an SES sending identity and output DKIM records.

### Key pattern (from docs)
```typescript
// cdk/lib/email-stack.ts
import * as ses from 'aws-cdk-lib/aws-ses';
import { CfnOutput } from 'aws-cdk-lib';

const emailIdentity = new ses.EmailIdentity(this, 'SesIdentity', {
  identity: ses.Identity.domain('the-canada-movers.com'),
  dkimSigning: true,
  mailFromDomain: 'mail.the-canada-movers.com',
  mailFromBehaviorOnMxFailure: ses.MailFromBehaviorOnMxFailure.REJECT_MESSAGE,
});

// Export all 3 DKIM CNAME pairs for DNS configuration
new CfnOutput(this, 'DkimName1',  { value: emailIdentity.dkimDnsTokenName1 });
new CfnOutput(this, 'DkimValue1', { value: emailIdentity.dkimDnsTokenValue1 });
new CfnOutput(this, 'DkimName2',  { value: emailIdentity.dkimDnsTokenName2 });
new CfnOutput(this, 'DkimValue2', { value: emailIdentity.dkimDnsTokenValue2 });
new CfnOutput(this, 'DkimName3',  { value: emailIdentity.dkimDnsTokenName3 });
new CfnOutput(this, 'DkimValue3', { value: emailIdentity.dkimDnsTokenValue3 });
```

### Post-deploy DNS records (add manually to Cloudflare)
| Type | Name | Value |
|---|---|---|
| CNAME | `<DkimName1>` | `<DkimValue1>` |
| CNAME | `<DkimName2>` | `<DkimValue2>` |
| CNAME | `<DkimName3>` | `<DkimValue3>` |
| MX | `mail.the-canada-movers.com` | `feedback-smtp.us-east-1.amazonses.com` (priority 10) |
| TXT | `mail.the-canada-movers.com` | `"v=spf1 include:amazonses.com ~all"` |
| TXT | `the-canada-movers.com` | `"v=DMARC1; p=quarantine; rua=mailto:thecanadamovers@gmail.com"` |

### Gotchas
- New AWS accounts are in SES sandbox — only verified addresses can receive email until production access is requested via AWS Support.
- SES region: use `us-east-1` or `ca-central-1`. Lambda's `boto3.client('ses')` region must match the stack region.
- Export `emailIdentity` from this stack so `ApiStack` can call `emailIdentity.grantSendEmail(fn)`.

### Verification
- Stack deploys without error
- DKIM names/values appear in CloudFormation outputs
- After DNS records are added: SES console shows identity as "Verified"

---

## Phase 4: ApiStack — API Gateway v2 + Lambda

### Goal
HTTP API with a single `POST /quote` route backed by a Python 3.12 Lambda. CORS locked to `the-canada-movers.com`.

### Key pattern (from docs)
```typescript
// cdk/lib/api-stack.ts
import * as apigwv2 from 'aws-cdk-lib/aws-apigatewayv2';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import * as python from '@aws-cdk/aws-lambda-python-alpha';
import { Runtime, Architecture } from 'aws-cdk-lib/aws-lambda';
import { Duration, CfnOutput } from 'aws-cdk-lib';
import * as path from 'path';

const quoteFn = new python.PythonFunction(this, 'QuoteFunction', {
  entry: path.join(__dirname, '../../lambda'),  // dir with handler.py + requirements.txt
  runtime: Runtime.PYTHON_3_12,
  index: 'handler.py',
  handler: 'handler',
  timeout: Duration.seconds(29),  // API GW max is 29s
  environment: {
    RECIPIENT_EMAIL: 'thecanadamovers@gmail.com',
    SENDER_EMAIL:    'noreply@the-canada-movers.com',
    SES_REGION:      'us-east-1',
    TURNSTILE_SECRET_KEY: '{{SET VIA SSM OR ENV}}',  // see gotchas
  },
});

// Grant Lambda permission to send SES email (imported from EmailStack)
emailIdentity.grantSendEmail(quoteFn);

const httpApi = new apigwv2.HttpApi(this, 'QuoteApi', {
  corsPreflight: {
    allowOrigins: ['https://the-canada-movers.com', 'https://www.the-canada-movers.com'],
    allowMethods: [apigwv2.CorsHttpMethod.POST, apigwv2.CorsHttpMethod.OPTIONS],
    allowHeaders: ['Content-Type'],
    maxAge: Duration.days(1),
  },
});

httpApi.addRoutes({
  path: '/quote',
  methods: [apigwv2.HttpMethod.POST],
  integration: new HttpLambdaIntegration('QuoteIntegration', quoteFn),
});

new CfnOutput(this, 'ApiEndpoint', { value: httpApi.apiEndpoint });
```

### Gotchas
- `PythonFunction` requires Docker running at `cdk synth`/`cdk deploy` time.
- `TURNSTILE_SECRET_KEY` must NOT be hardcoded. Use AWS SSM Parameter Store or Secrets Manager. Reference: `ssm.StringParameter.valueForStringParameter(this, '/tcm/turnstile-secret')`.
- HTTP API v2 uses payload format version 2.0 by default. Lambda handler must return `{ statusCode, body }` — body must be a JSON string, not an object.
- Lambda timeout max for HTTP API is 29 seconds. Set `timeout: Duration.seconds(29)`.

### Verification
- `curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/quote -H "Content-Type: application/json" -d '{"test":true}'` returns a response (even an error).
- CORS preflight `OPTIONS /quote` returns `Access-Control-Allow-Origin: https://the-canada-movers.com`.

---

## Phase 5: Lambda Handler — Python 3.12

### Goal
Security pipeline + SES email send. File: `lambda/handler.py`.

### Pipeline order (must execute in this sequence)
1. Parse JSON body
2. Check honeypot field (`middle_name` — if non-empty, return 200 silently)
3. Verify Cloudflare Turnstile token (via `urllib.request` — no `requests` dependency)
4. Validate required fields (name, email, phone, services)
5. Regex validate email and phone
6. Max-length enforce all string fields (name: 100, email: 254, phone: 20, instructions: 2000)
7. XSS escape all text (use `html.escape()` from stdlib)
8. Build and send lead email to `thecanadamovers@gmail.com`
9. Send auto-confirm email to client

### Requirements.txt
```
# lambda/requirements.txt
# boto3 is provided by Lambda runtime — do not include
# Use stdlib urllib.request for Turnstile — no requests needed
```
(Empty or nearly empty — use stdlib only to minimize cold start and avoid layers.)

### Key snippets (from docs)

**Turnstile verification (no dependencies):**
```python
import urllib.request, urllib.parse, json, os, html, re

def verify_turnstile(token: str, remote_ip: str = None) -> bool:
    payload = urllib.parse.urlencode({
        'secret': os.environ['TURNSTILE_SECRET_KEY'],
        'response': token,
        **({'remoteip': remote_ip} if remote_ip else {}),
    }).encode()
    req = urllib.request.Request(
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
        data=payload, method='POST'
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read()).get('success', False)
```

**SES send (boto3 — runtime-provided):**
```python
import boto3
ses = boto3.client('ses', region_name=os.environ['SES_REGION'])

ses.send_email(
    Source=os.environ['SENDER_EMAIL'],
    Destination={'ToAddresses': [os.environ['RECIPIENT_EMAIL']]},
    Message={
        'Subject': {'Data': f'New Quote Request — {name}', 'Charset': 'UTF-8'},
        'Body': {
            'Text': {'Data': body_text, 'Charset': 'UTF-8'},
            'Html': {'Data': body_html, 'Charset': 'UTF-8'},
        },
    },
)
```

**HTTP API v2 response format:**
```python
return {
    'statusCode': 200,
    'headers': {'Content-Type': 'application/json'},
    'body': json.dumps({'ok': True}),
}
```

### Validation rules
| Field | Max length | Regex |
|---|---|---|
| email | 254 | `^[^@\s]+@[^@\s]+\.[^@\s]+$` |
| phone | 20 | `^[\d\s\+\-\(\)\.]{7,20}$` |
| postal_code | 7 | `^[A-Za-z]\d[A-Za-z][\s-]?\d[A-Za-z]\d$` |
| name | 100 | non-empty |
| instructions | 2000 | any |

### Verification
- Unit test: honeypot-filled body returns 200 with `{"ok": true}` and sends NO email.
- Unit test: missing required field returns 400.
- Unit test: invalid email format returns 400.
- Integration test: valid payload triggers SES send (use SES sandbox with verified test email).

---

## Phase 6: Frontend Shell — HTML + CSS

### Goal
Single `frontend/index.html` with all 9 sections in BRD order. No JS framework.

### Section checklist (in order)
- [ ] `<header>` — sticky, logo left, red phone CTA right
- [ ] `<section id="hero">` — headline, subheadline, 2 CTAs
- [ ] `<section id="gallery">` — carousel placeholder (images client-supplied)
- [ ] `<section id="services">` — 8 service cards in CSS grid
- [ ] `<section id="reviews">` — static testimonial cards + schema.org markup
- [ ] `<section id="quote">` — 4-slide wizard container
- [ ] `<section id="faq">` — accordion + dos/don'ts grid
- [ ] `<section id="about">` — dense semantic `<address>` + `<article>` block
- [ ] `<footer>` — copyright, address, email, phone, payment icons

### CSS constraints
- CSS custom properties for palette: `--red: #D52B1E; --black: #222; --white: #fff`
- Mobile-first media queries
- No CSS framework (Tailwind/Bootstrap add weight — stay under 3MB total)
- Font: System font stack or single Google Font weight (preconnect + display=swap)

### SEO requirements (every section)
- Semantic HTML: `<main>`, `<section>`, `<article>`, `<address>`, `<nav>`
- All images: `alt` text, `loading="lazy"`, `width`/`height` attributes
- Reviews: `<script type="application/ld+json">` with `schema.org/Review`
- FAQ: structured data with `schema.org/FAQPage`
- Business: `schema.org/LocalBusiness` in `<head>`

### Verification
- HTML validates (W3C validator or `npx html-validate`)
- All 9 sections present with correct `id` attributes
- No inline styles (all in `css/style.css`)
- `lighthouse --view` (or PageSpeed Insights) on placeholder page scores structure

---

## Phase 7: Frontend — Interactive Components (Vanilla JS)

### Goal
Image carousel + 4-slide quote wizard + form submission. File: `frontend/js/main.js`.

### Carousel
- Touch/swipe support via `touchstart`/`touchend` delta calculation
- Auto-advance with pause on hover
- Lazy load images as they enter viewport (`IntersectionObserver`)
- No third-party carousel library

### 4-Slide Quote Wizard

State machine — `currentSlide` (0–3), `formState` object accumulating inputs.

```
Slide 0: Services checkboxes
  → validate: at least 1 selected
Slide 1: Dynamic details (conditional fields based on Slide 0 selections)
  → validate: required conditionals filled
Slide 2: Route (Origin + Destination city + postal code)
  → validate: all 4 fields non-empty, postal codes match Canadian format
Slide 3: Contact + date + submit
  → validate: name, email, phone required; date >= today
  → submit: POST JSON to API endpoint
```

Conditional logic for Slide 1:
```javascript
const hasHousehold = services.includes('household') || services.includes('office');
const hasPoolTable = services.includes('pool-table');
const hasHeavy = ['piano','pool-table','fitness','fish-tank','vending'].some(s => services.includes(s));
```

### Form submission
```javascript
const response = await fetch(API_ENDPOINT, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    services, details, origin, destination, contact,
    'cf-turnstile-response': document.querySelector('[name=cf-turnstile-response]').value,
    middle_name: document.querySelector('[name=middle_name]').value, // honeypot
  }),
});
```

### Honeypot field (in HTML)
```html
<!-- Honeypot: hidden from humans, visible to bots -->
<div style="position:absolute;left:-9999px;top:-9999px;width:1px;height:1px;overflow:hidden">
  <label for="middle_name">Leave this empty</label>
  <input type="text" name="middle_name" id="middle_name" tabindex="-1" autocomplete="off">
</div>
```

Note: Use CSS positioning, NOT `display:none` or `visibility:hidden` — bots skip those.

### Verification
- Carousel swipes on mobile (Chrome DevTools touch emulation)
- Slide 1 shows/hides conditional fields based on Slide 0 selections
- Slide validation blocks "Next" when fields are empty
- Form POST reaches Lambda (check CloudWatch logs)
- Both SES emails arrive (lead to business, confirm to test email)

---

## Phase 8: Cloudflare Turnstile + SEO Final Pass

### Goal
Wire Turnstile widget, complete schema.org markup, final PageSpeed audit.

### Turnstile integration (frontend)
```html
<!-- In <head> -->
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>

<!-- In form, Slide 3 or wrapping the submit button -->
<div class="cf-turnstile" data-sitekey="YOUR_SITE_KEY" data-theme="light"></div>
```

Get site key + secret key from Cloudflare Dashboard → Turnstile. Site key goes in HTML (public). Secret key goes in SSM Parameter Store (never in code).

### Schema.org markup blocks
```html
<!-- LocalBusiness in <head> -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "MovingCompany",
  "name": "The Canada Movers",
  "telephone": "+16478850450",
  "email": "thecanadamovers@gmail.com",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "301-3 Goldfinch Ct",
    "addressLocality": "Toronto",
    "addressRegion": "ON",
    "postalCode": "M2R2C2",
    "addressCountry": "CA"
  },
  "areaServed": ["Toronto", "GTA", "Ontario", "Canada", "United States"],
  "priceRange": "$$"
}
</script>

<!-- FAQPage -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [ ... ]
}
</script>
```

### Verification
- Google Rich Results Test passes for LocalBusiness + FAQPage + Review
- Lighthouse mobile score ≥ 95 (target 100)
- Total page weight < 3MB (check Network tab with images loaded)
- `<html lang="en-CA">` set

---

## Phase 9: Deployment & DNS Configuration

### Deploy order
```bash
cd cdk

# 1. Bootstrap (first time only)
cdk bootstrap aws://ACCOUNT_ID/us-east-1

# 2. Deploy all stacks
cdk deploy --all

# 3. Note outputs:
#    - CloudFront distribution domain
#    - API Gateway endpoint
#    - DKIM CNAME records (3 pairs)
```

### DNS records to add in Cloudflare (after deploy)
| Type | Name | Value | Proxy |
|---|---|---|---|
| CNAME | `the-canada-movers.com` | `<cloudfront-domain>.cloudfront.net` | OFF (DNS only) |
| CNAME | `www` | `<cloudfront-domain>.cloudfront.net` | OFF |
| CNAME | `<dkim1>._domainkey` | `<dkim1-value>` | OFF |
| CNAME | `<dkim2>._domainkey` | `<dkim2-value>` | OFF |
| CNAME | `<dkim3>._domainkey` | `<dkim3-value>` | OFF |
| MX | `mail` | `feedback-smtp.us-east-1.amazonses.com` (10) | OFF |
| TXT | `mail` | `"v=spf1 include:amazonses.com ~all"` | — |
| TXT | `@` | `"v=DMARC1; p=quarantine; rua=mailto:thecanadamovers@gmail.com"` | — |

### SES sandbox exit
File AWS Support ticket: "Request production SES access for domain the-canada-movers.com". Required before real users can receive auto-confirm emails.

### API endpoint in frontend
After deploy, set the API Gateway URL in `frontend/js/main.js`:
```javascript
const API_ENDPOINT = 'https://<api-id>.execute-api.us-east-1.amazonaws.com/quote';
```
Or inject it via `BucketDeployment` substitution / a generated `config.js`.

### Verification
- `https://the-canada-movers.com` loads over HTTPS with no cert warnings
- `https://www.the-canada-movers.com` redirects correctly
- SES identity shows "Verified" in AWS console
- DMARC/SPF/DKIM pass: check via `mail-tester.com` or `mxtoolbox.com`

---

## Phase 10: Final Verification

### Checklist
- [ ] PageSpeed Insights mobile score ≥ 95 on live URL
- [ ] Total page weight < 3MB
- [ ] End-to-end form submission: lead email arrives at `thecanadamovers@gmail.com`
- [ ] Auto-confirm email arrives at test address
- [ ] Honeypot: POST with `middle_name` filled → no email sent, 200 response
- [ ] Turnstile: POST without valid token → 400 response
- [ ] CORS: POST from `evil.com` → blocked by API Gateway
- [ ] Mobile carousel swipe works (iOS Safari + Android Chrome)
- [ ] All 8 service cards render correctly at 375px width
- [ ] 4-slide wizard conditional fields show/hide correctly
- [ ] Back/Next validation blocks progress on empty required fields
- [ ] `https://` forced (no HTTP access)
- [ ] Rich Results Test passes for LocalBusiness, FAQPage
- [ ] Lighthouse accessibility score ≥ 90
