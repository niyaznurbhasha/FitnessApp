#!/usr/bin/env python3
"""
Simple database migration script to add meal batching tables.
Run this to add the new tables for the meal batching functionality.
"""

from app.models import init_db

def main():
    print("Adding meal batching tables to database...")
    init_db()
    print("✅ Database migration completed!")
    print("New tables added:")
    print("  - raw_meal_inputs (stores raw meal text before processing)")
    print("  - daily_nutrition_summaries (stores processed daily summaries)")

if __name__ == "__main__":
    main()
