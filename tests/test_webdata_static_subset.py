"""select_static_subset (docs/adr/013): the fix for the STATE.md-flagged
bug where only 2 of 12 cities' indexable hotels actually had a built page.
The one invariant that must never regress: every indexable hotel gets a
real static page, no matter how the file budget or the confidence/
distinctiveness fill logic changes later."""
import pytest

from hotelareascore.webdata import STATIC_HOTEL_PAGE_BUDGET, select_static_subset


def _hotel(slug, *, indexable=False, confidence=50.0, balanced_score=50.0, comparable=None):
    return {
        "slug": slug,
        "publication_status": "indexable" if indexable else "noindex",
        "confidence": confidence,
        "balanced_score": balanced_score,
        "comparable": comparable or [],
    }


def test_every_indexable_hotel_is_in_the_static_subset():
    hotels_by_city = {
        "london": [_hotel(f"london-{i}", indexable=(i < 3)) for i in range(20)],
        "bangkok": [_hotel(f"bangkok-{i}", indexable=(i < 2)) for i in range(20)],
    }
    subset = select_static_subset(hotels_by_city)
    indexable_slugs = {
        h["slug"]
        for city_hotels in hotels_by_city.values()
        for h in city_hotels
        if h["publication_status"] == "indexable"
    }
    assert indexable_slugs <= subset


def test_comparable_links_from_an_indexable_hotel_are_included(monkeypatch):
    # Budget covers exactly {cohort-hotel, linked-hotel} and nothing else,
    # so "linked-hotel" landing in the subset proves the comparable-hotel
    # closure works, not just that the fill step had room to spare.
    monkeypatch.setattr("hotelareascore.webdata.STATIC_HOTEL_PAGE_BUDGET", 2)
    linked = _hotel("linked-hotel")
    indexable = _hotel(
        "cohort-hotel",
        indexable=True,
        comparable=[{"slug": "linked-hotel", "name": "Linked", "balanced_score": 50.0}],
    )
    hotels_by_city = {"london": [indexable, linked] + [_hotel(f"filler-{i}") for i in range(10)]}
    subset = select_static_subset(hotels_by_city)
    assert subset == {"cohort-hotel", "linked-hotel"}


def test_fill_prefers_higher_confidence_and_more_distinctive_hotels(monkeypatch):
    # Tight budget (1 fill slot for this city) so the ranking actually
    # decides who gets in, not "everyone fits anyway". Median balanced_score
    # of this city is 50; "distinctive" sits farther from it than "typical".
    monkeypatch.setattr("hotelareascore.webdata.STATIC_HOTEL_PAGE_BUDGET", 1)
    typical = _hotel("typical", confidence=90.0, balanced_score=51.0)
    distinctive = _hotel("distinctive", confidence=90.0, balanced_score=95.0)
    median_filler = [_hotel(f"median-{i}", confidence=90.0, balanced_score=50.0) for i in range(3)]
    hotels_by_city = {"london": [typical, distinctive] + median_filler}
    subset = select_static_subset(hotels_by_city)
    assert subset == {"distinctive"}


def test_refuses_to_silently_drop_indexable_pages_over_budget(monkeypatch):
    monkeypatch.setattr("hotelareascore.webdata.STATIC_HOTEL_PAGE_BUDGET", 1)
    hotels_by_city = {"london": [_hotel("a", indexable=True), _hotel("b", indexable=True)]}
    with pytest.raises(ValueError, match="exceed"):
        select_static_subset(hotels_by_city)


def test_budget_matches_the_documented_free_tier_margin():
    # docs/reports/hotel-pages-architecture-options.md §4 / docs/adr/013:
    # 20,000-file free tier, 20% margin, 250 files reserved for non-hotel
    # content (city/static pages, build assets, the merged + 192 sharded
    # search index files).
    assert STATIC_HOTEL_PAGE_BUDGET == 15_750
