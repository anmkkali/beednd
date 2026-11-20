import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

function customSitemap() {
  return {
    name: 'custom-sitemap',
    hooks: {
      'astro:build:done': async ({ dir, pages }) => {
        const outDir = fileURLToPath(dir);
        const site = 'https://dealssite.com';
        const urls = pages
          .filter(p => !p.pathname.includes('go/'))
          .map(p => {
            const cleanPath = p.pathname.replace(/\/index\.html$/, '/').replace(/^\/?/, '/');
            return `  <url>\n    <loc>${site}${cleanPath}</loc>\n    <changefreq>daily</changefreq>\n    <priority>${cleanPath === '/' ? '1.0' : '0.8'}</priority>\n  </url>`;
          });

        const sitemapContent = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join('\n')}\n</urlset>`;
        fs.writeFileSync(path.join(outDir, 'sitemap.xml'), sitemapContent, 'utf-8');
        console.log(`[sitemap] Successfully generated sitemap.xml with ${urls.length} verified URLs.`);
      }
    }
  };
}

export default defineConfig({
  site: 'https://dealssite.com',
  prefetch: {
    prefetchAll: true,
    defaultStrategy: 'hover',
  },
  compressHTML: true,
  integrations: [
    tailwind({
      applyBaseStyles: false,
    }),
    customSitemap(),
  ],
  output: 'static',
  build: {
    format: 'directory'
  }
});

