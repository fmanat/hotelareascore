import test from 'node:test';
import assert from 'node:assert/strict';
import { assertAccommodation } from './accommodation-guard.mjs';
test('unknown and nonhotel export cannot bypass recorded-status eligibility', () => {
  for (const kind of [undefined,'unknown','hostel','guesthouse-B&B','whole-home','aparthotel','serviced-apartment']) {
    assert.throws(() => assertAccommodation({id:'test',publication_status:'indexable',accommodation_type:kind}));
    assertAccommodation({id:'test',publication_status:'noindex',accommodation_type:kind});
  }
  assertAccommodation({id:'test',publication_status:'indexable',accommodation_type:'hotel'});
});
