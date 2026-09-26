#!/bin/bash

# FinSight AI - Universal Startup Script (Computer + Mobile)

echo "=============================================="
echo "    🚀 Starting FinSight AI                "
echo "=============================================="

# 1. Kill any existing processes on these ports to avoid errors
echo "Cleaning up existing processes on ports 8000 and 5000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5000 | xargs kill -9 2>/dev/null

# 2. Install/Verify Dependencies
echo "Step 1: Installing Backend Dependencies..."
pip3 install -r Backend/requirements.txt --quiet

# 3. Get Local IP Address (for Mobile Access)
# We try multiple interfaces (en0 is usually WiFi on Mac)
IP_ADDR=$(ipconfig getifaddr en0)
if [ -z "$IP_ADDR" ]; then
    IP_ADDR=$(ipconfig getifaddr en1)
fi
if [ -z "$IP_ADDR" ]; then
    IP_ADDR="localhost"
fi

# 4. Start Backend
echo "Step 2: Starting Backend Server on 0.0.0.0:8000..."
cd Backend
# Start uvicorn on all interfaces so your phone can "see" it
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload > /dev/null 2>&1 &
BACKEND_PID=$!
cd ..

# 5. Start Frontend Server
echo "Step 3: Starting Frontend Server on port 5000..."
# Using python's built-in http.server to serve the frontend files
python3 -m http.server 5000 > /dev/null 2>&1 &
FRONTEND_PID=$!

echo ""
echo "=========================================================="
echo "    ✨ FinSight AI IS READY! ✨                          "
echo "=========================================================="
echo "    💻 ON THIS MAC:   http://localhost:5000/index.html    "
echo "    📱 ON YOUR PHONE: http://$IP_ADDR:5000/index.html     "
echo "=========================================================="
echo "    (Important: Your phone & Mac MUST be on the same WiFi)"
echo "=========================================================="
echo "    Press Ctrl+C to stop both servers safely.             "
echo "=========================================================="
echo ""

# Automatically open the project on your Mac
open "http://localhost:5000/index.html"

# Handle script termination
trap "echo -e '\nStopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
