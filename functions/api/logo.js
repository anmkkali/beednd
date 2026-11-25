export async function onRequestGet({ request }) {
  const url = new URL(request.url);
  const domain = (url.searchParams.get('d') || '').replace(/[^a-zA-Z0-9.-]/g, '').slice(0, 120);
  const initial = (url.searchParams.get('n') || domain.charAt(0) || 'B').charAt(0).toUpperCase();

  const fallbackSvg = () =>
    new Response(
      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#ffffff"/><text x="32" y="42" text-anchor="middle" font-family="Georgia,serif" font-size="32" font-weight="600" fill="#141413">${initial}</text></svg>`,
      {
        status: 200,
        headers: {
          'Content-Type': 'image/svg+xml; charset=utf-8',
          'Cache-Control': 'public, max-age=604800, immutable',
        },
      }
    );

  if (!domain) return fallbackSvg();

  try {
    const upstream = await fetch(
      `https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=64`,
      { redirect: 'follow', cf: { cacheTtl: 604800, cacheEverything: true } }
    );
    const ct = upstream.headers.get('content-type') || '';
    if (!upstream.ok || !ct.startsWith('image/')) {
      return fallbackSvg();
    }
    const body = await upstream.arrayBuffer();
    if (!body || body.byteLength < 64) {
      return fallbackSvg();
    }
    return new Response(body, {
      status: 200,
      headers: {
        'Content-Type': ct,
        'Cache-Control': 'public, max-age=604800, immutable',
      },
    });
  } catch {
    return fallbackSvg();
  }
}
