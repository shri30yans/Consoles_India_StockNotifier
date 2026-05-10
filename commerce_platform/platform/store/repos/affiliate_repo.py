"""Affiliate repository — tracks clicks, earnings, and programs."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Literal

import asyncpg

from commerce_platform.platform.store.repos.affiliate_repo import (
    AffiliateProgramRow,
    ClickLogRow,
    DailyAffiliateStatsRow,
    EarningsRow,
)

logger = logging.getLogger(__name__)


class AffiliateRepo:
    def __init__(self, pool: asyncpg.pool.Pool) -> None:
        self._pool = pool

    def _row_to_program(self, row: asyncpg.Record) -> AffiliateProgramRow:
        return AffiliateProgramRow(
            id=row["id"],
            retailer=row["retailer"],
            name=row["name"],
            affiliate_tag=row["affiliate_tag"],
            affiliate_param=row["affiliate_param"],
            default_tag=row["default_tag"],
            enabled=row["enabled"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_click(self, row: asyncpg.Record) -> ClickLogRow:
        return ClickLogRow(
            id=row["id"],
            deal_id=row["deal_id"],
            product_id=row["product_id"],
            retailer=row["retailer"],
            source_url=row["source_url"],
            destination_url=row["destination_url"],
            affiliate_tag=row["affiliate_tag"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            clicked_at=row["clicked_at"],
        )

    def _row_to_earnings(self, row: asyncpg.Record) -> EarningsRow:
        return EarningsRow(
            id=row["id"],
            program_id=row["program_id"],
            retailer=row["retailer"],
            reporting_period=row["reporting_period"],
            clicks=row["clicks"],
            conversions=row["conversions"],
            revenue_paise=row["revenue_paise"],
            commission_paise=row["commission_paise"],
            currency=row["currency"],
            report_date=row["report_date"],
            raw_data=row["raw_data"],
            ingested_at=row["ingested_at"],
        )

    def _row_to_daily_stats(self, row: asyncpg.Record) -> DailyAffiliateStatsRow:
        return DailyAffiliateStatsRow(
            id=row["id"],
            date=row["date"],
            retailer=row["retailer"],
            clicks=row["clicks"],
            conversions=row["conversions"],
            revenue_paise=row["revenue_paise"],
            commission_paise=row["commission_paise"],
            updated_at=row["updated_at"],
        )

    async def list_programs(self, *, enabled: bool | None = None) -> list[AffiliateProgramRow]:
        query = "SELECT * FROM affiliate_programs"
        params: list[Any] = []
        if enabled is not None:
            query += f" WHERE enabled = ${len(params) + 1}"
            params.append(enabled)
        query += " ORDER BY retailer"
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        return [self._row_to_program(row) for row in rows]

    async def get_program(self, program_id: int) -> AffiliateProgramRow | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM affiliate_programs WHERE id = $1", program_id)
        return self._row_to_program(row) if row else None

    async def get_program_by_retailer(self, retailer: str) -> AffiliateProgramRow | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM affiliate_programs WHERE retailer = $1 AND enabled = true",
                retailer,
            )
        return self._row_to_program(row) if row else None

    async def upsert_program(
        self,
        retailer: str,
        name: str,
        affiliate_tag: str | None = None,
        affiliate_param: str = "ref",
        default_tag: bool = False,
        enabled: bool = True,
    ) -> AffiliateProgramRow:
        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO affiliate_programs
                (retailer, name, affiliate_tag, affiliate_param, default_tag, enabled, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $7)
                ON CONFLICT (retailer) DO UPDATE SET
                    name = EXCLUDED.name,
                    affiliate_tag = COALESCE(EXCLUDED.affiliate_tag, affiliate_programs.affiliate_tag),
                    affiliate_param = EXCLUDED.affiliate_param,
                    default_tag = EXCLUDED.default_tag,
                    enabled = EXCLUDED.enabled,
                    updated_at = EXCLUDED.updated_at
                RETURNING *
                """,
                retailer,
                name,
                affiliate_tag,
                affiliate_param,
                default_tag,
                enabled,
                now,
            )
        return self._row_to_program(row)

    async def update_program_tag(self, program_id: int, affiliate_tag: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE affiliate_programs SET affiliate_tag = $1, updated_at = $2 WHERE id = $3",
                affiliate_tag,
                now,
                program_id,
            )

    async def log_click(
        self,
        retailer: str,
        source_url: str,
        destination_url: str,
        affiliate_tag: str | None = None,
        deal_id: int | None = None,
        product_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ClickLogRow:
        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO affiliate_clicks
                (deal_id, product_id, retailer, source_url, destination_url, affiliate_tag,
                 ip_address, user_agent, clicked_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
                """,
                deal_id,
                product_id,
                retailer,
                source_url,
                destination_url,
                affiliate_tag,
                ip_address,
                user_agent,
                now,
            )
        return self._row_to_click(row)

    async def get_clicks(
        self,
        *,
        retailer: str | None = None,
        deal_id: int | None = None,
        product_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ClickLogRow]:
        query = "SELECT * FROM affiliate_clicks WHERE 1=1"
        params: list[Any] = []
        if retailer:
            query += f" AND retailer = ${len(params) + 1}"
            params.append(retailer)
        if deal_id:
            query += f" AND deal_id = ${len(params) + 1}"
            params.append(deal_id)
        if product_id:
            query += f" AND product_id = ${len(params) + 1}"
            params.append(product_id)
        if start_date:
            query += f" AND clicked_at::DATE >= ${len(params) + 1}::DATE"
            params.append(start_date)
        if end_date:
            query += f" AND clicked_at::DATE <= ${len(params) + 1}::DATE"
            params.append(end_date)
        query += f" ORDER BY clicked_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        return [self._row_to_click(row) for row in rows]

    async def get_click_counts(
        self,
        *,
        retailer: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, int]:
        query = "SELECT COUNT(*) FROM affiliate_clicks WHERE 1=1"
        params: list[Any] = []
        if retailer:
            query += f" AND retailer = ${len(params) + 1}"
            params.append(retailer)
        if start_date:
            query += f" AND clicked_at::DATE >= ${len(params) + 1}::DATE"
            params.append(start_date)
        if end_date:
            query += f" AND clicked_at::DATE <= ${len(params) + 1}::DATE"
            params.append(end_date)
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
        return {"total_clicks": row["count"] if row else 0}

    async def ingest_earnings(
        self,
        program_id: int,
        retailer: str,
        reporting_period: str,
        clicks: int,
        conversions: int,
        revenue_paise: int,
        commission_paise: int,
        currency: str,
        report_date: str,
        raw_data: str | None = None,
    ) -> EarningsRow:
        now = datetime.now(timezone.utc).isoformat()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO affiliate_earnings
                (program_id, retailer, reporting_period, clicks, conversions, revenue_paise,
                 commission_paise, currency, report_date, raw_data, ingested_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (program_id, reporting_period) DO UPDATE SET
                    clicks = EXCLUDED.clicks,
                    conversions = EXCLUDED.conversions,
                    revenue_paise = EXCLUDED.revenue_paise,
                    commission_paise = EXCLUDED.commission_paise,
                    report_date = EXCLUDED.report_date,
                    raw_data = COALESCE(EXCLUDED.raw_data, affiliate_earnings.raw_data),
                    ingested_at = EXCLUDED.ingested_at
                RETURNING *
                """,
                program_id,
                retailer,
                reporting_period,
                clicks,
                conversions,
                revenue_paise,
                commission_paise,
                currency,
                report_date,
                raw_data or "{}",
                now,
            )
        return self._row_to_earnings(row)

    async def list_earnings(
        self,
        *,
        program_id: int | None = None,
        retailer: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EarningsRow]:
        query = "SELECT * FROM affiliate_earnings WHERE 1=1"
        params: list[Any] = []
        if program_id:
            query += f" AND program_id = ${len(params) + 1}"
            params.append(program_id)
        if retailer:
            query += f" AND retailer = ${len(params) + 1}"
            params.append(retailer)
        query += " ORDER BY report_date DESC"
        query += f" LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        return [self._row_to_earnings(row) for row in rows]

    async def get_total_earnings(
        self,
        *,
        retailer: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        query = """
            SELECT
                COALESCE(SUM(clicks), 0) as total_clicks,
                COALESCE(SUM(conversions), 0) as total_conversions,
                COALESCE(SUM(revenue_paise), 0) as total_revenue_paise,
                COALESCE(SUM(commission_paise), 0) as total_commission_paise
            FROM affiliate_earnings WHERE 1=1
        """
        params: list[Any] = []
        if retailer:
            query += f" AND retailer = ${len(params) + 1}"
            params.append(retailer)
        if start_date:
            query += f" AND report_date >= $${len(params) + 1}"
            params.append(start_date)
        if end_date:
            query += f" AND report_date <= $${len(params) + 1}"
            params.append(end_date)
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
        if not row:
            return {
                "total_clicks": 0,
                "total_conversions": 0,
                "total_revenue_paise": 0,
                "total_commission_paise": 0,
            }
        return dict(row)

    async def get_daily_stats(
        self,
        *,
        retailer: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 90,
    ) -> list[DailyAffiliateStatsRow]:
        query = """
            SELECT
                clicked_at::DATE as date,
                retailer,
                COUNT(*) as clicks,
                0 as conversions,
                0 as revenue_paise,
                0 as commission_paise,
                NOW() as updated_at
            FROM affiliate_clicks WHERE 1=1
        """
        params: list[Any] = []
        if retailer:
            query += f" AND retailer = ${len(params) + 1}"
            params.append(retailer)
        if start_date:
            query += f" AND clicked_at::DATE >= ${len(params) + 1}::DATE"
            params.append(start_date)
        if end_date:
            query += f" AND clicked_at::DATE <= ${len(params) + 1}::DATE"
            params.append(end_date)
        query += f" GROUP BY clicked_at::DATE, retailer ORDER BY date DESC LIMIT ${len(params) + 1}"
        params.append(limit)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        return [self._row_to_daily_stats(row) for row in rows]

    async def get_earnings_by_retailer(self) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    retailer,
                    SUM(clicks) as total_clicks,
                    SUM(conversions) as total_conversions,
                    SUM(revenue_paise) as total_revenue_paise,
                    SUM(commission_paise) as total_commission_paise,
                    MAX(report_date) as last_report_date
                FROM affiliate_earnings
                GROUP BY retailer
                ORDER BY total_commission_paise DESC
                """
            )
        return [dict(row) for row in rows]
