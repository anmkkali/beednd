import { defineCollection, z } from 'astro:content';

const dealsCollection = defineCollection({
  type: 'data',
  schema: z.object({
    id: z.string(),
    slug: z.string(),
    title: z.string().min(5).max(140),
    short_description: z.string().max(300),
    brand_id: z.string(),
    country: z.string().regex(/^([A-Z]{2}|GLOBAL)$/).default('GLOBAL'),
    cities: z.array(z.string()).default([]),
    areas: z.array(z.string()).default([]),
    branch_info: z.array(z.object({
      branch_name: z.string(),
      address: z.string(),
      phone: z.string().optional(),
      google_maps_url: z.string().optional()
    })).default([]),
    category: z.enum([
      'clothing-fashion',
      'tech-electronics',
      'ai-tools',
      'food-dining',
      'beauty-wellness',
      'travel-lifestyle',
      'groceries-essentials'
    ]),
    deal_type: z.enum([
      'online',
      'in-store',
      'bank-card',
      'promo-code',
      'influencer-code',
      'store-sale',
      'campaign-stunt'
    ]),
    bank_details: z.object({
      bank_id: z.string(),
      eligible_cards: z.array(z.string()),
      cashback_percent: z.number().optional(),
      fixed_discount_amount: z.number().optional(),
      day_restrictions: z.array(z.string()).optional(),
      max_discount_cap: z.number().optional()
    }).optional(),
    discount_type: z.enum(['percentage', 'fixed_amount', 'bogo', 'freebie', 'free_shipping']),
    discount_value: z.string(), // e.g. "50% OFF", "$80 OFF"
    numeric_discount_percent: z.number().min(0).max(100).optional(),
    promo_code: z.string().optional(),
    terms_and_conditions: z.array(z.string()).min(1),
    start_date: z.string(),
    end_date: z.string().nullable().default(null),
    source_url: z.string().url(),
    affiliate_url: z.string(),
    last_verified_at: z.string(),
    status: z.enum(['active', 'expired', 'draft']).default('active'),
    is_featured: z.boolean().default(false),
    is_sponsored: z.boolean().default(false),
    is_trending: z.boolean().default(false),
    limited_time: z.boolean().default(false),
    channels: z.array(z.enum(['online', 'in-store'])).default([]),
    offer_kind: z.enum(['discount', 'trial', 'free', 'promo', 'voucher', 'credits']).optional(),
    badge_text: z.string().max(80).optional(),
    image: z.object({
      src: z.string(),
      alt: z.string()
    }),
    tags: z.array(z.string()).default([])
  })
});

const brandsCollection = defineCollection({
  type: 'data',
  schema: z.object({
    id: z.string(),
    name: z.string(),
    slug: z.string(),
    logo_url: z.string(),
    website_url: z.string(),
    country: z.string().regex(/^([A-Z]{2}|GLOBAL)$/).default('GLOBAL'),
    categories: z.array(z.string()),
    short_bio: z.string(),
    return_policy_days: z.number().optional(),
    free_shipping_min_order: z.number().optional()
  })
});

const banksCollection = defineCollection({
  type: 'data',
  schema: z.object({
    id: z.string(),
    name: z.string(),
    short_code: z.string(),
    country: z.string().regex(/^([A-Z]{2}|GLOBAL)$/).default('PK'),
    logo_url: z.string(),
    website_url: z.string().optional(),
    official_discounts_page: z.string().optional(),
    helpline_number: z.string().optional(),
    supported_card_tiers: z.array(z.string()).default([]),
    primary_color_hex: z.string().optional()
  })
});

const blogCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    published_date: z.string(),
    author: z.string().default('Editorial Team'),
    hero_image: z.string(),
    target_country: z.string().regex(/^([A-Z]{2}|GLOBAL)$/).default('GLOBAL'),
    featured_deal_ids: z.array(z.string()).default([]),
    tags: z.array(z.string()),
    is_published: z.boolean().default(true)
  })
});

export const collections = {
  deals: dealsCollection,
  brands: brandsCollection,
  banks: banksCollection,
  blog: blogCollection
};
