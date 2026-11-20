import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const deals = await getCollection('deals');
  return deals.map(deal => ({
    params: { slug: deal.data.slug },
    props: { affiliateUrl: deal.data.affiliate_url }
  }));
}

export const GET: APIRoute = async ({ props }) => {
  const { affiliateUrl } = props as { affiliateUrl: string };

  // Return HTML meta refresh redirect with nofollow/sponsored hygiene
  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=${affiliateUrl}">
  <meta name="robots" content="noindex, nofollow">
  <title>Redirecting to Partner Store...</title>
</head>
<body style="background:#0B0F17;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-center;height:100vh;margin:0;">
  <p>Redirecting you securely to verified partner discount...</p>
</body>
</html>`;

  return new Response(html, {
    status: 200,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'X-Robots-Tag': 'noindex, nofollow',
      'Cache-Control': 'no-cache, no-store, must-revalidate'
    }
  });
};
