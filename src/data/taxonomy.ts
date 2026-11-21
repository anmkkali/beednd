// Category -> group -> filter tree shared by the sidebar and the category pages.
// A group id must also appear as a tag on a deal (for example "women") for that deal to match.
export type Filter = { label: string; sub?: string; kind?: string };
export type Group = { id: string; label: string; filters: Filter[] };
export type Category = { id: string; name: string; icon: string; blurb: string; groups: Group[]; kinds?: Filter[] };

export const KIND_FILTERS: Filter[] = [
  { label: 'Discounts', kind: 'discount' },
  { label: 'Free trials', kind: 'trial' },
  { label: 'Free', kind: 'free' },
  { label: 'Promo codes', kind: 'promo' },
  { label: 'Credits & bonus', kind: 'credits' },
];

// Free trials, free plans and credits only make sense for software, so other categories get codes and vouchers.
export const SHOPPING_KINDS: Filter[] = [
  { label: 'Promo codes', kind: 'promo' },
  { label: 'Vouchers', kind: 'voucher' },
];

export const ALL_KIND_LABELS: Record<string, string> = {
  discount: 'Discounts',
  trial: 'Free trials',
  free: 'Free',
  promo: 'Promo codes',
  voucher: 'Vouchers',
  credits: 'Credits & bonus',
};

const group = (id: string, label: string, allLabel: string, filters: Filter[]): Group => ({
  id,
  label,
  filters: [{ label: allLabel }, ...filters],
});

const aiGroup = (id: string, label: string): Group => group(id, label, `All ${label} tools`, KIND_FILTERS);

const withShoppingKinds = (category: Category): Category => ({ ...category, kinds: SHOPPING_KINDS });

const baseCategories: Category[] = [
  {
    id: 'clothing-fashion',
    name: 'Clothing & Fashion',
    icon: 'apparel',
    blurb: 'Menswear, womenswear, kids and pets. Pick a group, then narrow by type.',
    groups: [
      group('men', "Men's", "All men's clothing", [
        { label: 'Stitched', sub: 'stitched' },
        { label: 'Unstitched', sub: 'unstitched' },
        { label: 'Footwear', sub: 'footwear' },
        { label: 'Accessories', sub: 'accessories' },
      ]),
      group('women', "Women's", "All women's clothing", [
        { label: 'Unstitched', sub: 'unstitched' },
        { label: 'Pret / Ready to wear', sub: 'pret' },
        { label: 'Footwear', sub: 'footwear' },
        { label: 'Bags & accessories', sub: 'accessories' },
      ]),
      group('kids', "Kids'", "All kids' clothing", [
        { label: 'Boys', sub: 'boys' },
        { label: 'Girls', sub: 'girls' },
        { label: 'Baby & newborn', sub: 'baby' },
        { label: 'Footwear', sub: 'footwear' },
      ]),
      group('pets', 'Pets', 'All pet apparel & gear', [
        { label: 'Clothing', sub: 'apparel' },
        { label: 'Accessories', sub: 'accessories' },
      ]),
    ],
  },
  {
    id: 'ai-tools',
    name: 'AI Tools',
    icon: 'ai',
    blurb: 'Discounts, free trials, credits and promo codes for AI tools, by type of tool.',
    groups: [
      aiGroup('video', 'AI Video'),
      aiGroup('image', 'AI Image'),
      aiGroup('voice', 'AI Voice & Audio'),
      aiGroup('3d', 'AI 3D'),
      aiGroup('writing', 'AI Writing'),
      aiGroup('coding', 'AI Coding'),
      aiGroup('website-builder', 'AI Website Builders'),
      aiGroup('productivity', 'AI Productivity'),
    ],
  },
  {
    id: 'tech-electronics',
    name: 'Tech & Electronics',
    icon: 'tech',
    blurb: 'Phones, computers, appliances, audio and finance tools.',
    groups: [
      group('mobiles', 'Mobiles & Tablets', 'All mobiles & tablets', [
        { label: 'Smartphones', sub: 'smartphones' },
        { label: 'Tablets', sub: 'tablets' },
        { label: 'Accessories', sub: 'accessories' },
      ]),
      group('computers', 'Computers', 'All computers', [
        { label: 'Laptops', sub: 'laptops' },
        { label: 'Desktops', sub: 'desktops' },
        { label: 'Peripherals', sub: 'peripherals' },
      ]),
      group('appliances', 'Home Appliances', 'All home appliances', [
        { label: 'Kitchen', sub: 'kitchen' },
        { label: 'Cooling & heating', sub: 'climate' },
      ]),
      group('audio', 'Audio & Wearables', 'All audio & wearables', [
        { label: 'Headphones', sub: 'headphones' },
        { label: 'Smartwatches', sub: 'smartwatches' },
      ]),
      group('finance', 'Finance Tools', 'All finance tools', [
        { label: 'Charting', sub: 'charting' },
        { label: 'Stocks & trading', sub: 'stocks' },
      ]),
    ],
  },
  {
    id: 'beauty-wellness',
    name: 'Beauty & Wellness',
    icon: 'beauty',
    blurb: 'Skincare, makeup, fragrance, grooming and wellness.',
    groups: [
      group('women', "Women's", "All women's beauty", [
        { label: 'Skincare', sub: 'skincare' },
        { label: 'Makeup', sub: 'makeup' },
        { label: 'Fragrance', sub: 'fragrance' },
        { label: 'Hair care', sub: 'hair' },
      ]),
      group('men', "Men's grooming", "All men's grooming", [
        { label: 'Skincare', sub: 'skincare' },
        { label: 'Fragrance', sub: 'fragrance' },
        { label: 'Hair & beard', sub: 'hair' },
      ]),
      group('wellness', 'Health & Wellness', 'All health & wellness', [
        { label: 'Supplements', sub: 'supplements' },
        { label: 'Fitness', sub: 'fitness' },
      ]),
    ],
  },
  {
    id: 'food-dining',
    name: 'Food & Dining',
    icon: 'food',
    blurb: 'Restaurants, fast food, cafes and food delivery.',
    groups: [
      group('restaurants', 'Restaurants', 'All restaurants', [
        { label: 'Fine dining', sub: 'fine-dining' },
        { label: 'Casual dining', sub: 'casual' },
      ]),
      group('fast-food', 'Fast Food', 'All fast food', [
        { label: 'Burgers', sub: 'burgers' },
        { label: 'Pizza', sub: 'pizza' },
        { label: 'Chicken', sub: 'chicken' },
      ]),
      group('cafes', 'Cafes & Bakery', 'All cafes & bakery', []),
      group('delivery', 'Food Delivery', 'All food delivery', []),
    ],
  },
  {
    id: 'travel-lifestyle',
    name: 'Travel & Hotels',
    icon: 'travel',
    blurb: 'Hotels, flights, tours and car rentals.',
    groups: [
      group('hotels', 'Hotels & Stays', 'All hotels & stays', []),
      group('flights', 'Flights', 'All flights', []),
      group('experiences', 'Tours & Experiences', 'All tours & experiences', []),
      group('car-rental', 'Car Rentals', 'All car rentals', []),
    ],
  },
  {
    id: 'groceries-essentials',
    name: 'Groceries',
    icon: 'grocery',
    blurb: 'Supermarkets, household essentials and fresh produce.',
    groups: [
      group('supermarkets', 'Supermarkets', 'All supermarkets', []),
      group('household', 'Household Essentials', 'All household essentials', []),
      group('fresh', 'Fresh & Organic', 'All fresh & organic', []),
    ],
  },
];

export const categories: Category[] = baseCategories.map((category) =>
  category.id === 'ai-tools' ? category : withShoppingKinds(category)
);

export const categoryById = new Map(categories.map((category) => [category.id, category]));
