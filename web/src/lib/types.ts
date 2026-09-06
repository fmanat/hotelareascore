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
}

export interface Hotel {
  id: string;
  slug: string;
  name: string;
  city_id: string;
  city_name: string;
  locality: string | null;
  country: string | null;
  lat: number;
  lon: number;
  distance_from_center_km: number;
  far_from_center: boolean;
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
}

export interface CityBaseline {
  city_id: string;
  n_hotels: number;
  [key: string]: unknown;
}

export type PersonaWeights = Record<DimensionKey, number>;
export type Personas = Record<string, PersonaWeights>;

export interface SearchIndexEntry {
  slug: string;
  name: string;
  city: string;
  locality: string | null;
}
