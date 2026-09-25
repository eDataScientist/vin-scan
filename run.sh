#!/usr/bin/env bash
# ponytail: the key comes from the environment or a local .env — never committed
set -e
cd "$(dirname "$0")"

if [ -z "${OPENROUTER_API_KEY:-}" ] && [ -f .env ]; then
  # .env files are often CRLF; a trailing \r makes httpx reject the auth header as "illegal"
  OPENROUTER_API_KEY=$(grep '^OPENROUTER_API_KEY=' .env | head -1 | cut -d= -f2- | tr -d '\r\n')
fi

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  echo "Set OPENROUTER_API_KEY, or put it in a .env file next to run.sh" >&2
  exit 1
fi
export OPENROUTER_API_KEY

exec .venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000
