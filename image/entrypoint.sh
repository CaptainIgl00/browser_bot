#!/bin/bash
set -e

export DISPLAY=:${DISPLAY_NUM}
# Add the home directory to PYTHONPATH so Python can find the src module
export PYTHONPATH=$HOME:$PYTHONPATH

./start_all.sh
./novnc_startup.sh

# Start Chrome in debug mode
google-chrome-stable \
    --remote-debugging-port=9222 \
    --remote-debugging-address=0.0.0.0 \
    --no-first-run \
    --no-default-browser-check \
    --start-maximized \
    --disable-gpu \
    --disable-dev-shm-usage \
    --no-sandbox \
    --user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
    --display=:${DISPLAY_NUM} &

sleep 2  # Wait for Chrome to start

# Create logs directory if it doesn't exist
mkdir -p $HOME/logs

# Start the API using the Python from pyenv with logging
$HOME/.pyenv/versions/$PYENV_VERSION/bin/python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --log-level debug --reload > $HOME/logs/uvicorn.log 2>&1 &

echo "✨ Browser Bot is ready!"
echo "➡️  Open http://localhost:8080 in your browser to begin"
echo "📝 Logs available in:"
echo "   - API logs: $HOME/logs/uvicorn.log"
echo "   - Scraper logs: $HOME/scraper.log"

# Keep the container running
tail -f $HOME/logs/uvicorn.log
