"""VIN scanner backend: one endpoint, one agent."""
import asyncio
import os
import re

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pydantic_ai import Agent, PromptedOutput
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import BinaryContent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

MODEL = "google/gemini-3.5-flash-lite"
MAX_BYTES = 12_000_000
# VIN: 17 chars, A-Z/0-9 minus I, O, Q. Trust-boundary sanity check on model output.
VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


class VinResult(BaseModel):
    vin: str | None
    found_on: str  # "car" | "mulkiya" | "unknown"


agent = Agent(
    OpenAIChatModel(
        # .strip(): a trailing \r from a CRLF .env makes httpx reject the header as illegal
        MODEL, provider=OpenRouterProvider(api_key=os.environ["OPENROUTER_API_KEY"].strip())
    ),
    # PromptedOutput: JSON-in-prompt. The tool-based default sets
    # tool_choice=required, which Alibaba rejects when the model is thinking,
    # and OpenRouter's profile for this model does not advertise native
    # structured output. A 3-field schema parses fine from a prompt.
    output_type=PromptedOutput(VinResult),
    instructions=(
        "Extract the VIN (Vehicle Identification Number) from the photo. "
        "It may be stamped on a vehicle (dashboard, door jamb, firewall, chassis plate) "
        "or printed on a vehicle registration card (mulkiya). "
        "A VIN is exactly 17 characters, uppercase letters A-Z and digits 0-9, "
        "and never contains I, O or Q. Return it uppercase with no spaces or hyphens. "
        "found_on is 'car' if it is on the vehicle itself, 'mulkiya' if it is on a "
        "registration document, else 'unknown'. If no readable VIN is present, "
        "set vin to null."
    ),
)

app = FastAPI(title="VIN Scanner")


def normalize_vin(raw: str | None) -> str | None:
    """Uppercase, drop spaces/hyphens, then require a legal 17-char VIN."""
    vin = re.sub(r"[\s\-]", "", (raw or "")).upper()
    return vin if VIN_RE.match(vin) else None


async def run_agent(msgs) -> VinResult:
    # ponytail: one retry only — OpenRouter's shared pool 429s transiently on this model
    for attempt in range(2):
        try:
            return (await agent.run(msgs)).output
        except ModelHTTPError as e:
            if e.status_code != 429 or attempt:
                raise
            await asyncio.sleep(3)


@app.post("/api/vin")
async def extract_vin(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty upload")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "image too large")
    media_type = file.content_type or "image/jpeg"
    if not media_type.startswith("image/"):
        raise HTTPException(415, "not an image")

    out = await run_agent(
        ["Extract the VIN from this image.", BinaryContent(data=data, media_type=media_type)]
    )
    vin = normalize_vin(out.vin)
    return {"vin": vin, "found_on": out.found_on, "valid": vin is not None}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
