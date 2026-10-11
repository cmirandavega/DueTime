"""Gemini: turns raw NHTSA + Tiger Data numbers into plain-language guidance,
and reads VIN photos. Without GEMINI_API_KEY, falls back to raw data so the
rest of the team is never blocked.
"""
import json
import re

from .config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_FALLBACK_MODELS, GROQ_API_KEY, GROQ_MODEL

_client = None


def client():
    global _client
    if _client is None and GEMINI_API_KEY:
        from google import genai
        # 60s timeout per try instead of the SDK's long default retries
        _client = genai.Client(api_key=GEMINI_API_KEY, http_options={"timeout": 60_000})
    return _client


async def generate(contents, config):
    """Try the main model, then each fallback. Busy (503) or rate-limited (429) -> next model."""
    from google.genai import errors
    last = None
    for model in [GEMINI_MODEL, *GEMINI_FALLBACK_MODELS]:
        try:
            return await client().aio.models.generate_content(model=model, contents=contents, config=config)
        except (errors.ServerError, errors.ClientError) as e:
            print(f"Gemini {model} failed: {getattr(e, 'code', '')} {e}")
            last = e
    raise last

async def groq_json(prompt: str) -> dict | None:
    """Backup when Gemini is down. JSON only, no web search."""
    if not GROQ_API_KEY:
        return None
    import httpx
    async with httpx.AsyncClient(timeout=30) as http:
        r = await http.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={"model": GROQ_MODEL, "temperature": 0.3,
                  "response_format": {"type": "json_object"},
                  "messages": [{"role": "user", "content": prompt}]},
        )
        r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])

REPORT_PROMPT = """You are DueTime, a patient mechanic explaining a car to its owner.
Write for someone who has never worked on a car. Short sentences. No jargon without a one-line explanation.
Respond in {language_name}.

Vehicle: {year} {make} {model}, {mileage} miles. Mode: {mode_text}.

FACTS YOU MAY USE (do not invent recalls, complaint counts, mileages, or prices):
{facts}

Return ONLY JSON with exactly these keys:
{{
  "summary": "one or two sentences: the single most important thing about this car right now",
  "recalls": [{{"campaign": str, "component": str, "summary_plain": str, "risk": "high"|"medium"|"low", "remedy_plain": str}}],
  "known_problems": [{{"component": str, "explanation": str}}],
  "maintenance_due": [{{"service": str, "interval_miles": int, "status": "overdue"|"due"|"upcoming", "why": str, "verify": true}}],
  "declined_services": [{{"rank": int, "service": str, "risk_if_ignored": str, "cost_if_ignored_usd": [int, int], "cost_to_do_now_usd": [int, int]}}],
  "diy_cards": [{{"job": str, "difficulty": "easy"|"moderate"|"hard"|"pro_only", "time_hours": [number, number], "tools": [str], "parts_cost_usd": [int, int], "shop_cost_usd": [int, int], "safety_note": str|null}}],
  "pre_purchase": {{"inspect": [str], "should_be_done": [str], "ask_seller": [str]}}
}}

Rules:
- recalls: one entry per recall in FACTS, same campaign numbers. Empty list if none.
- known_problems: one entry per component in FACTS, in the same order, using its exact component string.
- maintenance_due: use the manufacturer's typical schedule for this exact car from general knowledge. Mark every item verify=true.
- declined_services: services that should have been done by this mileage, ranked by cost of ignoring them. Ranges, not single numbers.
- diy_cards: the top 2-3 jobs from maintenance_due and known_problems. Brakes, airbags, fuel lines, and anything needing a lift get a safety_note saying to have a professional check the work.
- pre_purchase: fill only if mode is buying; otherwise use empty lists.
- Costs are US-dollar estimates, not quotes.
"""


def _facts(recalls, complaints_api, curves, price) -> str:
    return json.dumps({
        "recalls": recalls,
        "complaints_by_component_api": complaints_api,
        "failure_mileage_from_tiger_data": curves,
        "price_check": price,
    }, default=str)


def _fallback(recalls, complaints_api, curves) -> dict:
    problems = curves if curves else complaints_api.get("by_component", [])
    return {
        "_fallback": True,
        "summary": "Plain-language guidance is unavailable right now. Here is the raw safety data; try again in a minute.",
        "recalls": [{"campaign": r["campaign"], "component": r["component"],
                     "summary_plain": r["summary"], "risk": "high" if r.get("park_it") else "medium",
                     "remedy_plain": r["remedy"]} for r in recalls],
        "known_problems": [{"component": p["component"], "explanation": ""} for p in problems],
        "maintenance_due": [],
        "declined_services": [],
        "diy_cards": [],
        "pre_purchase": {"inspect": [], "should_be_done": [], "ask_seller": []},
    }


async def write_report(vehicle: dict, mode: str, lang: str,
                       recalls, complaints_api, curves, price) -> dict:
    c = client()
    if c is None:
        return _fallback(recalls, complaints_api, curves)
    prompt = REPORT_PROMPT.format(
        language_name="Spanish" if lang == "es" else "English",
        year=vehicle["year"], make=vehicle["make"], model=vehicle["model"],
        mileage=vehicle.get("mileage") or "unknown",
        mode_text="the user is thinking of BUYING this car" if mode == "buy" else "the user OWNS this car",
        facts=_facts(recalls, complaints_api, curves, price),
    )
    try:
        response = await generate(
            prompt,
            {"response_mime_type": "application/json", "temperature": 0.1},
        )
        payload = json.loads(response.text)
        return payload
    except Exception as e:
        print(f"Gemini failed: {type(e).__name__}: {e}")
        try:
            backup = await groq_json(prompt)
            if backup:
                print("Used Groq backup")
                return backup
        except Exception as g:
            print(f"Groq failed: {type(g).__name__}: {g}")
        return _fallback(recalls, complaints_api, curves)

SAFETY_WORDS = (
    "brake", "steering", "airbag", "air bag", "fuel smell", "gas smell", "smell gas", "smell fuel",
    "overheat", "smoke", "fire", "wheel wobble", "tire bulge",
    "freno", "dirección", "direccion", "bolsa de aire", "olor a gasolina", "sobrecalent", "humo", "fuego",
)

DIAGNOSE_SEARCH_PROMPT = """A car owner describes a symptom. Search the web for owner forums, repair videos,
and how-to articles about this exact car and symptom.

Vehicle: {year} {make} {model}, {mileage} miles.
Symptom (in the owner's words): {symptom}
Most-reported problem areas for this car from NHTSA owner complaints: {components}

Answer in {language_name}, plain words, for someone who has never worked on a car:
LIKELY CAUSES: up to 3, most likely first. For each: the cause, how to confirm it at home, and DIY or shop.
STOP DRIVING: yes or no, and why in one sentence.
Keep it short. Summarize; do not copy procedures from sources."""

DIAGNOSE_STRUCTURE_PROMPT = """Turn this answer into JSON. Use only what it says; add nothing.
Return ONLY JSON:
{{"stop_driving": bool, "stop_reason": str|null,
  "causes": [{{"cause": str, "how_to_confirm": str, "who": "diy"|"shop"|"either", "nhtsa_component": str|null}}]}}
Set nhtsa_component to the matching item from this list when a cause clearly belongs to it, else null:
{components}

ANSWER:
{answer}"""


async def diagnose(vehicle: dict, symptom: str, lang: str, components: list[str]) -> dict:
    """Search-grounded symptom lookup. Returns causes plus the web sources Gemini used.
    The symptom text is never stored or logged."""
    lowered = symptom.lower()
    safety_hit = any(w in lowered for w in SAFETY_WORDS)
    c = client()
    if c is None:
        return {"stop_driving": safety_hit, "stop_reason": None, "causes": [], "sources": [],
                "search_suggestions_html": None, "note": "Connect GEMINI_API_KEY to search for causes."}

    from google.genai import types
    comps = ", ".join(components) or "none on file"
    grounded = await generate(
        DIAGNOSE_SEARCH_PROMPT.format(
            year=vehicle["year"], make=vehicle["make"], model=vehicle["model"],
            mileage=vehicle.get("mileage") or "unknown", symptom=symptom, components=comps,
            language_name="Spanish" if lang == "es" else "English"),
        types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())], temperature=0.2),
    )
    answer = grounded.text or ""

    sources, suggestions = [], None
    meta = grounded.candidates[0].grounding_metadata if grounded.candidates else None
    if meta:
        seen = set()
        for chunk in meta.grounding_chunks or []:
            web = getattr(chunk, "web", None)
            if web and web.uri and web.uri not in seen:
                seen.add(web.uri)
                sources.append({"title": web.title or web.uri, "url": web.uri})
        if meta.search_entry_point:
            suggestions = meta.search_entry_point.rendered_content  # Google requires showing this

    structured = await generate(
        DIAGNOSE_STRUCTURE_PROMPT.format(components=comps, answer=answer),
        {"response_mime_type": "application/json", "temperature": 0},
    )
    try:
        out = json.loads(structured.text)
    except (json.JSONDecodeError, TypeError):
        out = {"stop_driving": False, "stop_reason": None, "causes": []}

    out["stop_driving"] = bool(out.get("stop_driving")) or safety_hit
    out["sources"] = sources[:6]
    out["search_suggestions_html"] = suggestions
    return out


VIN_RE = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")


def _to_jpeg(image: bytes) -> bytes:
    """Normalize any photo to a small JPEG so Gemini always sees an image."""
    import io
    from PIL import Image, ImageOps
    img = Image.open(io.BytesIO(image))
    img = ImageOps.exif_transpose(img).convert("RGB")  # fix phone rotation
    img.thumbnail((1600, 1600))                          # plenty for reading a VIN
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85)
    return out.getvalue()


async def read_vin_photo(image: bytes, mime_type: str) -> str | None:
    """Reads a VIN from a photo. The image is never stored."""
    c = client()
    if c is None:
        return None
    from google.genai import types
    jpeg = _to_jpeg(image)
    resp = await generate(
        [
            types.Part.from_bytes(data=jpeg, mime_type="image/jpeg"),
            "Read the 17-character vehicle VIN in this photo. Reply with only the VIN, or NONE.",
        ],
        None,
    )
    m = VIN_RE.search((resp.text or "").upper().replace(" ", ""))
    return m.group(0) if m else None
