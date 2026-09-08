// Shapes match src/hotelareascore/webdata.py exactly — that module is the
// single source of truth; keep this file in sync with it by hand.

export type DimensionKey =
  | 'walkability_density'
  | 'transit_access'
  | 'food_essentials'
  | 'quietness_proxy'
  | 'family_convenience'
  | 'nightlife_access';

export const DIMENSION_KEYS: DimensionKey[] = [
  'walkability_density',
  'transit_access',
  'food_essentials',
  'quietness_proxy',
  'family_convenience',
  'nightlife_access',
];

export type Scores = Record<DimensionKey, number>;

export interface NearbyFact {
  rank: number;
  category: string;
  name: string;
  distance_m: number;
}

export interface ComparableHotel {
  slug: string;
  name: string;
  balanced_score: number;
  /** docs/adr/013: whether this comparable hotel has a real built page
   * (`/hotel/{slug}`) or should link to the client-rendered limited-data
   * card (`/hotel/limited?slug={slug}`) instead. */
  has_static_page: boolean;
}

export interface Hotel {
  id: string;
  slug: string;
  name: string;
  city_id: string;
  city_name: string;
  locality: string | null;
  region: string | null;
  country: string | null;
  lat: number;
  lon: number;
  distance_from_center_km: number;
  far_from_center: boolean;
  locality_mismatch: boolean;
  locality_mismatch_detail: string | null;
  publication_status: 'indexable' | 'noindex';
  scores: Scores;
  balanced_score: number;
  confidence: number;
  confidence_label: 'High' | 'Medium' | 'Low';
  dedupe_confidence: number;
  score_version: string;
  source_release: string;
  verdict: string;
  reason_codes: string[];
  nearby_facts: NearbyFact[];
  comparable: ComparableHotel[];
  /** Always true for anything in hotels-{city}.json (docs/adr/013) --
   * present for consistency with SearchIndexEntry, not because a hotel
   * page ever needs to branch on it. */
  has_static_page: boolean;
}

export interface CityBaseline {
  city_id: string;
  n_hotels: number;
  [key: string]: unknown;
}

export interface CityPageHotelRef {
  name: string;
  locality: string | null;
  slug: string | null;
  score?: number;
  balanced_score?: number;
}

export interface CityPage {
  city_id: string;
  city_name: string;
  country: string;
  center_lat: number;
  center_lon: number;
  n_hotels: number;
  score_version: string;
  source_release: string;
  dimensions: Record<DimensionKey, { median: number | null; mean: number | null }>;
  top_by_dimension: Record<DimensionKey, CityPageHotelRef[]>;
  representative_hotels: CityPageHotelRef[];
  /** page_publication's recorded decision (CLAUDE.md hard rule 2) --
   * 'indexable' or 'noindex'. Read directly by city/[id].astro's
   * `indexable` prop; PUBLIC_INDEXING_ENABLED still ANDs on top of it. */
  publication_status: string;
}

export type PersonaWeights = Record<DimensionKey, number>;
export type Personas = Record<string, PersonaWeights>;

export interface SearchIndexEntry {
  slug: string;
  name: string;
  city: string;
  /** Machine city id (e.g. "new_york"), not the display name in `city` --
   * lets the limited-data card (docs/adr/013) fetch that one city's
   * `/data/search-index-{city_id}.json` shard instead of the full
   * ~17 MB merged index. */
  city_id: string;
  locality: string | null;
  /** docs/adr/013: false for the long tail outside the static-page budget
   * -- SearchBox/ComparableHotels route these to
   * `/hotel/limited?slug={slug}&city={city_id}` instead of `/hotel/{slug}`. */
  has_static_page: boolean;
  // Present so the Compare page (docs/strategy.md §2 journey B) and the
  // limited-data card (web/src/pages/hotel/limited.astro) can reuse this
  // same fetched index instead of a second file.
  scores: Scores;
  balanced_score: number;
  confidence: number;
  confidence_label: 'High' | 'Medium' | 'Low';
  verdict: string;
}
