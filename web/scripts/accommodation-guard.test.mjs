import test from 'node:test';
import assert from 'node:assert/strict';
import { assertAccommodation } from './accommodation-guard.mjs';
test('unknown and nonhotel export cannot bypass recorded-status eligibility', () => {
  for (const kind of [undefined,'unknown','hostel','guesthouse-B&B','whole-home','aparthotel','serviced-apartment']) {
    assert.throws(() => assertAccommodation({id:'test',publication_status:'indexable',accommodation_type:kind,name_index_eligible:true}));
    assertAccommodation({id:'test',publication_status:'noindex',accommodation_type:kind});
  }
  assertAccommodation({id:'test',publication_status:'indexable',accommodation_type:'hotel',name_index_eligible:true});
});
test('hotel type cannot bypass a missing or unreliable Latin name', () => {
  for (const eligible of [undefined,false]) assert.throws(() => assertAccommodation({
    id:'test',publication_status:'indexable',accommodation_type:'hotel',name_index_eligible:eligible,
  }), /Latin name/);
});
