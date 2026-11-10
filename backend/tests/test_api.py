from app import metrics_config

from .conftest import ALAMEDA, MARIN, OAKLAND


def get_metrics(client, dataset, year):
    return client.get("/api/metrics", params={"dataset": dataset, "year": year}).json()


def test_housing_exact_year(client):
    body = get_metrics(client, "housing", 2020)
    assert body["data_year"] == 2020
    assert body["values"][ALAMEDA]["median_home_value"] == 950000
    assert body["values"][ALAMEDA]["median_gross_rent"] == 2500
    assert "population" not in body["values"][ALAMEDA]


def test_demographics_exact_year(client):
    body = get_metrics(client, "demographics", 2012)
    assert body["data_year"] == 2012
    assert body["values"][ALAMEDA]["population"] == 1500000
    assert body["values"][ALAMEDA]["white_population"] == 1500000
    assert "median_home_value" not in body["values"][ALAMEDA]


def test_only_counties_are_returned(client):
    for dataset, year in (("housing", 2020), ("demographics", 2020), ("demographics", 2009)):
        assert all(len(geoid) == 5 for geoid in get_metrics(client, dataset, year)["values"])
    assert set(get_metrics(client, "housing", 2020)["values"]) == {ALAMEDA, MARIN}


def test_uses_latest_earlier_year(client):
    assert get_metrics(client, "housing", 2018)["data_year"] == 2015


def test_before_first_year_uses_earliest(client):
    assert get_metrics(client, "housing", 2003)["data_year"] == 2005


def test_data_year_is_per_dataset(client):
    assert get_metrics(client, "housing", 2012)["data_year"] == 2005
    assert get_metrics(client, "demographics", 2012)["data_year"] == 2012


def test_data_year_ignores_years_with_only_subdivision_data(client):
    assert get_metrics(client, "demographics", 2014)["data_year"] == 2012


def test_missing_value_is_left_out(client):
    assert "median_gross_rent" not in get_metrics(client, "housing", 2005)["values"][ALAMEDA]


def test_metric_with_no_source_has_no_values_or_domain(client):
    body = get_metrics(client, "housing", 2020)
    assert "owner_occupied_pct" not in body["values"][ALAMEDA]
    assert body["domains"]["owner_occupied_pct"] is None


def test_housing_domain_uses_county_values(client):
    lo, hi = get_metrics(client, "housing", 2020)["domains"]["median_home_value"]
    assert 500000 <= lo < hi <= 1200000


def test_demographic_domain_ignores_subdivisions(client):
    lo, hi = get_metrics(client, "demographics", 2020)["domains"]["population"]
    assert 505000 <= lo < hi <= 1600000


def test_unknown_dataset(client):
    assert client.get("/api/metrics", params={"dataset": "nope", "year": 2020}).status_code == 404


def test_series_for_county_housing(client):
    body = client.get("/api/series", params={"geoid": ALAMEDA, "metric": "median_gross_rent"}).json()
    assert body["points"] == [{"year": 2015, "value": 2100}, {"year": 2020, "value": 2500}]


def test_series_for_county_demographics(client):
    body = client.get("/api/series", params={"geoid": ALAMEDA, "metric": "population"}).json()
    assert body["points"] == [
        {"year": 2009, "value": 505000},
        {"year": 2012, "value": 1500000},
        {"year": 2020, "value": 1600000},
    ]


def test_series_rejects_subdivision(client):
    response = client.get("/api/series", params={"geoid": OAKLAND, "metric": "population"})
    assert response.status_code == 404


def test_series_unknown_metric(client):
    assert client.get("/api/series", params={"geoid": ALAMEDA, "metric": "nope"}).status_code == 404


def test_series_metric_with_no_source_is_empty(client):
    body = client.get("/api/series", params={"geoid": ALAMEDA, "metric": "median_age"}).json()
    assert body["points"] == []


def test_health_and_metadata(client):
    expected = [2005, 2009, 2012, 2015, 2020]
    assert client.get("/api/health").json()["years_loaded"] == expected
    body = client.get("/api/metadata").json()
    assert body["years_with_data"] == expected
    assert set(body["datasets"]) == set(metrics_config.DATASETS)


def test_reload_endpoint_is_gone(client):
    assert client.post("/api/reload").status_code in (404, 405)
