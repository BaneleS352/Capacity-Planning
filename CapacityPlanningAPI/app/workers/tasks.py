import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from app.application.services import CapacityPlanningService
from app.infrastructure.database.session import AsyncSessionFactory
from app.models import OutboxEvent
from app.workers.celery_app import celery_app


def enqueue_capacity_recalculation(organization_id: UUID, sprint_id: UUID) -> None:
    celery_app.send_task(
        "capacity.recalculate", args=[str(organization_id), str(sprint_id)], queue="planning"
    )


@celery_app.task(
    name="capacity.recalculate",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)  # type: ignore[untyped-decorator]
def recalculate_capacity(organization_id: str, sprint_id: str) -> str:
    async def run() -> str:
        async with AsyncSessionFactory() as session:
            await CapacityPlanningService(session).recalculate(
                UUID(organization_id), UUID(sprint_id)
            )
        return sprint_id

    return asyncio.run(run())


@celery_app.task(
    name="outbox.publish",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
)  # type: ignore[untyped-decorator]
def publish_outbox() -> int:
    async def run() -> int:
        async with AsyncSessionFactory() as session:
            events = list(
                await session.scalars(
                    select(OutboxEvent)
                    .where(OutboxEvent.published_at.is_(None))
                    .order_by(OutboxEvent.occurred_at)
                    .with_for_update(skip_locked=True)
                    .limit(100)
                )
            )
            # Event-type handlers can be split by queue without changing transaction producers.
            for event in events:
                if event.event_type in {
                    "JiraIssueUpdated",
                    "PaySpaceLeaveUpdated",
                    "EmployeeTeamChanged",
                    "SprintStarted",
                }:
                    sprint_id = event.payload.get("sprint_id")
                    if sprint_id:
                        celery_app.send_task(
                            "capacity.recalculate",
                            args=[str(event.organization_id), sprint_id],
                            queue="planning",
                        )
                event.published_at = datetime.now(UTC)
                event.attempts += 1
            await session.commit()
            return len(events)

    return asyncio.run(run())
