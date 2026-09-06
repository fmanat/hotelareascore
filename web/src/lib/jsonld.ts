// Structured data (docs/seo-policy.md §6): Hotel/LodgingBusiness/Place/
// BreadcrumbList/WebSite ONLY. Our environmental score is explicitly NOT a
// review (CLAUDE.md hard rule 3, 7 — no fabricated precision, no fake
// ratings) — nothing here may ever emit `aggregateRating`, `review`, or
// `ratingValue`. scripts/seo_assertions.py's build-time CI check parses
// every emitted block and fails the build if one of those keys appears.
import { SITE_URL } from './site';

export function websiteJsonLd() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'HotelAreaScore',
    url: SITE_URL,
  };
}

export function breadcrumbJsonLd(items: { name: string; path: string }[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: item.name,
      item: new URL(item.path, SITE_URL).toString(),
    })),
  };
}

export function placeJsonLd(opts: { name: string; lat: number; lon: number; addressLocality?: string | null }) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Place',
    name: opts.name,
    geo: {
      '@type': 'GeoCoordinates',
      latitude: opts.lat,
      longitude: opts.lon,
    },
    ...(opts.addressLocality
      ? { address: { '@type': 'PostalAddress', addressLocality: opts.addressLocality } }
      : {}),
  };
}

/** LodgingBusiness, not Hotel's stricter sibling with review/rating
 * conventions baked into common tooling -- deliberately no
 * `starRating`/`aggregateRating` field is ever set here. `additionalProperty`
 * carries our own computed dimension scores AS OUR OWN metric (named and
 * described as ours), never disguised as a guest-review signal. */
export function lodgingBusinessJsonLd(opts: {
  name: string;
  lat: number;
  lon: number;
  addressLocality?: string | null;
  url: string;
  balancedScore: number;
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'LodgingBusiness',
    name: opts.name,
    url: new URL(opts.url, SITE_URL).toString(),
    geo: {
      '@type': 'GeoCoordinates',
      latitude: opts.lat,
      longitude: opts.lon,
    },
    ...(opts.addressLocality
      ? { address: { '@type': 'PostalAddress', addressLocality: opts.addressLocality } }
      : {}),
    additionalProperty: {
      '@type': 'PropertyValue',
      name: 'HotelAreaScore surroundings balanced score',
      description:
        'An independently computed score of the area surrounding this hotel (walkability, transit, food, quiet, family, nightlife) — not a guest review or star rating.',
      value: opts.balancedScore,
    },
  };
}
