"""Which metrics exist, and which database column holds each one.

The first four metrics of each dataset must match frontend/src/constants.js.
A metric with no "column" has no source in /data yet: the API lists it but
returns no values for it, and the frontend shows "—".
"""

DATASETS: dict[str, dict] = {
    "housing": {
        "label": "Housing",
        "metrics": {
            # Zillow ZHVI: a typical home value, not a true median sale price.
            "median_home_value": {"label": "Median home value", "format": "usd", "column": "zhvi_usd"},
            # Zillow ZORI: a typical market rent, not Census gross rent. Starts in 2015.
            "median_gross_rent": {"label": "Median gross rent", "format": "usd", "column": "zori_usd"},
            "owner_occupied_pct": {"label": "Homeownership rate", "format": "pct"},
            "vacancy_rate_pct": {"label": "Vacancy rate", "format": "pct"},
            "fhfa_hpi_2000_base": {"label": "House price index (2000 = 100)", "format": "int", "column": "fhfa_hpi_2000_base"},
            "fhfa_annual_change_pct": {"label": "House price index, annual change", "format": "pct", "column": "fhfa_annual_change_pct"},
        },
    },
    "demographics": {
        "label": "Demographics",
        "metrics": {
            "population": {"label": "Population", "format": "int", "column": "total_population"},
            "median_household_income": {"label": "Median household income", "format": "usd"},
            "median_age": {"label": "Median age", "format": "years"},
            "bachelors_pct": {"label": "Bachelor's degree or higher", "format": "pct"},
            "white_population": {"label": "White alone", "format": "int", "column": "white"},
            "black_population": {"label": "Black or African American alone", "format": "int", "column": "black"},
            "native_american_population": {"label": "American Indian and Alaska Native alone", "format": "int", "column": "native_american"},
            "asian_population": {"label": "Asian alone", "format": "int", "column": "asian"},
            "pacific_islander_population": {"label": "Native Hawaiian and Other Pacific Islander alone", "format": "int", "column": "pacific_islander"},
            "other_race_population": {"label": "Some other race alone", "format": "int", "column": "other_race"},
            "two_or_more_races_population": {"label": "Two or more races", "format": "int", "column": "two_or_more"},
        },
    },
}

YEAR_MIN, YEAR_MAX = 2000, 2026

def metric_columns(dataset: str) -> dict[str, str]:
    """{metric key: database column} for the metrics in `dataset` that have data."""
    metrics = DATASETS[dataset]["metrics"]
    return {key: m["column"] for key, m in metrics.items() if "column" in m}


def find_metric(metric: str) -> tuple[str, str | None] | None:
    """(dataset, column) for a metric key, or None if the key is unknown."""
    for name, dataset in DATASETS.items():
        if metric in dataset["metrics"]:
            return name, dataset["metrics"][metric].get("column")
    return None
