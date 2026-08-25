import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///bot_database.db"


def _parse_admin_ids(raw: str) -> tuple[int, ...]:
    """ADMIN_IDS из .env: '123, 456' -> (123, 456). Дубликаты и пробелы отбрасываются."""
    ids: list[int] = []
    for chunk in raw.replace(";", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if not chunk.isdigit():
            raise ValueError(f"ADMIN_IDS: '{chunk}' не похож на Telegram ID")
        ids.append(int(chunk))
    return tuple(dict.fromkeys(ids))


@dataclass(frozen=True)
class Config:
    BOT_TOKEN: str
    ADMIN_IDS: tuple[int, ...]
    DATABASE_URL: str

    @classmethod
    def from_env(cls) -> "Config":
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError("BOT_TOKEN не задан. Заполните .env (см. .env.example).")

        admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
        if not admin_ids:
            raise RuntimeError("ADMIN_IDS не заданы — админ-команды будут недоступны никому.")

        return cls(
            BOT_TOKEN=token,
            ADMIN_IDS=admin_ids,
            DATABASE_URL=os.getenv("DATABASE_URL", "").strip() or DEFAULT_DATABASE_URL,
        )

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.ADMIN_IDS


config = Config.from_env()
