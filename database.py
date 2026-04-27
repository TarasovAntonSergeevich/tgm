from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import config

engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(Integer, nullable=False)
    display_name = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    category_choice = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, tg_id={self.tg_id}, name={self.display_name}, city={self.city}, choice={self.category_choice})>"

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_user(tg_id: int, display_name: str, city: str, category_choice: str):
    db = SessionLocal()
    try:
        user = User(
            tg_id=tg_id,
            display_name=display_name,
            city=city,
            category_choice=category_choice
        )
        db.add(user)
        db.commit()
        return user
    finally:
        db.close()

def get_all_users():
    db = SessionLocal()
    try:
        return db.query(User).all()
    finally:
        db.close()