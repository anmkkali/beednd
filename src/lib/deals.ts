// Small helpers shared by deal cards, filters and notifications.
type DealLike = {
  offer_kind?: string;
  promo_code?: string;
  tags?: string[];
  category: string;
  brand_id: string;
};

export const KIND_LABELS: Record<string, string> = {
  discount: 'Discounts',
  trial: 'Free trial',
  free: 'Free',
  promo: 'Promo codes',
  credits: 'Credits',
};

export const dealKind = (deal: DealLike) => deal.offer_kind || (deal.promo_code ? 'promo' : 'discount');

// Whole-token matching string, for example "|women|unstitched|". Prevents "men" matching "women".
export const dealTokens = (deal: DealLike) =>
  '|' +
  [...(deal.tags || []), deal.category, deal.brand_id]
    .map((tag) => tag.toLowerCase().trim().replace(/\s+/g, '-'))
    .join('|') +
  '|';

export const shortDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });

export const expiryLabel = (end: string | null | undefined, limited: boolean, now = Date.now()) => {
  if (end) {
    const days = Math.ceil((new Date(end).getTime() - now) / 86_400_000);
    if (days < 0) return { label: 'Expired', expired: true };
    if (days <= 30) return { label: days === 0 ? 'Expires today' : `Expires in ${days}d`, expired: false };
  }
  return limited ? { label: 'Limited time', expired: false } : { label: '', expired: false };
};
