"""Initial schema: regions, metrics, metric_values

Revision ID: 0001
Revises:
Create Date: 2026-10-31
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

region_level = sa.Enum("county", "subdivision", name="region_level")
dataset_name = sa.Enum("housing", "demographics", name="dataset_name")


def upgrade() -> None:
    op.create_table(
        "regions",
        sa.Column("geoid", sa.String(10), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("level", region_level, nullable=False),
        sa.Column("county_geoid", sa.String(10), nullable=True),
        sa.CheckConstraint(
            "(level = 'county' AND county_geoid IS NULL AND length(geoid) = 5)"
            " OR (level = 'subdivision' AND county_geoid IS NOT NULL AND length(geoid) = 10)",
            name=op.f("ck_regions_level_matches_geoid"),
        ),
        sa.ForeignKeyConstraint(
            ["county_geoid"], ["regions.geoid"],
            name=op.f("fk_regions_county_geoid_regions"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("geoid", name=op.f("pk_regions")),
    )
    op.create_index(op.f("ix_regions_county_geoid"), "regions", ["county_geoid"])

    op.create_table(
        "metrics",
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("dataset", dataset_name, nullable=False),
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


def downgrade() -> None:
    op.drop_index("ix_metric_values_metric_year", table_name="metric_values")
    op.drop_table("metric_values")
    op.drop_index(op.f("ix_metrics_dataset"), table_name="metrics")
    op.drop_table("metrics")
    op.drop_index(op.f("ix_regions_county_geoid"), table_name="regions")
    op.drop_table("regions")
    dataset_name.drop(op.get_bind(), checkfirst=True)
    region_level.drop(op.get_bind(), checkfirst=True)
