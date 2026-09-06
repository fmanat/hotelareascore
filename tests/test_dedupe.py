from hotelareascore.dedupe import HotelRecord, dedupe_hotels, haversine_m, normalize_name


def test_normalize_name_case_and_punctuation():
    assert normalize_name("The Savoy Hotel!") == normalize_name("the savoy hotel")


def test_normalize_name_accents():
    assert normalize_name("Hôtel Café") == normalize_name("Hotel Cafe")


def test_normalize_name_empty():
    assert normalize_name("") == ""
    assert normalize_name(None) == ""


def test_haversine_known_distance():
    # ~111.2 km per degree of latitude at the equator.
    d = haversine_m(0.0, 0.0, 1.0, 0.0)
    assert 110_000 < d < 112_000


def test_haversine_zero_for_same_point():
    assert haversine_m(51.5, -0.1, 51.5, -0.1) == 0.0


def _rec(id_, name, lat, lon, confidence=0.9, n_sources=1, taxonomy_primary="hotel"):
    return HotelRecord(id=id_, name=name, lat=lat, lon=lon, confidence=confidence, n_sources=n_sources, taxonomy_primary=taxonomy_primary)


def test_dedupe_merges_same_name_within_proximity():
    records = [
        _rec("a", "The Savoy Hotel", 51.5100, -0.1200, confidence=0.95),
        _rec("b", "The Savoy Hotel", 51.51001, -0.12001, confidence=0.80),  # ~1m away
    ]
    results = dedupe_hotels(records, proximity_m=25.0)
    assert len(results) == 1
    assert results[0].method == "normalized_name+proximity"
    assert results[0].canonical_id == "a"  # higher confidence wins
    assert set(results[0].member_ids) == {"a", "b"}


def test_dedupe_never_merges_different_names_even_if_coincident():
    records = [
        _rec("a", "The Savoy Hotel", 51.5100, -0.1200),
        _rec("b", "River Room, The Savoy", 51.5100, -0.1200),  # same point, different name
    ]
    results = dedupe_hotels(records, proximity_m=25.0)
    assert len(results) == 2
    assert all(r.method == "none" for r in results)


def test_dedupe_never_merges_same_name_far_apart_chain_branches():
    records = [
        _rec("a", "Premier Inn", 51.50, -0.10),
        _rec("b", "Premier Inn", 51.60, -0.20),  # different branch, km away
    ]
    results = dedupe_hotels(records, proximity_m=25.0)
    assert len(results) == 2


def test_dedupe_single_record_untouched():
    results = dedupe_hotels([_rec("a", "Solo Hotel", 51.5, -0.1)])
    assert len(results) == 1
    assert results[0].method == "none"
    assert results[0].dedupe_confidence == 100.0
