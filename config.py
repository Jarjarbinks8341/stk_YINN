"""Configuration settings for YINN trading system"""
import os
from pathlib import Path

# Database settings
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "yinn.db"
DB_URL = f"sqlite:///{DB_PATH}"

# Trading settings
TICKER = "YINN"
START_DATE = "2025-01-01"

# Ensure data directory exists
DB_PATH.parent.mkdir(exist_ok=True)
