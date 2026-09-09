from hotelareascore.slug import hotel_slug, is_numeric_name, slugify


def test_slugify_basic():
    assert slugify("The Savoy Hotel") == "the-savoy-hotel"


def test_slugify_accents_and_punctuation():
    assert slugify("Hôtel Café de Paris!") == "hotel-cafe-de-paris"


def test_slugify_empty_falls_back():
    assert slugify("") == "hotel"
    assert slugify(None) == "hotel"


def test_hotel_slug_is_stable_and_unique_for_same_brand_name():
    a = hotel_slug("Premier Inn", "08f2a1c3d4e5f6a7")
    b = hotel_slug("Premier Inn", "19a2b3c4d5e6f7a8")
    assert a != b
    assert a.startswith("premier-inn-")
    assert b.startswith("premier-inn-")


def test_hotel_slug_deterministic():
    assert hotel_slug("The Savoy Hotel", "abc12345") == hotel_slug("The Savoy Hotel", "abc12345")


def test_purely_numeric_name_gets_hotel_prefix():
    # docs/reports/nyc-bbox-options.md: a bare numeric string (an unresolved
    # source reference, not a real name) reads as a broken/spam link if
    # slugified as-is ("8468671-f152bc7b") -- the prefix keeps it legible.
    assert slugify("8468671") == "hotel-8468671"
    assert slugify("86") == "hotel-86"


def test_name_with_a_number_but_not_purely_numeric_is_untouched():
    assert slugify("21 Club") == "21-club"
    assert slugify("Hotel 1898") == "hotel-1898"


def test_is_numeric_name():
    # docs/adr/014: single source of truth for the hard indexability gate
    # (publication.py) and validate.py's n_numeric_name QA count.
    assert is_numeric_name("8468671") is True
    assert is_numeric_name("  86  ") is True  # trimmed, like validate.py's trim(name)
    assert is_numeric_name("21 Club") is False
    assert is_numeric_name("Hotel 1898") is False
    assert is_numeric_name("") is False
    assert is_numeric_name(None) is False
