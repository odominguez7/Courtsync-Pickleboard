#!/bin/bash
# CourtSync - Local Test Script
# Runs the function locally using functions-framework and sends a test message

set -euo pipefail

echo "Starting CourtSync locally..."

# Start the functions framework in background
cd function
functions-framework --target=whatsapp_webhook --port=8080 &
SERVER_PID=$!

sleep 2
echo "Server started (PID: $SERVER_PID)"

# Test: New player match request
echo ""
echo "--- Test 1: Match Request ---"
curl -s -X POST http://localhost:8080 \
  -d "From=whatsapp:+12125551234" \
  -d "Body=3.5 doubles tomorrow 6pm" \
  -d "ProfileName=Test Player" | head -c 500

echo ""
echo ""

# Test: YES response
echo "--- Test 2: YES Response ---"
curl -s -X POST http://localhost:8080 \
  -d "From=whatsapp:+12125551234" \
  -d "Body=Yes I'm in!" \
  -d "ProfileName=Test Player" | head -c 500

echo ""
echo ""

# Test: Health check
echo "--- Test 3: Health Check ---"
curl -s http://localhost:8080 | head -c 200

echo ""

# Cleanup
kill $SERVER_PID 2>/dev/null || true
echo "Done."
