from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.search_history import SearchHistory


class SearchHistoryRepository:
    """Repository for user search logs and trending queries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_search(
        self,
        user_id: int,
        query: str,
        result_count: int,
        filter_type: Optional[str] = None
    ) -> SearchHistory:
        """Record search query."""
        history = SearchHistory(
            user_id=user_id,
            query=query[:255],
            result_count=result_count,
            filter_type=filter_type
        )
        self.session.add(history)
        await self.session.flush()
        return history

    async def get_recent_searches(self, user_id: int, limit: int = 5) -> List[str]:
        """Get recent distinct search queries by user."""
        stmt = (
            select(SearchHistory.query)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit * 2)
        )
        result = await self.session.execute(stmt)
        seen = set()
        queries = []
        for q in result.scalars().all():
            if q not in seen:
                seen.add(q)
                queries.append(q)
            if len(queries) >= limit:
                break
        return queries
