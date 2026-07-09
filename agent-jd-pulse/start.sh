#!/bin/bash
# Start CROO provider in background
python cap/integration.py &

# Start FastAPI server
uvicorn main:app --host 0.0.0.0 --port $PORT