"""Replace metrics and metric_values with demographics and housing tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_metric_values_metric_year", table_name="metric_values")
    op.drop_table("metric_values")
    op.drop_index(op.f("ix_metrics_dataset"), table_name="metrics")
    op.drop_table("metrics")
    sa.Enum(name="dataset_name").drop(op.get_bind(), checkfirst=True)

    op.create_table(
        "demographics",
        sa.Column("geoid", sa.String(10), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("period_label", sa.String(16), nullable=False),
        sa.Column("total_population", sa.Integer(), nullable=False),
        sa.Column("white", sa.Integer(), nullable=False),
        sa.Column("black", sa.Integer(), nullable=False),
        sa.Column("native_american", sa.Integer(), nullable=False),
        sa.Column("asian", sa.Integer(), nullable=False),
        sa.Column("pacific_islander", sa.Integer(), nullable=False),
        sa.Column("other_race", sa.Integer(), nullable=False),
        sa.Column("two_or_more", sa.Integer(), nullable=False),
        sa.CheckConstraint("year BETWEEN 1990 AND 2100", name=op.f("ck_demographics_year_range")),
        sa.ForeignKeyConstraint(
            ["geoid"], ["regions.geoid"],
            name=op.f("fk_demographics_geoid_regions"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("geoid", "year", name=op.f("pk_demographics")),
    )
    op.create_index("ix_demographics_year", "demographics", ["year"])

    op.create_table(
        "housing_prices",
        sa.Column("geoid", sa.String(10), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("zillow_region_id", sa.Integer(), nullable=True),
        sa.Column("zhvi_usd", sa.Double(), nullable=True),
        sa.Column("zhvi_months_observed", sa.SmallInteger(), nullable=True),
        sa.Column("zori_usd", sa.Double(), nullable=True),
        sa.Column("zori_months_observed", sa.SmallInteger(), nullable=True),
        sa.Column("fhfa_annual_change_pct", sa.Double(), nullable=True),
        sa.Column("fhfa_hpi_native", sa.Double(), nullable=True),
        sa.Column("fhfa_hpi_1990_base", sa.Double(), nullable=True),
        sa.Column("fhfa_hpi_2000_base", sa.Double(), nullable=True),
        sa.CheckConstraint("length(geoid) = 5", name=op.f("ck_housing_prices_county_only")),
        sa.CheckConstraint("year BETWEEN 1990 AND 2100", name=op.f("ck_housing_prices_year_range")),
        sa.ForeignKeyConstraint(
            ["geoid"], ["regions.geoid"],
            name=op.f("fk_housing_prices_geoid_regions"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("geoid", "year", name=op.f("pk_housing_prices")),
    )
    op.create_index("ix_housing_prices_year", "housing_prices", ["year"])

    op.create_table(
        "housing_prices_monthly",
        sa.Column("geoid", sa.String(10), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("month", sa.SmallInteger(), nullable=False),
        sa.Column("zhvi_usd", sa.Double(), nullable=True),
        sa.Column("zori_usd", sa.Double(), nullable=True),
        sa.CheckConstraint("length(geoid) = 5", name=op.f("ck_housing_prices_monthly_county_only")),
        sa.CheckConstraint("month BETWEEN 1 AND 12", name=op.f("ck_housing_prices_monthly_month_range")),
        sa.CheckConstraint("year BETWEEN 1990 AND 2100", name=op.f("ck_housing_prices_monthly_year_range")),
        sa.ForeignKeyConstraint(
            ["geoid"], ["regions.geoid"],
            name=op.f("fk_housing_prices_monthly_geoid_regions"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("geoid", "year", "month", name=op.f("pk_housing_prices_monthly")),
    )


def downgrade() -> None:
    op.drop_table("housing_prices_monthly")
    op.drop_index("ix_housing_prices_year", table_name="housing_prices")
    op.drop_table("housing_prices")
    op.drop_index("ix_demographics_year", table_name="demographics")
    op.drop_table("demographics")

    op.create_table(
        "metrics",
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("dataset", sa.Enum("housing", "demographics", name="dataset_name"), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("format", sa.String(16), nullable=False),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_metrics")),
    )
    op.create_index(op.f("ix_metrics_dataset"), "metrics", ["dataset"])
    op.create_table(
        "metric_values",
        sa.Column("geoid", sa.String(10), nullable=False),
        sa.Column("metric_key", sa.String(64), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("value", sa.Double(), nullable=False),
        sa.Column("source", sa.String(32), nullable=True),
        sa.Column("loaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("year BETWEEN 1990 AND 2100", name=op.f("ck_metric_values_year_range")),
        sa.ForeignKeyConstraint(
            ["geoid"], ["regions.geoid"],
            name=op.f("fk_metric_values_geoid_regions"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["metric_key"], ["metrics.key"],
            name=op.f("fk_metric_values_metric_key_metrics"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("geoid", "metric_key", "year", name=op.f("pk_metric_values")),
    )
    op.create_index("ix_metric_values_metric_year", "metric_values", ["metric_key", "year"])
