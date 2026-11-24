import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const SITE = 'https://beednd.com';

const slugify = (value) =>
  value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

// City, brand and bank pages are only listed in the sitemap once at least one active deal exists for them,
// so search engines are not asked to index empty pages.
function pagesWithDeals() {
  const dir = path.join(root, 'src/content/deals');
  const found = new Set();
  for (const file of fs.readdirSync(dir).filter((name) => name.endsWith('.json'))) {
    const deal = JSON.parse(fs.readFileSync(path.join(dir, file), 'utf-8'));
    if (deal.status === 'draft' || deal.status === 'expired') continue;
    for (const city of deal.cities || []) {
      found.add(`/city/${String(deal.country || '').toLowerCase()}/${slugify(city)}/`);
    }
    found.add(`/brands/${deal.brand_id}/`);
    if (deal.bank_details?.bank_id) found.add(`/banks/${deal.bank_details.bank_id}/`);
  }
  return found;
}

const needsDeals = (pathname) =>
  /^\/(city\/[^/]+\/[^/]+|brands\/[^/]+|banks\/[^/]+)\/$/.test(pathname);

function customSitemap() {
  return {
    name: 'custom-sitemap',
    hooks: {
      'astro:build:done': async ({ dir, pages }) => {
        const outDir = fileURLToPath(dir);
        const indexable = pagesWithDeals();
        const today = new Date().toISOString().split('T')[0];

        const urls = pages
          .map((page) => '/' + page.pathname.replace(/^\/+/, '').replace(/index\.html$/, ''))
          .filter((pathname) => !pathname.startsWith('/go/'))
          .filter((pathname) => !needsDeals(pathname) || indexable.has(pathname))
          .map(
            (pathname) =>
              `  <url>\n    <loc>${SITE}${pathname}</loc>\n    <lastmod>${today}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>${pathname === '/' ? '1.0' : '0.7'}</priority>\n  </url>`
          );

        const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join('\n')}\n</urlset>`;
        fs.writeFileSync(path.join(outDir, 'sitemap.xml'), xml, 'utf-8');
        console.log(`[sitemap] sitemap.xml written with ${urls.length} URLs`);
      },
    },
  };
}

export default defineConfig({
  site: SITE,
  devToolbar: { enabled: false },
  prefetch: {
    prefetchAll: true,
    defaultStrategy: 'hover',
  },
  compressHTML: true,
  integrations: [tailwind({ applyBaseStyles: false }), customSitemap()],
  output: 'static',
  build: {
    format: 'directory',
    // Small CSS is inlined so the first paint does not wait for a stylesheet request
    inlineStylesheets: 'always',
  },
});
