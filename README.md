# DealsSite ⚡
> Ultra-fast, SEO-optimized Deals & Coupons aggregator for Global/US and Pakistan retail markets.

Designed with an Astro SSG foundation, zero runtime JS core, Resourify-inspired category sidebar, Pagefind client search, and an automated Python + Google Gemini ingestion pipeline.

---

## 🚀 Key Features
- **Lighthouse 98+ Speed:** Astro Static Site Generation with Cloudflare Pages Edge CDN.
- **Resourify Layout:** Sticky left categories & topics sidebar, top navbar with `Ctrl + K` instant search.
- **My Card Engine:** Client-side bank card personalization (HBL, Meezan, Bank Alfalah) saved in `localStorage`.
- **Stack Finder:** Real-time compounding discount calculator (Store Sale + Bank Discount + Promo Code).
- **Automated Pipeline:** Python scrapers (Shopify `/products.json`, Bank discount portals) + Google Gemini 2.5 Flash normalization.
- **Zero Cost Stack:** $0/month budget utilizing free tiers (Cloudflare Pages, GitHub Actions, Google AI Studio).

---

## 🛠️ Project Structure
```
├── .github/workflows/       # GitHub Actions automated ingestion & Cloudflare deployment
├── public/                  # Static assets (robots.txt, ads.txt, favicon.svg)
├── scripts/                 # Automated Python scraping & Gemini 2.5 Flash normalization
├── src/
│   ├── components/          # Reusable Astro UI components (Resourify sidebar, Deal cards)
│   ├── content/             # Structured Zod content collections (deals, brands, banks, blog)
│   ├── layouts/             # Base and SEO layouts
│   └── pages/               # Programmatic SEO routes (/deals/[slug], /brands/[slug], /banks/[slug])
└── package.json
```

---

## 💻 Local Development
1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

3. **Build production static site + Pagefind index:**
   ```bash
   npm run build
   ```

---

## 🤖 Automated Ingestion Pipeline
To run the automated collector and Gemini AI normalizer:
```bash
pip install -r scripts/requirements.txt
export GEMINI_API_KEY="your-gemini-api-key"
python scripts/run_pipeline.py
```
