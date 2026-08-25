from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Integer, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import config

engine = create_async_engine(config.DATABASE_URL, pool_pre_ping=True)
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Lead(Base):
    """Одна строка на пользователя: повторная заявка обновляет существующую."""

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    name: Mapped[str] = mapped_column(String(128))
    city: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    def __repr__(self) -> str:
        return f"<Lead id={self.id} tg_id={self.tg_id} name={self.name!r} city={self.city!r}>"


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_db() -> None:
    await engine.dispose()


async def save_lead(tg_id: int, username: str | None, name: str, city: str) -> Lead:
    """Создаёт заявку или обновляет существующую для того же tg_id."""
    async with Session() as session, session.begin():
        lead = await session.scalar(select(Lead).where(Lead.tg_id == tg_id))
        if lead is None:
            lead = Lead(tg_id=tg_id, username=username, name=name, city=city)
            session.add(lead)
        else:
            lead.username = username
            lead.name = name
            lead.city = city
        await session.flush()
        return lead


async def count_leads() -> int:
    async with Session() as session:
        return await session.scalar(select(func.count()).select_from(Lead)) or 0


async def list_leads(limit: int, offset: int = 0) -> Sequence[Lead]:
    async with Session() as session:
        result = await session.scalars(
            select(Lead)
            .order_by(Lead.created_at.desc(), Lead.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.all()
