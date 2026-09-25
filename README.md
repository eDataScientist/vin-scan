# VIN Scanner

Point your phone at a VIN stamped on a car, or at a **mulkiya** (vehicle registration card), and get the 17-character VIN back.

Mobile-first. One camera button. One endpoint.

## How it works

```
phone camera → photo POST → FastAPI → PydanticAI + Gemini 3.5 Flash Lite (via OpenRouter) → VIN
```

Plain HTML/CSS/TypeScript on the front, one FastAPI route on the back. No database, no build tooling beyond `tsc`.

## Requirements

- Python 3.11+
- Node.js (only to recompile `static/app.ts`; the compiled `static/app.js` is committed)
- An [OpenRouter](https://openrouter.ai) API key
- [`cloudflared`](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) — optional, only for a temporary public link

## Setup

```bash
git clone https://github.com/eDataScientist/vin-scan.git
cd vin-scan

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env      # then paste your OpenRouter key into .env
```

`.env` is gitignored. Never commit it.

## Run

```bash
./run.sh
```

Open http://127.0.0.1:8000 on the machine, or http://<your-lan-ip>:8000 from a phone on the same network.

The key is read from `$OPENROUTER_API_KEY` if set, otherwise from `.env`. `run.sh` strips any trailing carriage return — a CRLF `.env` otherwise fails with a misleading `Connection error.`

## Get a temporary public link

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Cloudflare prints a `https://<random>.trycloudflare.com` URL. No Cloudflare account or config needed. It dies when `cloudflared` stops — this is a quick tunnel, not a deployment.

> **The endpoint is unauthenticated and spends OpenRouter credits.** Don't leave a public tunnel running unattended.

## Test

```bash
.venv/bin/python check.py                    # VIN validation rules (no network)
curl -X POST http://127.0.0.1:8000/api/vin \
     -F "file=@test/mulkiya.jpg;type=image/jpeg"
```

Expected:

```json
{"vin": "WBAEV53444KM12345", "found_on": "mulkiya", "valid": true}
```

`test/` holds three fixture photos: a stamped VIN plate, a mulkiya card, and a blank image that must return `vin: null`.

## API

### `POST /api/vin`

Multipart form field `file`, max 12 MB, `image/*` only.

| field | type | meaning |
|---|---|---|
| `vin` | `string \| null` | Uppercased 17-char VIN, or `null` if none found |
| `found_on` | `string` | `car`, `mulkiya`, or `unknown` |
| `valid` | `bool` | Whether `vin` passed the VIN format check |

Errors: `400` empty upload, `413` too large, `415` not an image.

## Rebuild the frontend

`static/app.js` is compiled from `static/app.ts` and committed, so the app runs with no build step. After editing the TypeScript:

```bash
npx -y -p typescript tsc static/app.ts \
  --target es2020 --module es2020 --moduleResolution bundler \
  --strict --outDir static
```

## Layout

```
server.py        FastAPI + the PydanticAI agent
run.sh           starts uvicorn, loads the API key
check.py         assertions on VIN validation
static/          index.html, style.css, app.ts → app.js
test/            fixture photos
```

## Swapping the model

`MODEL` at the top of `server.py`. It must accept image input on OpenRouter.

Two gotchas already handled in the code, so you don't rediscover them:

- The output uses `PromptedOutput`, not the default tool-based structured output. Tool mode sets `tool_choice=required`, which thinking models on Alibaba's provider reject.
- `qwen/qwen3.8-flash` worked but was noticeably slower; `google/gemini-3.5-flash-lite` runs in ~2s.
