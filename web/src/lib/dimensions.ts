// Human copy for the 6 v1 dimensions — paraphrased from docs/scoring.md §2,
// our own cited methodology (CLAUDE.md hard rule 3: no claim not grounded in
// structured project data or a cited source). The quietness description
// keeps the mandatory disclaimer wording from scoring.md verbatim.
import type { DimensionKey } from './types';

export interface DimensionMeta {
  label: string;
  short: string;
  description: string;
}

export const DIMENSION_META: Record<DimensionKey, DimensionMeta> = {
  walkability_density: {
    label: 'Walkability',
    short: 'Useful density nearby',
    description:
      'How many everyday, walkable destinations — shops, cafes, services — sit within a short walk, weighted by distance so closer places count more.',
  },
  transit_access: {
    label: 'Transit access',
    short: 'Distance to public transport',
    description:
      'Proximity to train, metro, light rail and bus stops. This is a distance measure only — no travel-time or routing data is used.',
  },
  food_essentials: {
    label: 'Food & essentials',
    short: 'Restaurants, cafes, groceries, pharmacy',
    description:
      'Diversity and proximity of restaurants, cafes, grocery stores, pharmacies and similar everyday essentials — a mix of different useful places nearby scores higher than one type repeated.',
  },
  quietness_proxy: {
    label: 'Quiet-surroundings proxy',
    short: 'Estimated environmental exposure',
    description:
      'Estimates environmental noise exposure from nearby infrastructure and activity — major roads, rail lines, nightlife venues and airports. This is not an in-room noise measurement.',
  },
  family_convenience: {
    label: 'Family convenience',
    short: 'Parks and family-friendly amenities',
    description: 'Proximity to parks, playgrounds and similar family-oriented amenities.',
  },
  nightlife_access: {
    label: 'Nightlife access',
    short: 'Bars, pubs and nightlife venues',
    description:
      'Proximity and density of bars, pubs and nightlife venues — a plus for travelers seeking it, and a factor worth weighing against the quiet-surroundings score for others.',
  },
};
