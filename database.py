"""Database models and setup for YINN trading system"""
from sqlalchemy import create_engine, Column, String, Float, Integer, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import config

Base = declarative_base()

class DailyPrice(Base):
    """Store daily OHLCV data for YINN"""
    __tablename__ = 'daily_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    adj_close = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DailyPrice(ticker={self.ticker}, date={self.date}, close={self.close})>"

def init_db():
    """Initialize the database and create tables"""
    engine = create_engine(config.DB_URL, echo=False)
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Get a database session"""
    engine = create_engine(config.DB_URL, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()
