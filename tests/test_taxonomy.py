from hotelareascore import taxonomy


def test_is_hotel_type_included():
    assert taxonomy.is_hotel_type("hotel")
    assert taxonomy.is_hotel_type("hostel")
    assert taxonomy.is_hotel_type("bed_and_breakfast")


def test_is_hotel_type_excludes_out_of_scope_lodging():
    assert not taxonomy.is_hotel_type("holiday_rental_home")
    assert not taxonomy.is_hotel_type("campground")
    assert not taxonomy.is_hotel_type("lodging")  # generic/unclassified leaf


def test_is_hotel_type_excludes_non_lodging():
    assert not taxonomy.is_hotel_type("restaurant")
    assert not taxonomy.is_hotel_type(None)
    assert not taxonomy.is_hotel_type("")


def test_included_and_excluded_are_disjoint():
    included = taxonomy.hotel_included_types()
    excluded = taxonomy.hotel_excluded_types()
    assert included & excluded == set()


def test_hotel_sql_predicate_contains_all_included_types():
    predicate = taxonomy.hotel_sql_predicate()
    for t in taxonomy.hotel_included_types():
        assert f"'{t}'" in predicate


def test_matches_point_dimension_category_leaf():
    assert taxonomy.matches_point_dimension("food_essentials", "restaurant", ["food_and_drink", "restaurant"])
    assert not taxonomy.matches_point_dimension("food_essentials", "hair_salon", ["lifestyle_services"])


def test_matches_point_dimension_hierarchy_family():
    assert taxonomy.matches_point_dimension("walkability_density", "hair_salon", ["lifestyle_services", "hair_salon"])
    assert not taxonomy.matches_point_dimension("walkability_density", "train_station", ["travel_and_transportation"])


def test_matches_point_dimension_rejects_quietness_proxy():
    import pytest

    with pytest.raises(ValueError):
        taxonomy.matches_point_dimension("quietness_proxy", "bar", ["food_and_drink"])


def test_poi_sql_predicate_builds_valid_or_clause():
    sql = taxonomy.poi_sql_predicate("nightlife_access")
    assert "taxonomy.primary IN" in sql
    assert sql.strip().startswith("(") and sql.strip().endswith(")")


def test_quietness_config_has_required_keys():
    cfg = taxonomy.quietness_config()
    for key in ("major_road_radius_m", "rail_radius_m", "nightlife_radius_m", "airport_radius_m", "road_classes"):
        assert key in cfg
