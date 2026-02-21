#!/bin/bash
cd /home/spiritai/science/targeting/backend
exec uvicorn app:app --host 127.0.0.1 --port 8502
