#!/bin/bash
set -e

export DISPLAY=:${DISPLAY_NUM}
./start_all.sh
./novnc_startup.sh

python http_server.py > /tmp/server_logs.txt 2>&1 &

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

# # Start the log server
# python src/log_server.py &

# # Start the main script
# python src/main.py

echo "✨ Browser Bot is ready!"
echo "➡️  Open http://localhost:8080 in your browser to begin"

# Keep the container running
tail -f /dev/null
