#!/usr/bin/env python3
"""Initialize database with routes and sample data"""

import sys
import os

# Ajoute le chemin du backend au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.database import SessionLocal, engine
    print("Import successful!")
except Exception as e:
    print(f"Import error: {e}")
    print(f"Error type: {type(e)}")
    
    # Essaie d'importer juste database pour voir
    try:
        import app.core.database as db
        print(f"Database module: {db}")
        print(f"Database attributes: {dir(db)}")
    except Exception as e2:
        print(f"Can't import database at all: {e2}")

# Le reste du code...