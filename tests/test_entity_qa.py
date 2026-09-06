import pytest

from hotelareascore.entity_qa import is_likely_non_hotel


def test_flags_known_non_hotel_examples():
    # Real example from the 18-hotel inspection audit (docs/STATE.md).
    assert is_likely_non_hotel("RevenuebyDesign")


def test_true_tower_is_now_a_known_accepted_false_negative():
    # "อาคารใยแก้ว True Tower" (the other original audit example, an office
    # building) is no longer flagged now that "tower" was removed from
    # NON_HOTEL_MARKERS -- removing it was necessary to stop excluding real
    # hotels/serviced apartments (Batch 1 dry run, see module docstring).
    # This is a deliberate precision-over-recall trade-off, not a bug.
    assert not is_likely_non_hotel("อาคารใยแก้ว True Tower")


def test_flags_clear_business_entities():
    assert is_likely_non_hotel("SBJ Benefit Consultants")
    assert is_likely_non_hotel("Kingston University")
    assert is_likely_non_hotel("F9 Consulting - Accountants City of London")
    assert is_likely_non_hotel("The Emirates Academy of Hospitality Management")
    assert is_likely_non_hotel("One Point Solution")


def test_does_not_flag_plain_hotel_names():
    assert not is_likely_non_hotel("The Savoy Hotel")
    assert not is_likely_non_hotel("Premier Inn London Richmond")
    assert not is_likely_non_hotel("Cedar House")  # plain small B&B name, no keyword either way
    assert not is_likely_non_hotel("Grace")


def test_does_not_flag_known_hospitality_brands_even_without_lodging_keyword():
    assert not is_likely_non_hotel("The Carlton Tower Jumeirah")
    assert not is_likely_non_hotel("lebua at State Tower")
    assert not is_likely_non_hotel("Ascott Embassy Sathorn")
    assert not is_likely_non_hotel("Four Points by Sheraton Bangkok, Sukhumvit 22 Tower")
    assert not is_likely_non_hotel("Cheval Three Quays at The Tower of London")
    assert not is_likely_non_hotel("Bob W Tower of London")
    assert not is_likely_non_hotel("Tower Residences by Blue Orchid")


def test_accented_hotel_spellings_are_recognized():
    # v1 missed every accented spelling of "hotel" -- Batch 1 dry run
    # (docs/STATE.md) found real Paris hotels wrongly excluded because
    # "Hôtel" with the accent didn't match a bare ASCII "hotel" pattern.
    assert not is_likely_non_hotel("Hôtel Design Sorbonne")
    assert not is_likely_non_hotel("Hôtel Elysées Union")
    assert not is_likely_non_hotel("BLC Design Hôtel")
    assert not is_likely_non_hotel("Château de Something")


def test_design_and_tower_are_not_markers_after_batch1_false_positives():
    # "Design Hotel"/"Design Apartments" is a legitimate boutique-hospitality
    # style, and OYO-branded short-term rentals are routinely named after
    # the residential tower they're in -- both caused real false exclusions
    # on the Batch 1 dry run and were removed from NON_HOTEL_MARKERS.
    assert not is_likely_non_hotel("Design Apartment Urban Epiro - Roma")
    assert not is_likely_non_hotel("Navona Tower Relais")
    assert not is_likely_non_hotel("OYO 985 Home 1BR Lake City Tower, JLT")
    assert not is_likely_non_hotel("Zara Tower - Serviced Apartments")
    assert not is_likely_non_hotel("Royal Tower, Atlantis The Palm, Dubai")
    assert not is_likely_non_hotel("Occidental Diagonal 414")
    assert not is_likely_non_hotel("Occidental Aurelia")


def test_serviced_apartments_plural_recognized():
    assert not is_likely_non_hotel("City Stay Serviced Apartments")


def test_markers_do_not_match_inside_unrelated_words():
    # "temple" matched inside "Templeton", "church" matched inside
    # "Hornchurch" (a London place name) before every marker got its own
    # \b...\b -- both are real hotel names from the Batch 1/London dry run.
    assert not is_likely_non_hotel("Templeton Garden")
    assert not is_likely_non_hotel("Miiro Templeton Garden, a Member of Design Hotels")
    assert not is_likely_non_hotel("Innkeeper's Collection Hornchurch")
    assert not is_likely_non_hotel("Weddings Hornchurch")


def test_street_name_collisions_not_flagged():
    # Bug #4 (Batch 2 New York/Singapore): "union"/"mosque" matched inside
    # real street/square names, wrongly excluding a real W Hotels property
    # and a real Singapore hostel address.
    assert not is_likely_non_hotel("W New York – Union Square")
    assert not is_likely_non_hotel("31 Union Square West")
    assert not is_likely_non_hotel("Wink @ Mosque Street")
    assert not is_likely_non_hotel("Hotel on Church Street")
    assert not is_likely_non_hotel("Bank Street Studios")  # would need a lodging keyword in practice; checks the guard alone
    assert not is_likely_non_hotel("Temple Place Apartments")


def test_risky_markers_still_catch_genuine_non_hotels():
    # The guard only exempts "<marker> <street-type-word>" -- a real
    # institution named plainly should still be caught.
    assert is_likely_non_hotel("First National Bank")
    assert is_likely_non_hotel("St Mary's Church")
    assert is_likely_non_hotel("Sri-Sri Radha Govinda Temple")


def test_park_plaza_brand_recognized():
    assert not is_likely_non_hotel("Park Plaza County Hall London Limited")


def test_generic_accommodation_keyword_recognized():
    assert not is_likely_non_hotel("International Accommodation Ltd")


def test_empty_or_none_name_not_flagged():
    assert not is_likely_non_hotel("")
    assert not is_likely_non_hotel(None)


def test_lodging_keyword_alone_beats_marker():
    # "Ltd" NON_HOTEL_MARKERS hit, but "Hostel" keyword should win.
    assert not is_likely_non_hotel("City Stay Hostel Ltd")


def test_souq_marker_catches_a_souk_name():
    assert is_likely_non_hotel("Souq Waqif")
    assert is_likely_non_hotel("Grand Souq Market")


def test_souq_marker_alone_does_not_catch_the_backlog_specimen():
    # docs/STATE.md entity-QA backlog: "Souq Madinat Jumeirah, Dubai" is a
    # souk/venue, not a hotel -- but it is NOT caught even with the new
    # "souq" marker, because "Jumeirah" hits the brand allowlist first and
    # short-circuits everything else (the pre-existing, separately-logged
    # brand-shortcut limitation in the module docstring). Documented here
    # as a concrete instance of that known limitation, not a bug in the new
    # marker: the marker itself works (see test_souq_marker_catches_a_souk_name).
    assert not is_likely_non_hotel("Souq Madinat Jumeirah, Dubai")


def test_souq_marker_does_not_collide_with_real_hotel_name():
    # "Maison Souquet" (Paris) is a real boutique hotel -- \b after "souq"
    # correctly fails to match since the next letter ("u") is still a word
    # character, same word-boundary discipline as bug #3.
    assert not is_likely_non_hotel("Maison Souquet")


def test_souk_and_bazaar_and_mall_deliberately_not_markers():
    # Checked against every hit across all 12 ingested cities and rejected
    # (module docstring): each has a real, currently-included hotel using
    # the word as a theme name, with no guardable collision pattern.
    assert not is_likely_non_hotel("Souk Al Bahar Palace Hotel Dubai")
    assert not is_likely_non_hotel("The Bazaar Hotel Bangkok")
    assert not is_likely_non_hotel("Kempinski Hotel Mall of the Emirates")


@pytest.mark.xfail(
    reason=(
        "Known limitation, logged not fixed (module docstring): this heuristic "
        "is Latin-script only. 桝本屋酒店 is almost certainly a liquor shop -- "
        "酒店 means 'sake shop' in Japanese, 'hotel' only in Chinese -- but "
        "nothing here reads script or language, so it can't be caught without "
        "a dedicated non-English marker list. Documented as an honest xfail, "
        "not silently skipped, so this stays visible until someone builds that."
    ),
    strict=True,
)
def test_known_limitation_cjk_liquor_shop_not_caught():
    assert is_likely_non_hotel("桝本屋酒店")
