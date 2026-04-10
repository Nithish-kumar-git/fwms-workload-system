#!/bin/bash
# Apply migration 034 to seed MCA odd semester subjects

# Get DATABASE_URL from .env
if [ -f .env ]; then
    export $(cat .env | grep DATABASE_URL | xargs)
fi

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not found in .env"
    exit 1
fi

echo "Applying migration 034: Seed MCA odd semesters and fix duplicate programs..."
psql "$DATABASE_URL" -f migrations/034_seed_mca_odd_semesters.sql

if [ $? -eq 0 ]; then
    echo "✓ Migration 034 applied successfully"
else
    echo "✗ Migration 034 failed"
    exit 1
fi
