import pytest

from hotelareascore import publication


@pytest.fixture
def con(tmp_path):
    with publication.connect(tmp_path / "test.sqlite") as c:
        yield c


def test_unrecorded_page_is_not_indexable(con):
    assert publication.get_status(con, "hotel", "unknown-id") is None
    assert publication.is_indexable(con, "hotel", "unknown-id") is False


def test_set_and_get_status_roundtrip(con):
    publication.set_status(con, "hotel", "h1", "indexable", "pilot cohort", "system:test", accommodation_type="hotel", name_index_eligible=True)
    row = publication.get_status(con, "hotel", "h1")
    assert row["status"] == "indexable"
    assert row["reason"] == "pilot cohort"
    assert row["decided_by"] == "system:test"
    assert publication.is_indexable(con, "hotel", "h1") is True


def test_reason_required(con):
    with pytest.raises(ValueError):
        publication.set_status(con, "hotel", "h1", "indexable", "", "system:test", accommodation_type="hotel", name_index_eligible=True)
    with pytest.raises(ValueError):
        publication.set_status(con, "hotel", "h1", "indexable", "   ", "system:test", accommodation_type="hotel", name_index_eligible=True)


def test_invalid_status_rejected(con):
    with pytest.raises(ValueError):
        publication.set_status(con, "hotel", "h1", "published", "reason", "system:test")


def test_invalid_page_type_rejected(con):
    with pytest.raises(ValueError):
        publication.set_status(con, "restaurant", "h1", "indexable", "reason", "system:test")


def test_updating_status_overwrites_not_duplicates(con):
    publication.set_status(con, "hotel", "h1", "noindex", "default", "system:test")
    publication.set_status(con, "hotel", "h1", "indexable", "promoted to pilot cohort", "system:test2", accommodation_type="hotel", name_index_eligible=True)
    row = publication.get_status(con, "hotel", "h1")
    assert row["status"] == "indexable"
    assert row["reason"] == "promoted to pilot cohort"
    rows = publication.list_by_status(con, "indexable", "hotel")
    assert len(rows) == 1


def test_list_by_status_filters_by_page_type(con):
    publication.set_status(con, "hotel", "h1", "indexable", "r", "system:test", accommodation_type="hotel", name_index_eligible=True)
    publication.set_status(con, "city", "london", "indexable", "r", "system:test")
    hotel_rows = publication.list_by_status(con, "indexable", "hotel")
    all_rows = publication.list_by_status(con, "indexable")
    assert len(hotel_rows) == 1
    assert len(all_rows) == 2


# docs/adr/014: numeric-name hotels are structurally barred from ever
# being 'indexable', independent of confidence -- docs/reports/
# nyc-bbox-options.md's finding was that confidence alone doesn't catch
# this, so the gate lives in set_status itself, not a caller's judgment.
def test_numeric_name_hotel_cannot_be_marked_indexable(con):
    with pytest.raises(ValueError, match="numeric-name"):
        publication.set_status(con, "hotel", "h1", "indexable", "r", "system:test", hotel_name="8468671", accommodation_type="hotel", name_index_eligible=True)
    assert publication.get_status(con, "hotel", "h1") is None


def test_numeric_name_gate_is_trimmed_like_the_slug_helper(con):
    with pytest.raises(ValueError):
        publication.set_status(con, "hotel", "h1", "indexable", "r", "system:test", hotel_name="  86  ", accommodation_type="hotel", name_index_eligible=True)


def test_numeric_name_hotel_can_still_be_draft_or_noindex(con):
    # The gate is specifically about 'indexable' -- a numeric-name hotel
    # still needs a real (non-indexable) recorded status, same as any
    # other hotel (compute_publication.py puts these in 'draft').
    publication.set_status(con, "hotel", "h1", "draft", "numeric name", "system:test", hotel_name="8468671")
    publication.set_status(con, "hotel", "h1", "noindex", "numeric name", "system:test", hotel_name="8468671")
    assert publication.get_status(con, "hotel", "h1")["status"] == "noindex"


def test_non_numeric_name_hotel_is_unaffected_by_the_gate(con):
    publication.set_status(con, "hotel", "h1", "indexable", "r", "system:test", hotel_name="The Savoy Hotel", accommodation_type="hotel", name_index_eligible=True)
    assert publication.is_indexable(con, "hotel", "h1") is True


def test_numeric_name_gate_only_applies_when_a_name_is_given(con):
    # Static/city callers don't pass hotel_name at all -- the gate must
    # not accidentally block them (it's specific to page_type == "hotel"
    # AND a name being provided).
    publication.set_status(con, "city", "london", "indexable", "r", "system:test")
    publication.set_status(con, "hotel", "h1", "indexable", "r", "system:test", accommodation_type="hotel", name_index_eligible=True)  # no hotel_name passed
    assert publication.is_indexable(con, "city", "london") is True
    assert publication.is_indexable(con, "hotel", "h1") is True
