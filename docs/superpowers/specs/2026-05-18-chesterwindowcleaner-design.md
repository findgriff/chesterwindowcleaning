# chesterwindowcleaner.co.uk — design spec

**Date:** 2026-05-18
**Status:** design approved, pending implementation plan
**Owner:** Craig Griffiths
**Project:** new website + lead-capture bot + lightweight CRM for a solo-trader window cleaning business in Chester, UK.

---

## 1. Objective

Ship a website that converts curious local visitors into captured leads (email + WhatsApp ping to the owner), prices most jobs instantly without a phone call, and tracks the resulting customers through a regular 6-weekly round.

The brand voice is "modern, clean, calm" — trustworthy local trade, not shouty discount. The site must work hard for the owner without ever feeling like a funnel.

### Operating context

- Solo trader. One person doing all the cleans.
- Starting from scratch — no existing customers, no Google reviews, no Google Business Profile.
- Service area: CH1–CH5 (Chester + Hoole, Boughton, Handbridge, Vicars Cross, Christleton, Upton, Newton, Saltney, Broughton, Hawarden, Queensferry, Connah's Quay).
- Method: pure water-fed pole only. No ladders, no chemicals.
- No public liability insurance (owner's decision; bot handles enquiries by deflecting to direct contact).
- Mobile-first — most window-cleaner customers search on phones.
- Local SEO matters more than national SEO.

### Pricing anchor (residential, 6-weekly)

| Property | Price |
|---|---|
| 3-bed semi | £20 |
| 4-bed semi | £22 |
| 3-bed detached | £25 |
| 4-bed detached | £30 |
| 5-bed detached | £36 |
| Town house / bespoke | POA (manual quote) |

Add-ons (midpoint of published ranges; bot quotes midpoint, page shows range):

| Add-on | Standard (≤3-bed) | Large (4+ bed) |
|---|---|---|
| Conservatory | £10 | £12.50 |
| Extension / 2+ side windows + doors | £6.50 | £8.50 |
| Velux | £2.50 per window | £2.50 per window |
| Garage door | £3 single / £4 double | £3 single / £4 double |

One-off / first clean: 1.75× the regular rate.

### In scope

- Marketing site (7 pages)
- Two-mode lead-capture bot widget (wizard + Claude-backed FAQ chat)
- Lightweight CRM admin panel (leads + customers + 6-weekly round)
- Email notifications via Resend
- WhatsApp ping to owner via CallMeBot (with Twilio as the future upgrade path)
- Local SEO + schema.org + Google Business Profile linkage
- Post-launch Google reviews collection flow

### Out of scope (for this spec)

- Online booking with calendar slots — initial flow is "bot captures contact → owner follows up manually"
- Online payments
- Customer account portal
- Multi-location rollout
- Gutter clearing / soffits / fascias (the bot captures interest leads for these to keep the option open, but the site never advertises them)
- Public liability insurance (owner's decision; bot deflects)
- Blog / content marketing (defer to 3-month review)

---

## 2. Information architecture

A 7-page site with a tight nav. Mobile nav collapses to a hamburger; desktop nav is a single row.

| Path | Purpose | Length | Bot visible |
|---|---|---|---|
| `/` | Hero, what we do, method teaser, pricing teaser, service area, primary CTA | Medium | Yes (inline widget + floating) |
| `/pricing` | Full pricing ranges + add-on table + "what's included" | Short | Yes (inline "get exact price" CTA) |
| `/service-area` | CH1–CH5 named neighbourhoods, static map | Short | Yes (inline) |
| `/method` | Pure water-fed pole explainer: how, why, eco angle | Short | Yes (inline) |
| `/about` | Owner-led: name, photo, story, why Chester | Short | Yes (inline) |
| `/faq` | Indexable FAQ covering the bot's knowledge | Medium | Yes (inline) |
| `/contact` | Bot primary; fallback email-only form below for no-JS visitors | Short | Yes (primary) |

**Implicit pages:** `/admin` (basic-auth, hidden), `/api/*` (backend), `/sitemap.xml`, `/robots.txt`, `/.well-known/security.txt`.

**Footer:** social links (if any later), email `hello@chesterwindowcleaner.co.uk`, an inclusion line — *"Every clean covers your windows, frames, sills and doors — inside-of-glass on request."* (positive framing, no "we don't do X" exclusions on the site itself), copyright.

**Deliberate omissions:** no blog at launch, no testimonials page until reviews accrue, no team page, no booking calendar, no published phone number (bot captures contact, owner calls back).

---

## 3. Brand voice & visual identity

### Voice rules

**Do:**
- First person, owner-led: *"I clean your windows every six weeks"*
- Concrete specifics: *"£20 for a 3-bed semi"* over *"great value"*
- Plain words: *"ladders"* not *"elevated access systems"*
- Calm timings: *"I'll be in touch within 4 working hours"*

**Don't:**
- Hyperbole — *"the best in Chester"*, *"unbeatable"*
- Urgency tricks — countdowns, *"act fast"*, *"only 2 slots left"*
- Exclamation marks (one per page, max)
- Industry jargon (*"WFP system deployed"*) — say *"a long pole with a brush and pure water"*

### Visual identity

| Element | Choice |
|---|---|
| Primary | Muted teal `#2C5F6F` |
| Background | Soft cream `#F7F4ED` |
| Text | Near-black `#1A1A1A` |
| Accent (CTAs) | Warm rust `#D97A4C` |
| Heading font | Fraunces (variable serif, self-hosted) |
| Body font | Inter (self-hosted) |

Both fonts ship locally under `/static/fonts/` — no Google Fonts CDN. Keeps page loads independent of third-party CDNs and removes the GDPR cookie-banner trigger that Google Fonts otherwise creates.

### Hero layout

Left-aligned headline + subhead + primary CTA + secondary CTA. Bot widget embedded directly into the hero on desktop (right side of a 60/40 split). On mobile the widget collapses to a sticky bottom "Tap to get an instant price" floating button. Below the hero: trust strip (3 short items — *Pure water, no ladders* · *Chester & Deeside* · *4-hour reply time*). Then the rest of the page.

### Photography strategy

**Pre-launch:** No stock photos (uniformly poor quality and tone-deaf for the brand). Hero uses an SVG geometric pattern placeholder designed to feel intentional, not empty.

**Post-launch session (commission once):** five photos shot in a single session, used across the site, GBP, and social.
1. Owner with WFP pole, head turned slightly to camera, Chester sandstone wall behind
2. Close-up detail of a freshly cleaned sash window (eastlight, gleam on glass)
3. Wide shot — Chester terrace, van parked, owner mid-clean
4. Hands on the pole controls (texture, craft)
5. Aerial-ish wide of the Roman walls or rows (place-anchoring)

---

## 4. The bot

Two modes inside one widget:

1. **Wizard mode (default)** — structured quote flow, no LLM, deterministic math
2. **Chat mode (opt-in via "Ask a question →" link)** — Claude-backed FAQ assistant with tool calls

### 4.1 Wizard flow

```
[Start]
  ↓
Step 1: Property type
  → 3-bed semi | 4-bed semi | 3-bed detached | 4-bed detached
  → 5-bed detached | Town house / something different
  → If "town house / something different" → POA branch:
      bot skips the instant-quote math and goes to a
      free-text "describe your property" step, then straight
      to contact capture. Lead is flagged poa=1 so the owner
      knows to quote manually.
  ↓
Step 2: Rear access? [qualifying gate]
  → Yes → continue
  → No / not sure → "I can only take on properties with rear access.
                     Want me to note your details in case that changes?"
                     → capture as access_blocked lead, exit
  ↓
Step 3: Postcode [qualifying gate]
  → Validate CH1–CH5 (UK postcode regex + outward code allow-list)
  → Outside → "I focus on Chester and Deeside (CH1–CH5)." (no lead captured)
  ↓
Step 4: Add-ons (multi-select)
  → Conservatory · Extension/side windows+doors · Velux (count)
  → Garage door (single/double) · None
  ↓
Step 5: Frequency
  → Regular 6-weekly · One-off / first clean only (1.75× rate)
  ↓
Step 6: Quote shown
  → "Here's your price: £25 every 6 weeks. Add-ons: +£10 conservatory.
     Total: £35. Want me to book you in?"
  ↓
Step 7: Contact capture
  → Name · Email · Phone (encouraged) · Address · Preferred contact
  → Optional notes (dogs, access codes, anything special)
  ↓
Step 8: Confirmation
  → "Thanks Sarah — I'll be in touch within 4 working hours."
  → Triggers: email to owner · WhatsApp ping · row in SQLite
```

### 4.2 Pricing math (server-side, `/api/quote`)

```python
BASE = {'3bed_semi': 2000, '4bed_semi': 2200, '3bed_det': 2500,
        '4bed_det': 3000, '5bed_det': 3600}  # pence

ADDONS = {
    'conservatory':  {'std': 1000, 'large': 1250},  # pence (midpoint)
    'extension':     {'std':  650, 'large':  850},
    'velux_per_win': 250,
    'garage_single': 300,
    'garage_double': 400,
}
# 'large' tier applies for 4-bed or 5-bed properties
ONE_OFF_MULTIPLIER = 1.75
```

All prices stored as integer pence in the database to avoid float drift. Displayed as `£NN.NN` to the visitor.

### 4.3 Chat mode (Claude)

Triggered by the "Ask me a question →" link inside the widget. System prompt includes:

- **Identity:** *"I'm a bot for Chester Window Cleaner. I help with quotes and answer common questions. I'm not a person — but I'll pass your details to the owner if you'd like."*
- **Service knowledge:** full pricing table, WFP method, service area, what's included
- **Hard rules (with rationale baked in):**
  - Never claim to be human
  - Never confirm a booking — only capture contact details
  - **Gutters / soffits / fascias:** *"Not something I'm offering yet — looking into adding it. Want me to note you for if it becomes available?"* → captures with `interest_flag`
  - **Insurance:** *"Good question — that's something the owner prefers to discuss directly. Can I take your details and have you called back?"*
  - **No rear access:** capture as `access_blocked` lead
  - **Outside CH1–CH5:** polite decline, no capture
- **Tone:** mirrors site voice — owner-led, plain English, calm

### 4.4 Tools available to Claude

The chat bot uses tool calls to keep responses deterministic and grounded:

| Tool | Purpose |
|---|---|
| `compute_quote(property_type, addons, frequency)` | Returns price using the same backend as the wizard |
| `check_postcode(postcode)` | Returns `in_area` / `outside_area` |
| `capture_lead(name, email, phone, address, postcode, interest_flags, notes, source='chat')` | Writes lead to SQLite, triggers email + WhatsApp |

This prevents the LLM from hallucinating prices or pretending to book.

### 4.5 Anti-abuse

- `/api/chat`: 20 messages/hour per IP, hard cap 100/day per IP
- `/api/lead`: max 3 submissions/hour per IP
- Conversation max 20 turns, then bot suggests *"leave your details and let's chat properly"*
- Defensive system prompt against prompt injection — user input never overrides system instructions
- All chat transcripts persisted to `chat_sessions` for post-hoc review

### 4.6 Cost projection

- Wizard quote: **£0** (no LLM)
- Chat conversation: ~5–10 LLM calls, ~500–1500 tokens per call.
- Anthropic Max plan + $100/mo SDK credit (starts 15 June) covers thousands of chats/month.
- Above that limit: ~£0.025 per conversation. Negligible at expected scale.

---

## 5. CRM data model & admin panel

### 5.1 Schema (SQLite)

```sql
-- Every capture: wizard, chat, or fallback contact form
CREATE TABLE leads (
  id INTEGER PRIMARY KEY,
  created_at INTEGER NOT NULL,
  source TEXT NOT NULL,           -- 'wizard' | 'chat' | 'contact_form'
  status TEXT NOT NULL DEFAULT 'new',
                                  -- new | contacted | quoted | booked
                                  -- | converted | declined | spam
  name TEXT,
  email TEXT,
  phone TEXT,
  address TEXT,
  postcode TEXT,
  property_type TEXT,
  addons_json TEXT,
  frequency TEXT,                 -- 'regular_6w' | 'one_off' | NULL
  poa INTEGER DEFAULT 0,          -- 1 if property_type is town house / bespoke
  quote_pence INTEGER,             -- NULL for poa=1 leads (manual quote)
  preferred_contact TEXT,         -- 'email' | 'phone' | 'either'
  notes_visitor TEXT,
  notes_owner TEXT,
  interest_flags_json TEXT,       -- e.g. ["gutters","soffits_fascias"]
  access_blocked INTEGER DEFAULT 0,
  out_of_area INTEGER DEFAULT 0,
  ip_address TEXT,
  user_agent TEXT,
  customer_id INTEGER REFERENCES customers(id)
);

CREATE INDEX idx_leads_status_created ON leads(status, created_at DESC);
CREATE INDEX idx_leads_postcode ON leads(postcode);

-- Leads that converted into regular customers
CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  created_at INTEGER NOT NULL,
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  address TEXT NOT NULL,
  postcode TEXT NOT NULL,
  preferred_contact TEXT,
  property_type TEXT,
  addons_json TEXT,
  frequency TEXT NOT NULL,        -- 'regular_6w' | 'one_off' | other (manual)
  price_pence INTEGER NOT NULL,
  last_cleaned_date TEXT,
  next_due_date TEXT,
  active INTEGER DEFAULT 1,
  notes TEXT,
  lead_id INTEGER REFERENCES leads(id)
);

CREATE INDEX idx_customers_next_due ON customers(active, next_due_date);
CREATE INDEX idx_customers_postcode ON customers(postcode);

-- Every clean performed
CREATE TABLE clean_log (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  cleaned_date TEXT NOT NULL,
  paid INTEGER DEFAULT 0,
  price_charged_pence INTEGER NOT NULL,
  notes TEXT
);

CREATE INDEX idx_clean_log_customer_date ON clean_log(customer_id, cleaned_date DESC);

-- Chat transcripts for tuning and cost tracking
CREATE TABLE chat_sessions (
  id INTEGER PRIMARY KEY,
  created_at INTEGER NOT NULL,
  ip_address TEXT,
  user_agent TEXT,
  messages_json TEXT NOT NULL,
  resulted_in_lead INTEGER DEFAULT 0,
  lead_id INTEGER REFERENCES leads(id),
  llm_input_tokens INTEGER DEFAULT 0,
  llm_output_tokens INTEGER DEFAULT 0
);

-- Review request queue (post-2nd-clean nudge)
CREATE TABLE review_requests (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  queued_at INTEGER NOT NULL,
  sent_at INTEGER,
  reminder_sent_at INTEGER,
  review_received INTEGER DEFAULT 0,
  marked_received_at INTEGER
);
```

### 5.2 Admin pages

All pages basic-auth protected via Caddy `basicauth`.

| Path | Purpose |
|---|---|
| `/admin` | Dashboard — counts (new / contacted / quoted / booked / active / due-this-week / overdue), recent activity feed |
| `/admin/leads` | Lead table, filter by status, sort by date, inline status update, *Convert to customer* button |
| `/admin/leads/<id>` | Full lead detail: visitor notes, interest flags, IP, chat transcript if from chat, owner notes (editable), convert button |
| `/admin/customers` | Customer table, sort by next-due-date, filter by postcode |
| `/admin/customers/<id>` | Customer detail, clean history, edit fields, *Mark cleaned today* button |
| `/admin/round` | THIS WEEK / NEXT WEEK / OVERDUE views, grouped by postcode. Bulk "Mark all CH3 cleaned today" |
| `/admin/chats` | Recent chat transcripts for tuning the system prompt |
| `/admin/reviews` | Review request queue + status |

### 5.3 Key workflows

**Lead → customer conversion:**
1. Lead arrives → email + WhatsApp ping
2. Owner replies via email/phone, agrees a first-clean date
3. Click *Convert to customer* on `/admin/leads/<id>`
4. Form prompts for: agreed first-clean date, agreed price (defaults to quoted), frequency, any address corrections
5. Submit → creates `customers` row, lead marked `converted`, `next_due_date` set to first-clean date

**Daily round:**
1. Open `/admin/round` on phone
2. See "Today: 8 customers in CH3", grouped by postcode
3. Drive the round, tap *Mark cleaned* per house
4. `next_due_date` auto-advances by 6 weeks (or `frequency` interval)

**Overdue catch:**
- `next_due_date < today` → row highlighted red on `/admin/round`
- Daily summary email at 07:00 UTC: *"3 overdue today. 5 due this week."*

**Review nudge:**
- When `clean_log` row #2 is recorded for a customer, a `review_requests` row queues for 24h
- Email sent: short, link to Google Business Profile review form
- One reminder after 4 weeks if no review received; never again after that
- Manually mark `review_received` when you spot one on Google

### 5.4 Backups

- Daily SQLite dump → `/var/backups/chesterwc/db-YYYY-MM-DD.sql.gz` (systemd timer, 30-day retention)
- Weekly off-box scp to your Mac (or a £3/month object store)

---

## 6. Infrastructure

### 6.1 File layout (dev box)

```
/etc/chesterwc/                       # 0600 secrets
  resend-api-key
  whatsapp-webhook-url                # CallMeBot URL with API key
  anthropic-api-key
  admin-creds.txt
  backend.env                         # service config (DRY_RUN, alert email, etc.)

/opt/chesterwc/
  backend/
    app.py                            # single-file http.server-based service
    pricing.py                        # quote computation
    bot.py                            # Claude system prompt + tool wrappers
    notify.py                         # Resend + WhatsApp wrappers
    admin.py                          # admin views
    schema.sql                        # DDL
  site/
    *.html
    /static/{fonts,css,js,img}/
    sitemap.xml · robots.txt

/var/lib/chesterwc/app.db
/var/backups/chesterwc/

/etc/caddy/Caddyfile.d/chesterwindowcleaner.caddy
/etc/systemd/system/chesterwc-backend.service
/etc/systemd/system/chesterwc-backup.{service,timer}
```

Service runs on `127.0.0.1:8094`. Existing port allocation: opspocket-backend 8092, waitlist 8091.

### 6.2 Caddy config

```caddy
chesterwindowcleaner.co.uk, www.chesterwindowcleaner.co.uk {
    redir https://chesterwindowcleaner.co.uk{uri} permanent

    @admin path /admin /admin/*
    basicauth @admin {
        craig <bcrypt-hash-from-caddy-hash-password>
    }
    reverse_proxy @admin 127.0.0.1:8094

    @api path /api/*
    reverse_proxy @api 127.0.0.1:8094

    root * /opt/chesterwc/site
    file_server
    encode gzip zstd

    @static path *.css *.js *.woff2 *.png *.webp *.svg *.avif
    header @static Cache-Control "public, max-age=31536000, immutable"

    header /* {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
        Permissions-Policy "interest-cohort=()"
    }
}
```

### 6.3 Systemd unit

```ini
[Unit]
Description=Chester Window Cleaner backend
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/chesterwc/backend/app.py
EnvironmentFile=/etc/chesterwc/backend.env
Restart=on-failure
RestartSec=2
User=chesterwc
Group=chesterwc

[Install]
WantedBy=multi-user.target
```

### 6.4 Domain & DNS

1. Register `chesterwindowcleaner.co.uk` via **Cloudflare Registrar** (at-cost ~£8/yr, nameservers configured automatically)
2. Cloudflare DNS records:
   - `A @` → `178.104.242.211`
   - `A www` → `178.104.242.211`
   - DKIM (3 CNAMEs) + SPF (TXT) + return-path CNAME from Resend
   - `_dmarc` TXT: `v=DMARC1; p=quarantine; rua=mailto:dmarc@chesterwindowcleaner.co.uk`
3. Cloudflare proxying **OFF (DNS-only)** for this domain — Caddy handles TLS via DNS-01, CF caching offers nothing extra for a Caddy-fronted dynamic site
4. TLS issuance via existing CF token at `/etc/opspocket/cloudflare-token` (if scope doesn't cover the new zone, generate a zone-edit-scoped token and store at `/etc/chesterwc/cloudflare-token`)

### 6.5 Email (Resend)

- Verified sender: `hello@chesterwindowcleaner.co.uk`
- Alerts target: owner's existing email (set via `backend.env` → `ALERT_EMAIL`)
- Domain-scoped API key stored at `/etc/chesterwc/resend-api-key`

### 6.6 WhatsApp notifications

**Phase 1 (launch): CallMeBot**
- Free, no Meta verification
- ~10 msg/hour limit (plenty for early traffic)
- Setup: text *"I allow callmebot to send me messages"* to +34 644 51 95 23 from owner's phone → reply contains API key
- Webhook URL stored in `/etc/chesterwc/whatsapp-webhook-url`

**Phase 2 (when volume justifies): Twilio WhatsApp Business**
- Meta verification (~30 min upfront)
- Higher rate limits
- ~£0.04/message
- Backend wraps both behind `notify.notify_owner_whatsapp(msg)` — swap is one config line

### 6.7 Deploy workflow

```bash
# From the repo on the owner's Mac:
make deploy-site      # rsync site/ → dev:/opt/chesterwc/site/ + caddy reload
make deploy-backend   # rsync backend/ → dev:/opt/chesterwc/backend/ + restart
make logs             # ssh dev 'journalctl -u chesterwc-backend -f'
make backup-pull      # scp latest dump to local
make tail-db          # ssh dev 'sqlite3 /var/lib/chesterwc/app.db'
```

---

## 7. Local SEO & post-launch growth

### 7.1 Schema.org markup (JSON-LD in `<head>` of every relevant page)

```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "@id": "https://chesterwindowcleaner.co.uk/#business",
  "name": "Chester Window Cleaner",
  "image": "https://chesterwindowcleaner.co.uk/static/img/og.png",
  "url": "https://chesterwindowcleaner.co.uk",
  "priceRange": "£20-£50",
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Chester",
    "addressRegion": "Cheshire",
    "addressCountry": "GB"
  },
  "areaServed": [
    "Chester", "Hoole", "Boughton", "Handbridge", "Vicars Cross",
    "Christleton", "Upton", "Newton", "Saltney", "Broughton",
    "Hawarden", "Queensferry", "Connah's Quay"
  ],
  "geo": {"@type": "GeoCoordinates", "latitude": 53.1934, "longitude": -2.8931},
  "openingHoursSpecification": {
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
    "opens": "08:00", "closes": "17:00"
  },
  "sameAs": ["<Google Business Profile URL once verified>"]
}
```

Plus a `Service` schema for each offering (regular clean, one-off, conservatory, extension, velux, garage door) with embedded `Offer` + price.

### 7.2 Page titles

| Page | Title (under 60 chars) |
|---|---|
| Home | Chester Window Cleaner — Pure Water Cleans from £20 |
| Pricing | Window Cleaning Prices in Chester — From £20 |
| Service Area | Window Cleaning: Chester, Hoole, Saltney, Hawarden |
| Method | Pure Water Window Cleaning Explained |
| About | About — Chester Window Cleaner |
| FAQ | Window Cleaning FAQs — Chester Window Cleaner |
| Contact | Contact Chester Window Cleaner |

Meta descriptions handwritten per page, under 160 chars, "Chester" in each.

### 7.3 Google Business Profile

The single biggest local SEO lever. Tracked as a post-launch operational task:

1. Create at `business.google.com` once domain is live
2. Verify (postcard / video / phone — 1–3 weeks)
3. Configure: hours, service area (drop CH1–CH5 postcodes individually), photos (re-use the 5-photo session), enable "online appointments" linking to the bot, list services with prices
4. Paste GBP URL into the schema.org `sameAs`
5. Add the website link to the GBP profile

### 7.4 Reviews collection

- Nudge after the **2nd** clean (~12 weeks in), not the 1st
- 24h delay after the clean is marked complete (avoids feeling pushy)
- Short email with direct link to the GBP review form
- **One** reminder if no review after 4 weeks; then never again
- Manual marking when a review lands (no Google API integration at launch)

### 7.5 Analytics

**Cloudflare Web Analytics** — free, privacy-respecting (no cookies, no consent banner required under UK GDPR / PECR because no personal data is tracked), single-line JS snippet, gives traffic + top pages + referrers. The single third-party network call this introduces is acceptable because it's cookieless and aggregate-only; nothing else third-party is loaded.

### 7.6 Performance targets

- Lighthouse Performance ≥ 95
- Lighthouse Accessibility ≥ 95
- Lighthouse Best Practices ≥ 95
- Lighthouse SEO ≥ 95
- LCP < 1.5s on mid-tier mobile / 4G
- Bot widget JS loaded async + after first paint so it never blocks LCP

### 7.7 Deferred to 3-month review

- `/blog/` with 1–2 posts/month for long-tail Chester keywords
- Photography session #2 (seasonal images)
- Twilio WhatsApp upgrade (if volume demands)

---

## 8. Pre-launch checklist (operational)

These items are not part of the build itself but must be ticked before the site goes live. Tracked in the implementation plan as the final phase.

- [ ] Domain `chesterwindowcleaner.co.uk` registered via Cloudflare Registrar
- [ ] A records set to dev box IP
- [ ] Cloudflare zone token scoped + stored at `/etc/chesterwc/cloudflare-token` (or existing token scope extended)
- [ ] Caddy site config validated (`caddy validate`)
- [ ] Systemd units installed, enabled, started
- [ ] Resend domain verified (DKIM + SPF + return-path)
- [ ] `hello@chesterwindowcleaner.co.uk` test send received
- [ ] CallMeBot API key obtained, test ping received on owner's phone
- [ ] Admin password generated, Caddy bcrypt hash created
- [ ] First end-to-end test lead (wizard) → email + WhatsApp received
- [ ] First end-to-end test lead (chat) → email + WhatsApp received
- [ ] Backup timer firing (check `journalctl -u chesterwc-backup.timer`)
- [ ] `sitemap.xml` + `robots.txt` deployed
- [ ] Google Search Console domain property verified
- [ ] Cloudflare Web Analytics snippet added (optional)
- [ ] Google Business Profile created and submitted for verification (verification can land post-launch)

---

## 9. Decisions deferred

Captured here so future agents and the owner know what was intentionally not decided in this round.

- **Owner name + about-page copy** — placeholder text in v1, copy pass with the owner before site goes public
- **Owner photo** — none at launch; design accommodates a graceful empty state, photo added when the 5-photo session happens
- **Phone number visibility** — bot-only contact at launch (no published phone). Revisit if conversion data suggests a published number would help.
- **Insurance** — owner's decision is "not planning to get insurance"; bot deflects insurance questions to direct contact. Worth re-visiting at the 3-month mark, when conversion data + customer feedback will show whether it's a real blocker.
- **Twilio WhatsApp migration** — defer until CallMeBot's volume limit becomes the bottleneck
- **Blog / content marketing** — defer to 3-month review

---

## 10. Success criteria

The site is considered successful at the 3-month mark if:

1. At least one lead per week is captured from organic search
2. At least 50% of wizard-started visitors complete contact capture
3. At least 5 Google reviews accrued
4. Lighthouse scores remain ≥ 95 across all four categories
5. Zero unplanned downtime > 5 minutes
6. The admin panel is the owner's primary tool for round management (not a paper diary)

Failure modes to watch for and act on:
- Wizard completion rate < 20% — UX problem, redesign step ordering
- Chat-only leads dominate over wizard — wizard isn't doing its job, look at the friction
- Bot hallucinating prices — tighten tool-call requirement in system prompt, add guardrail tests
- Spam submissions overwhelming the lead inbox — add hCaptcha or honeypot to `/api/lead`
