#!/usr/bin/env python3
"""Create database tables using SQLAlchemy ORM models"""

import os
import sys
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.base import Base
from app.db.database import engine
from sqlalchemy import text

try:
    print("[INFO] Creating tables from ORM models...")
    Base.metadata.create_all(bind=engine)
    print("[OK] All tables created")
    
    # Verify
    print("\n[INFO] Verifying tables...")
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = sorted([row[0] for row in result])
        print(f"[OK] Tables created: {', '.join(tables)}")
        print(f"\n[SUCCESS] Database initialization complete!")
        print(f"[INFO] Total tables: {len(tables)}")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
