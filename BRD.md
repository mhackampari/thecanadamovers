# Business Requirements Document (BRD)
## Project Name: The Canada Movers Web Platform

---

## 1. Executive Summary & Business Case
* **The Problem:** The Canada Movers currently manages quotes and customer inquiries through manual email and phone outreach. While highly effective, they lack a dedicated, search-engine-optimized, and conversion-optimized web presence to capture high-intent digital leads and organic searches for specialized moves.
* **The Solution:** A serverless, ultra-fast, single-page web platform showcasing specialized moving services, customer reviews, and an interactive 4-slide dynamic "Get Quote" form.
* **Value Proposition:** 100% serverless infrastructure resulting in **$0/month hosting fees** under the AWS Free Tier, combined with an optimized visual flow that maximizes phone calls and structured form leads.

---

## 2. Project Objectives & Success Metrics
* **Objective 1:** Position The Canada Movers as Toronto's premier specialized moving service (Pianos, Pool Tables + Refurbishing, Fitness Equipment, Fish Tanks, Vending Machines) for local, long-distance, and Canada-US relocations.
* **Objective 2:** Achieve a 100/100 Mobile PageSpeed score to minimize Google Ads click costs and maximize conversions.
* **Objective 3:** Ensure 100% of website content, FAQs, and company profiles are perfectly readable and highly structured for SEO and AI Search Agents (ChatGPT, Gemini, Perplexity).
* **Success Metric:** Capture 15%+ conversion rate on paid ad traffic through either direct "Call Now" clicks or "Get Quote" form submissions.

---

## 3. Scope of Work (In-Scope vs. Out-of-Scope)

### In-Scope (Phase 1)
* **Single-Page UI:** Fast-loading, responsive page with a professional Red, White, and Black aesthetic.
* **Specialized Services Grid:** Individual blocks with optimized copy for all 8 core specialties.
* **Sliding Gallery Carousel:** Horizontal, swipeable image carousel displaying real work, with images optimized in WebP format and lazy-loaded.
* **Social Proof Card Slider:** Hand-selected static reviews from Google Maps and Homestars, marked up with Schema.org `Review` tags and linked directly to live review platforms.
* **4-Slide Dynamic "Get Quote" Form:** Client-side slider capturing dynamic inventory and route data.
* **FAQ & Dos/Don'ts Section:** Expandable accordion FAQ list, plus a high-contrast grid listing pre-move dos and don'ts.
* **Serverless Backend (Python):** AWS Lambda endpoint triggered securely via AWS API Gateway to handle lead sanitization, XSS protection, spam prevention, and email notifications.

### Out-of-Scope (Strictly Excluded for Cost Control)
* **Live Databases:** No relational databases (SQL) or active servers to maintain 100% Free Tier status.
* **Automated Instant Pricing:** Leads will be collected and estimated manually by dispatchers to prevent operational pricing losses.
* **Paid Map APIs:** No Google Maps API distance calculations on the frontend (handled manually post-submission).

---

## 4. Brand Aesthetic & Page Layout Flow

### Visual & Color Scheme
* **Primary (60%):** White (Clean spacing, readable backgrounds).
* **Secondary (30%):** Charcoal Black (Sharp headings, body text, footer).
* **Accent (10%):** Canadian Red (Active CTAs, phone numbers, form highlights, and submit buttons).

### Layout Sequence
1. **Header / Navigation:** Persistent logo on left; prominent Red click-to-call CTA on the right: **📞 1-647-885-0450 (24/7 Support Line)**.
2. **Hero Section (Top Fold):** Strong headline, sub-headline, and two visual CTAs:
   * **[Call Now]** (Red solid button)
   * **[Get a Quote Online]** (White button with Red border — scrolls to Section 6).
3. **Sliding Picture Carousel:** Swipeable gallery of high-quality, WebP-compressed images showing trucks and specialized moving in action.
4. **Specialized Services Grid:** Highly detailed blocks detailing:
   * Piano Moving
   * Pool Table Moving & Refurbishing
   * Fitness Equipment Moving
   * Big Fish Tanks
   * Long Distance Moving (Canada & US)
   * Household Moving
   * Office Moving
   * Vending Machines
5. **Static Reviews Section:** High-converting Google & Homestars testimonial cards with verified external links.
6. **Dynamic "Get Quote" Section:** Horizontal 4-slide slide-in wizard (detailed in Section 5).
7. **FAQ and Dos & Don'ts Section:** Expandable accordions with comprehensive local moving FAQs and high-contrast tables listing pre-move checklists.
8. **Semantic About Us Block:** Highly detailed text block outlining company values, Toronto base of operations, and physical address: `301-3 Goldfinch Ct, Toronto ON M2R2C2`, optimized specifically for AI Agent crawling.
9. **Footer:** Copyright, address, contact email (`thecanadamovers@gmail.com`), and phone.

---

## 5. Functional Requirements (Form & Interactive Elements)

### FR-1: 4-Slide Dynamic Quote Wizard
* **Slide 1 [Services]:** User selects checkboxes for their moving needs.
* **Slide 2 [Dynamic Details]:**
  * *If Household/Office selected:* Display a dropdown/slider for **"Estimated number of boxes"** (Options: 1-10, 10-30, 30-50, 50+).
  * *If Pool Table selected:* Display checkbox **"Include Pool Table Refurbishing? (Felt replacement, bumpers, leveling, etc.)"**.
  * *If Heavy Items selected (Piano, Pool Table, Fitness, Fish Tank, Vending):* Display number field **"Number of heavy items"** and dynamic stair inputs:
    * Checkbox: *"Are there stairs involved?"*
    * If checked, display text field: **"Number of flights / steps"**.
* **Slide 3 [Route]:** Text fields capturing **Origin City & Postal Code** and **Destination City & Postal Code**.
* **Slide 4 [Contact & Timing]:** 
  * Native browser Date picker (FR-1.1).
  * Fields: Name, Email, Phone, and Special Instructions.
  * Submit Button: Submits via JSON payload to the API.

### FR-2: Form Navigation
* **FR-2.1:** Form must include clear **"Back"** and **"Next"** buttons to navigate slides.
* **FR-2.2:** User inputs must be validated on-the-fly before allowing progress to the next slide.

### FR-3: Security, XSS & Anti-Spam
* **FR-3.1 [Honeypot Field]:** The HTML form must contain an invisible field (e.g., `middle_name`) hidden with CSS. If filled out, the backend silently drops the submission as bot spam.
* **FR-3.2 [Cloudflare Turnstile]:** Integration of a zero-cost, invisible Turnstile widget to verify user legitimacy without slowing the page.
* **FR-3.3 [Backend Input Sanitization]:** Python Lambda function must escape all incoming text to prevent XSS, run strict Regex matching on phone/emails, and enforce maximum length properties on string text.
* **FR-3.4 [CORS Policy]:** AWS API Gateway must be strictly configured to only accept incoming requests from `https://thecanadamovers.ca` and its subdomains.

---

## 6. Technical Architecture & AWS Free Tier Alignment

```
[Web Browser] 
    │
    ├─── (GET Content) ───> [AWS S3 & CloudFront CDN] (Static Web Site - Red/White/Black Palette)
    │
    └─── (POST Form Submission JSON) ───> [AWS API Gateway (CORS Protected)]
                                                │
                                                └───> [AWS Lambda (Python 3.12)]
                                                            │
                                                            └─── (XSS Scan & Honeypot Check)
                                                            │
                                                            └─── (Send Lead & Auto-Confirm) ───> [AWS SES]
                                                                                                    ├───> thecanadamovers@gmail.com
                                                                                                    └───> Client Email
```

### Infrastructure Specifications
1. **Hosting:** AWS S3 + AWS CloudFront (CDN) for HTTPS secure delivery with zero server maintenance.
2. **Domain & DNS:** Managed via Route 53 or external registrar, utilizing AWS Certificate Manager (ACM) for free SSL.
3. **Backend API:** AWS API Gateway routing to a serverless **Python 3.12 Lambda function**.
4. **Email Notification:** AWS SES with Domain Verification (SPF, DKIM, DMARC DNS settings fully configured on `thecanadamovers.ca` to ensure high deliverability directly to Gmail and Client).

---

## 7. Assumptions & Constraints
* **Assumption 1:** The client has full access to the domain DNS panel of `thecanadamovers.ca` to configure SES and CloudFront CNAME records.
* **Assumption 2:** The client will provide optimized, high-quality images of their vehicles and specialized moves in WebP format.
* **Constraint 1:** No database storage will be used for Phase 1; SES email delivery is the sole mechanism of lead retrieval, demanding robust email configuration.
* **Constraint 2:** Page must remain under 3MB total size to maintain a 100/100 Mobile PageSpeed rank.
