export function onRequestGet(context) {
  const cfCountry = context.request?.cf?.country;
  const headerCountry = context.request?.headers?.get('CF-IPCountry');
  const country = (cfCountry || headerCountry || '').toUpperCase();

  return new Response(
    JSON.stringify({
      country: /^[A-Z]{2}$/.test(country) && country !== 'XX' && country !== 'T1' ? country : null,
    }),
    {
      headers: {
        'content-type': 'application/json; charset=utf-8',
        'cache-control': 'no-store, no-cache, must-revalidate',
      },
    }
  );
}
