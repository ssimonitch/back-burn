#!/bin/bash

# Slow Burn Local Development Setup Script
# This script sets up the local Supabase environment for development

set -e

echo "🔥 Starting Slow Burn Local Development Environment..."

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found. Please install it:"
    echo "npm install -g supabase"
    exit 1
fi

# Start Supabase services
echo "🚀 Starting Supabase services..."
supabase start

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 5

# Get the connection details
echo ""
echo "📋 Local Supabase Connection Details:"
supabase status

echo ""
echo "🎯 Next steps:"
echo "1. Copy the API URL and anon key to your .env.local file"
echo "2. Run migrations: ./scripts/run-migrations.sh"
echo "3. Start your FastAPI server: poe dev"
echo ""
echo "📖 Access points:"
echo "- Studio: http://127.0.0.1:54323"
echo "- API: http://127.0.0.1:54321"
echo "- Database: postgresql://postgres:postgres@127.0.0.1:54322/postgres"
echo "- Email testing: http://127.0.0.1:54324"