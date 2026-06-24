#!/bin/sh
until curl -s http://ollama:11434/api/tags > /dev/null; do
  sleep 2
done
curl -X POST http://ollama:11434/api/pull -d '{"name": "llama3.2:3b"}'
uvicorn app.main:app --host 0.0.0.0 --port 8000