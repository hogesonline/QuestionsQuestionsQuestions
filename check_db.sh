#!/bin/bash
# Run with bash check_tables.sh

DB="catan.db"

# Check if database exists
if [ ! -f "$DB" ]; then
    echo "Database $DB not found!"
    exit 1
fi

# Display schema
echo "=== Database Schema ==="
sqlite3 "$DB" ".schema"

# Get list of tables
tables=$(sqlite3 "$DB" ".tables")

echo "=== Data from all tables ==="
for table in $tables; do
    echo "--- Table: $table ---"
    sqlite3 "$DB" "SELECT * FROM $table LIMIT 20;"
done
