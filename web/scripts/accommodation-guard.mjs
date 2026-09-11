import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
export function assertAccommodation(row) {
  if (row.publication_status === 'indexable' && row.accommodation_type !== 'hotel') {
    throw new Error(`Nonhotel or unclassified indexable accommodation: ${row.id ?? row.slug}`);
  }
}
export function checkAccommodationExports(root) {
  for (const file of readdirSync(path.join(root, 'src/data')).filter(f => /^hotels-.*\.json$/.test(f))) {
    for (const row of JSON.parse(readFileSync(path.join(root,'src/data',file),'utf8'))) assertAccommodation(row);
  }
}
