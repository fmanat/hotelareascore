// Display copy for the deterministic reason codes computed in
// src/hotelareascore/reason_codes.py — keep the code list in sync with that
// module. Never phrase these as free text generated per-hotel; the set of
// possible strings is fixed and reviewed once, here.
export const REASON_CODE_COPY: Record<string, string> = {
  HIGH_RESTAURANT_DENSITY: 'High density of restaurants nearby',
  GOOD_TRANSIT_ACCESS: 'Good transit access',
  VERY_CLOSE_TRANSIT: 'A transit stop is very close',
  QUIET_SURROUNDINGS: 'Quiet surroundings',
  BUSY_SURROUNDINGS: 'Busy surroundings',
  ACTIVE_NIGHTLIFE: 'Active nightlife nearby',
  FAMILY_FRIENDLY_SURROUNDINGS: 'Family-friendly surroundings',
  LOW_DATA_CONFIDENCE: 'Data confidence is low for this location',
  LIMITED_NEARBY_DATA: 'Limited nearby data available',
};
