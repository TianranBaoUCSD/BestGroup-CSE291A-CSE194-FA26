# Bay Area Housing Data

County-level housing data for the nine Bay Area counties, covering
2000–2025 where available.

## Datasets

- Zillow ZHVI: typical home values in USD, 2000–2025.
- Zillow ZORI: typical monthly market rents in USD, available from 2015,
  with county-specific gaps.
- FHFA HPI: annual house price indices, 2000–2025.
  These are index values, not dollar prices.

## How to Run

1. Open `clean_county_housing.ipynb` in Jupyter Notebook or VS Code.
2. Keep these original files in the same folder as the notebook:
   - `County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv`
   - `County_zori_uc_sfrcondomfr_sm_month.csv`
   - `hpi_at_county (1).xlsx`
3. Install the required packages:
   `pip install pandas openpyxl`
4. Run all cells from top to bottom.

## Outputs

Cleaned CSV files are saved in `cleaned_outputs/`.

The main annual output is:
`bay_area_county_housing_combined_2000_2025.csv`

Each row represents one county and year. Use `COUNTY_FIPS` and `YEAR`
to match housing data with compatible county-level demographic data.
Read `COUNTY_FIPS` as text to preserve leading zeros.

## Missing Values and Annual Summaries

- ZHVI: missing February 2007 for Contra Costa County.
- ZORI: 17 missing monthly observations across Napa County in 2015–2016
  and San Francisco County in 2020.
- FHFA: no missing values within the selected nine counties and 2000–2025.

Missing values remain blank; no interpolation or zero-filling is applied.
Annual Zillow summaries include the number of observed months.
Full-year means are provided only when all 12 months are available.
Annual ZORI means remain in USD per month.

## Sources

- Zillow Research: https://www.zillow.com/research/data/
- FHFA HPI: https://www.fhfa.gov/data/hpi/datasets
