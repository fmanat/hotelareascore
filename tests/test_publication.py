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
    publication.set_status(con, "hotel", "h1", "indexable", "pilot cohort", "system:test")
    row = publication.get_status(con, "hotel", "h1")
    assert row["status"] == "indexable"
    assert row["reason"] == "pilot cohort"
    assert row["decided_by"] == "system:test"
    assert publication.is_indexable(con, "hotel", "h1") is True


def test_reason_required(con):
    with pytest.raises(ValueError):
        publication.set_status(con, "hotel", "h1", "indexable", "", "system:test")
    with pytest.raises(ValueError):
        publication.set_status(con, "hotel", "h1", "indexable", "   ", "system:test")


def test_invalid_status_rejected(con):
    with pytest.raises(ValueError):
        publication.set_status(con, "hotel", "h1", "published", "reason", "system:test")


def test_invalid_page_type_rejected(con):
    with pytest.raises(ValueError):
        publication.set_status(con, "restaurant", "h1", "indexable", "reason", "system:test")


def test_updating_status_overwrites_not_duplicates(con):
    publication.set_status(con, "hotel", "h1", "noindex", "default", "system:test")
    publication.set_status(con, "hotel", "h1", "indexable", "promoted to pilot cohort", "system:test2")
    row = publication.get_status(con, "hotel", "h1")
    assert row["status"] == "indexable"
    assert row["reason"] == "promoted to pilot cohort"
    rows = publication.list_by_status(con, "indexable", "hotel")
    assert len(rows) == 1


def test_list_by_status_filters_by_page_type(con):
    publication.set_status(con, "hotel", "h1", "indexable", "r", "system:test")
    publication.set_status(con, "city", "london", "indexable", "r", "system:test")
    hotel_rows = publication.list_by_status(con, "indexable", "hotel")
    all_rows = publication.list_by_status(con, "indexable")
    assert len(hotel_rows) == 1
    assert len(all_rows) == 2
