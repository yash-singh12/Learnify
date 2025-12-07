#!/bin/bash
# MongoDB Backup Script for Learnify
# Backs up the entire database to ./backup directory

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Create backup directory
BACKUP_DIR="./backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "🔄 Starting MongoDB backup..."
echo "Database: $DB_NAME"
echo "Backup location: $BACKUP_DIR"

# Run mongodump
mongodump --uri="$MONGODB_URI" --db="$DB_NAME" --out="$BACKUP_DIR"

echo "✅ Backup completed successfully!"
echo "Backup saved to: $BACKUP_DIR"

# Keep only last 5 backups
cd backup
ls -t | tail -n +6 | xargs -r rm -rf
cd ..

echo "🧹 Old backups cleaned up (keeping last 5)"
