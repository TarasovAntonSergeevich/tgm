from dataclasses import dataclass


@dataclass
class Config:
    BOT_TOKEN: str = ""
    ADMIN_IDS = [969792952]
    DATABASE_URL: str = "sqlite:///bot_database.db"

    def __post_init__(self):
        if self.ADMIN_IDS is None:
            self.ADMIN_IDS = [123456789]


config = Config()