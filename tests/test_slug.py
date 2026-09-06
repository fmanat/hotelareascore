from hotelareascore.slug import hotel_slug, slugify


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
