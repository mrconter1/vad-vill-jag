import json
import os
import re
import zipfile
import io
import urllib.request
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import threading
import anthropic

# ── env ───────────────────────────────────────────────────────────────────────
def _load_env():
    path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

_load_env()

# ── constants ─────────────────────────────────────────────────────────────────
PARTIES    = ["S", "SD", "M", "V", "C", "KD", "MP", "L"]
MODEL      = "claude-sonnet-4-6"
_STATS_MODE = len(sys.argv) > 1 and sys.argv[1] == "--stats"
N_DOCS     = int(sys.argv[1]) if len(sys.argv) > 1 and not _STATS_MODE else 10
WORKERS    = int(sys.argv[2]) if len(sys.argv) > 2 else 5

# Optional: --since YYYY-MM-DD  e.g. python extract_questions.py 9999 10 --since 2021-09-01
_SINCE_DATE = None
for _i, _arg in enumerate(sys.argv):
    if _arg == "--since" and _i + 1 < len(sys.argv):
        _SINCE_DATE = sys.argv[_i + 1]
        break
OUTPUT     = "questions.json"
BET_CACHE  = "bet-cache.json"
ERRORS_LOG = "extraction-errors.json"
BASE_URL   = "https://data.riksdagen.se/dataset"

# If the assembled user message (instructions + document) exceeds this character count,
# we skip the API call, log extraction-errors.json, and continue.
MAX_USER_MESSAGE_CHARS = 320_000

PRICE_IN   = 3.0  / 1_000_000
PRICE_OUT  = 15.0 / 1_000_000

COMMITTEE_CATEGORIES = {
    "AU":  {"sv": "Arbetsmarknad",             "en": "Labor Market"},
    "CU":  {"sv": "Civilrätt",                 "en": "Civil Law"},
    "FiU": {"sv": "Ekonomi och finans",        "en": "Economy & Finance"},
    "FöU": {"sv": "Försvar",                   "en": "Defense"},
    "JuU": {"sv": "Rättsväsende",              "en": "Justice & Criminal Law"},
    "KU":  {"sv": "Konstitution och demokrati", "en": "Constitution & Democracy"},
    "KrU": {"sv": "Kultur",                    "en": "Culture"},
    "MJU": {"sv": "Miljö och jordbruk",        "en": "Environment & Agriculture"},
    "NU":  {"sv": "Näringsliv",                "en": "Business & Industry"},
    "SkU": {"sv": "Skatter",                   "en": "Taxation"},
    "SfU": {"sv": "Socialförsäkring och migration", "en": "Social Insurance & Migration"},
    "SoU": {"sv": "Hälsa och sjukvård",        "en": "Health & Social Affairs"},
    "TU":  {"sv": "Transport och infrastruktur", "en": "Transport & Infrastructure"},
    "UbU": {"sv": "Utbildning",                "en": "Education"},
    "UU":  {"sv": "Utrikespolitik",            "en": "Foreign Affairs"},
}

def _extract_committee(beteckning):
    m = re.match(r"^([A-Za-zÖöÅåÄä]+)", beteckning)
    return m.group(1) if m else ""

def _get_category(beteckning):
    code = _extract_committee(beteckning)
    cat = COMMITTEE_CATEGORIES.get(code, {"sv": code, "en": code})
    return code, cat["sv"], cat["en"]

def _detect_punkt_type(forslag_text):
    """Detect if a punkt is about a government proposition or opposition motions."""
    lower = forslag_text.lower()
    has_proposition = "propositionen" in lower or "proposition" in lower
    has_motion = "motion" in lower
    if has_proposition and not has_motion:
        return "proposition"
    if has_motion and not has_proposition:
        return "motion"
    if has_proposition and has_motion:
        return "proposition_and_motion"
    return "other"

USD_TO_SEK = 10.5

# ── Expected JSON from Claude (Sonnet) ───────────────────────────────────────
# The model must reply with ONLY this JSON shape (no markdown fences). We parse it
# with json.loads after stripping optional ``` fences from the assistant text.
#
# Top-level object:
# {
#   "questions": [
#     {
#       "question_sv": "<Swedish: plain everyday wording; one or two sentences; last = yes/no hook>",
#       "question_en": "<English: plain everyday wording; one or two sentences; last = yes/no hook>",
#       "punkt": "<punkt number as string, e.g. \"3\"; REQUIRED — must match one of the PUNKTs above>"
#     }
#   ]
# }
#
# Rules: omit unsuitable items entirely (do not use null entries). Only include
# questions that are concrete enough for a general public quiz.
# Every question MUST include a "punkt" field matching the document punkt it is about.
# question_sv / question_en may each be one or two sentences: weave in brief
# grounding from the document when needed; the last sentence must read as the
# yes/no quiz hook. If a single sentence suffices, use only one. Within one API
# response, openings must be varied (no copy-paste template across questions).
# Wording must be plain enough that an ordinary adult without politics or law
# training understands it on first read (everyday words; explain real-world
# effects, not procedure).
# The [Omröstning: ...] line under each punkt shows how the parties actually voted —
# use this to understand the real political fault line and write a question that
# reflects it accurately.
MODEL_RESPONSE_EXAMPLE = {
    "questions": [
        {
            "question_sv": "När man överklagar vissa beslut skulle man kunna få längre tid på sig innan sista datum. Ska den tiden förlängas?",
            "question_en": "People appealing certain decisions could be given more time before the final deadline. Should that time limit be extended?",
            "punkt": "2",
        }
    ]
}

# Sessions ordered newest → oldest
VOTERING_SESSIONS = [
    ("2025/26", "votering-202526"),
    ("2024/25", "votering-202425"),
    ("2023/24", "votering-202324"),
    ("2022/23", "votering-202223"),
    ("2021/22", "votering-202122"),
    ("2020/21", "votering-202021"),
    ("2019/20", "votering-201920"),
    ("2018/19", "votering-201819"),
    ("2017/18", "votering-201718"),
    ("2016/17", "votering-201617"),
]

# Bet periods: (start_year, end_year, zip_stem)
BET_PERIODS = [
    (2022, 2025, "bet-2022-2025"),
    (2018, 2021, "bet-2018-2021"),
    (2014, 2017, "bet-2014-2017"),
    (2010, 2013, "bet-2010-2013"),
    (2006, 2009, "bet-2006-2009"),
]

def _rm_start_year(rm):
    try:
        return int(rm.split("/")[0])
    except Exception:
        return 0

def _bet_stem_for_rm(rm):
    year = _rm_start_year(rm)
    for start, end, stem in BET_PERIODS:
        if start <= year <= end:
            return stem
    return None

# ── download helper ───────────────────────────────────────────────────────────
def _download_zip(url, label, local_zip=None):
    if local_zip and os.path.exists(local_zip):
        print(f"  Reading local {local_zip}...", flush=True)
        with open(local_zip, "rb") as f:
            return f.read()
    print(f"  Downloading {label}...", flush=True)
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                total, data = 0, b""
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    data += chunk
                    total += len(chunk)
                    print(f"    {total // 1024} KB...", end="\r", flush=True)
            print()
            return data
        except Exception as e:
            print(f"\n    urllib attempt {attempt+1} failed: {e}", flush=True)
    out = local_zip or (label.replace(" ", "_") + ".zip")
    print(f"  Trying PowerShell...", flush=True)
    result = subprocess.run(
        ["powershell", "-Command", f'Invoke-WebRequest -Uri "{url}" -OutFile "{out}"'],
        capture_output=True, text=True
    )
    if result.returncode != 0 or not os.path.exists(out):
        raise RuntimeError(f"Download failed: {result.stderr}")
    with open(out, "rb") as f:
        return f.read()

# ── votering loading ──────────────────────────────────────────────────────────
def _load_session(rm, stem):
    """Load (or download+cache) a single votering session. Returns list of vote rows."""
    cache_file = f"{stem}.json"
    zip_file   = f"{stem}.json.zip"
    if os.path.exists(cache_file):
        with open(cache_file, encoding="utf-8") as f:
            return json.load(f)
    url  = f"{BASE_URL}/votering/{stem}.json.zip"
    data = _download_zip(url, stem, zip_file)
    votes = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = [n for n in zf.namelist() if n.endswith(".json")]
        print(f"    Extracting {len(names)} files...", flush=True)
        for i, name in enumerate(names):
            try:
                with zf.open(name) as f:
                    raw = json.load(f)
            except Exception:
                continue
            rows = raw.get("dokvotering", {}).get("votering", [])
            if isinstance(rows, dict):
                rows = [rows]
            votes.extend(rows)
            if i % 100 == 0:
                print(f"    {i}/{len(names)}...", end="\r", flush=True)
    print()
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(votes, f, ensure_ascii=False)
    print(f"    Saved {len(votes)} records to {cache_file}", flush=True)
    return votes

# ── dokumentstatus / punkt parsing ────────────────────────────────────────────
def _punkter_from_dokumentstatus_ds(ds):
    """Build punkt → {rubrik, forslag} from a dokumentstatus object (same shape as bulk zips)."""
    punkter = {}
    forslags = ds.get("dokutskottsforslag", {}).get("utskottsforslag", []) or []
    if isinstance(forslags, dict):
        forslags = [forslags]
    for uf in forslags:
        punkt = uf.get("punkt", "")
        rubrik = uf.get("rubrik", "")
        raw_f = uf.get("forslag", "") or ""
        forslag = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw_f)).strip()
        if punkt:
            punkter[punkt] = {"rubrik": rubrik, "forslag": forslag}
    return punkter


def _resolve_punkt_key(punkt, punkter_dict):
    """
    Map votering punkt string to a key present in punkter_dict.
    Handles whitespace and numeric variants (e.g. '7' vs '07').
    """
    if punkt in punkter_dict:
        return punkt
    s = str(punkt).strip()
    if s in punkter_dict:
        return s
    if s.isdigit():
        n = int(s)
        for candidate in (str(n), str(n).zfill(2), str(n).zfill(3)):
            if candidate in punkter_dict:
                return candidate
        for k in punkter_dict:
            ks = str(k).strip()
            if ks.isdigit() and int(ks) == n:
                return k
    return None


def _fetch_dokumentstatus_punkter(dok_id):
    """Fetch live dokumentstatus JSON; returns punkt dict or None on failure."""
    if not dok_id:
        return None
    url = f"https://data.riksdagen.se/dokumentstatus/{dok_id}.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = json.load(resp)
    except Exception:
        return None
    ds = raw.get("dokumentstatus", {})
    return _punkter_from_dokumentstatus_ds(ds) or None


# ── bet cache loading ─────────────────────────────────────────────────────────
def _load_bet_period(stem, bet_cache):
    """Download a bet period zip and merge its data into bet_cache in place."""
    zip_file = f"{stem}.json.zip"
    url      = f"{BASE_URL}/dokument/{stem}.json.zip"
    data     = _download_zip(url, stem, zip_file)
    added = skipped = 0
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = [n for n in zf.namelist() if n.endswith(".json")]
        print(f"    Extracting {len(names)} betänkanden...", flush=True)
        for i, name in enumerate(names):
            try:
                with zf.open(name) as f:
                    raw = json.load(f)
            except Exception:
                skipped += 1
                continue
            ds   = raw.get("dokumentstatus", {})
            doc  = ds.get("dokument", {})
            beteckning = doc.get("beteckning", "")
            rm_val     = doc.get("rm", "")
            titel      = doc.get("titel", "")
            dok_id     = doc.get("dok_id", "")
            if not beteckning:
                continue
            punkter = _punkter_from_dokumentstatus_ds(ds)
            key = f"{rm_val}|{beteckning}"
            if key not in bet_cache:
                bet_cache[key] = {"titel": titel, "dok_id": dok_id, "punkter": punkter}
                added += 1
            if i % 200 == 0:
                print(f"    {i}/{len(names)}...", end="\r", flush=True)
    print()
    if skipped:
        print(f"    (Skipped {skipped} malformed files)")
    print(f"    Added {added} betänkanden from {stem}", flush=True)

def load_bet_cache():
    if os.path.exists(BET_CACHE):
        with open(BET_CACHE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_bet_cache(bet_cache):
    with open(BET_CACHE, "w", encoding="utf-8") as f:
        json.dump(bet_cache, f, ensure_ascii=False)

# ── data manager ──────────────────────────────────────────────────────────────
def build_index(votes):
    """Return (bet_data, bet_dates, bet_rm) from a flat vote list."""
    bet_data  = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    bet_dates = {}
    bet_rm    = {}
    for v in votes:
        if v.get("avser") != "sakfrågan":
            continue
        bet = v.get("beteckning", "")
        if not bet:
            continue
        bet_data[bet][v["punkt"]][v["votering_id"]].append(v)
        d = v.get("datum") or ""
        if bet not in bet_dates or d > bet_dates[bet]:
            bet_dates[bet] = d
        bet_rm[bet] = v.get("rm", "")
    return bet_data, bet_dates, bet_rm

def count_unique_vote_docs(votes):
    seen = set()
    for v in votes:
        if v.get("avser") != "sakfrågan":
            continue
        bet, rm = v.get("beteckning", ""), v.get("rm", "")
        if bet and rm:
            seen.add((rm, bet))
    return len(seen)

def ensure_data(n_docs_needed):
    """
    Load votering sessions and bet periods until we have >= n_docs_needed distinct
    voted (rm, betänkande) pairs. Returns (all_votes, bet_data, bet_cache).
    """
    all_votes = []
    bet_cache = load_bet_cache()

    for rm, stem in VOTERING_SESSIONS:
        print(f"Loading session {rm} ({stem})...", flush=True)
        session_votes = _load_session(rm, stem)
        all_votes.extend(session_votes)

        n_docs = count_unique_vote_docs(all_votes)
        print(f"  {n_docs} distinct voted betänkanden so far\n")

        bet_data, _, bet_rm = build_index(all_votes)
        rms_needed = set(bet_rm.values())
        loaded_bet_stems = set()
        for rm_val in rms_needed:
            bet_stem = _bet_stem_for_rm(rm_val)
            if not bet_stem or bet_stem in loaded_bet_stems:
                continue
            has_coverage = any(k.startswith(f"{rm_val}|") for k in bet_cache)
            if not has_coverage:
                print(f"  Fetching bet data for {rm_val} ({bet_stem})...", flush=True)
                _load_bet_period(bet_stem, bet_cache)
                save_bet_cache(bet_cache)
                print(f"  bet-cache.json updated ({len(bet_cache)} entries)\n")
            loaded_bet_stems.add(bet_stem)

        if n_docs >= n_docs_needed:
            break
    else:
        print(f"Ran out of sessions — only {count_unique_vote_docs(all_votes)} betänkanden available.")
        bet_data, _, _ = build_index(all_votes)

    return all_votes, bet_data, bet_cache

# ── party stance from real votes ───────────────────────────────────────────────
def derive_stance(party_tally, committee_approves):
    ja  = party_tally.get("Ja", 0)
    nej = party_tally.get("Nej", 0)
    av  = party_tally.get("Avstår", 0)
    if ja + nej + av == 0 or (av >= ja and av >= nej):
        return "abstain"
    if committee_approves:
        return "for" if ja > nej else "against"
    return "against" if ja > nej else "for"

def tally_votes(bet_data, bet, punkt):
    """Return {party: {rost: count}} for a given beteckning + punkt."""
    tally = defaultdict(lambda: defaultdict(int))
    for mp_votes in bet_data.get(bet, {}).get(punkt, {}).values():
        for v in mp_votes:
            tally[v.get("parti", "-")][v.get("rost", "?")] += 1
    return tally

def stances_from_votes(tally, committee_approves):
    return {
        party: derive_stance(tally[party], committee_approves)
        for party in PARTIES if party in tally
    }

# ── Claude ────────────────────────────────────────────────────────────────────
_total_in = _total_out = 0
_errors_lock = threading.Lock()
_extraction_errors = []

def _record_error(rm, bet, code, detail=None):
    with _errors_lock:
        _extraction_errors.append({
            "rm": rm,
            "beteckning": bet,
            "error": code,
            "detail": detail,
            "at": datetime.now().isoformat(timespec="seconds"),
        })

_ALLOWED_STANCES = frozenset({"for", "against", "abstain"})

def _normalize_party_stances(raw):
    if not isinstance(raw, dict):
        return None
    out = {}
    for p in PARTIES:
        v = raw.get(p)
        if isinstance(v, str) and v.strip().lower() in _ALLOWED_STANCES:
            out[p] = v.strip().lower()
        else:
            out[p] = "abstain"
    return out

def _vote_summary_line(tally):
    """Return a compact vote line e.g. 'Ja → S, M, L | Nej → SD, V | Avstår → C'"""
    buckets = {"Ja": [], "Nej": [], "Avstår": []}
    for party in PARTIES:
        pt = tally.get(party, {})
        ja, nej, av = pt.get("Ja", 0), pt.get("Nej", 0), pt.get("Avstår", 0)
        if ja + nej + av == 0:
            continue
        if ja >= nej and ja >= av:
            buckets["Ja"].append(party)
        elif nej >= ja and nej >= av:
            buckets["Nej"].append(party)
        else:
            buckets["Avstår"].append(party)
    parts = [f"{k} → {', '.join(v)}" for k, v in buckets.items() if v]
    return f"[Omröstning: {' | '.join(parts)}]" if parts else ""

def _build_document_body(titel, punkter_data, bet_data_for_bet=None):
    lines = [f"Betänkande: {titel}", ""]
    for punkt, pd in sorted(
        punkter_data.items(),
        key=lambda x: int(x[0]) if str(x[0]).strip().isdigit() else 0,
    ):
        rubrik = pd.get("rubrik", "")
        forslag = pd.get("forslag", "")
        lines.append(f"PUNKT {punkt}: {rubrik}")
        if bet_data_for_bet is not None:
            vote_tally = tally_votes({"_": bet_data_for_bet}, "_", punkt)
            summary = _vote_summary_line(vote_tally)
            if summary:
                lines.append(summary)
        lines.append(forslag)
        lines.append("")
    return "\n".join(lines)

def extract_questions_for_document(titel, document_body):
    """
    One Sonnet call per betänkande. Returns a list of validated question dicts
    (question_sv, question_en, party_stances, optional punkt) or raises on API/JSON failure.
    """
    global _total_in, _total_out
    schema_hint = json.dumps(MODEL_RESPONSE_EXAMPLE, ensure_ascii=False, indent=2)
    prompt = (
        "You are given the full text of a Swedish parliamentary committee report (betänkande) "
        "with utskottsforslag (committee proposals) per punkt.\n\n"
        "Task:\n"
        "1) Produce zero or more valid quiz questions. For each, question_sv and question_en "
        "may be one or at most two sentences. When readers need a line of grounding from the "
        "document (what is proposed, scope, who is affected), put it in the same field as the "
        "first sentence; the final sentence must read as a clear yes/no hook. If one sentence "
        "is enough, use only one. Tone: serious and neutral, but in plain language an "
        "ordinary person uses every day — not administration-speak, legalese, or insider "
        "parliamentary phrasing. No slang. No em dashes. Someone with no special interest in "
        "politics should understand every word on first read; prefer concrete outcomes "
        "(what would change for people, companies, or society) over process framing such as "
        "'should the Riksdag decide …' or 'should Parliament approve …' unless you cannot "
        "express the substance otherwise. When the source text is technical, translate the "
        "idea into normal words. In Swedish, avoid stiff fillers like 'är föremål för', "
        "'föreslås att', 'i enlighet med de framlagda förslagen', 'har ifrågasatts från "
        "flera håll' when a shorter, direct wording works. Avoid words like motion, "
        "betänkande, utskott, yrkande in the question text.\n"
        "   Within this single response, vary how each question begins: do not repeat the same "
        "opening pattern across items. In particular avoid leaning on stock openers such as "
        "'Det finns förslag om …', 'There are proposals …', 'Riksdagen har avslagit förslag om …', "
        "or 'The Riksdag has rejected proposals …' for every question. Mix structures (e.g. "
        "lead with the policy change, or only the hook, or a different factual lead-in each time) "
        "so the set reads like distinct journalism lines, not one template copied many times.\n"
        "   Each punkt includes an [Omröstning: ...] line showing how the parties actually "
        "voted (Ja/Nej/Avstår). Use this to understand the real political divide when "
        "writing the question — the question should reflect what parties genuinely disagree on.\n"
        "   CONSENSUS TRAP CHECK: Before finalising each question, ask yourself — "
        "would almost any reasonable adult answer yes to this? If so, the question is "
        "useless as a quiz item regardless of how the parties voted. Reframe it around "
        "the actual fault line: the mechanism, cost, trade-off, or restriction that "
        "divides parties. For example, 'Should children exposed to violence get more "
        "protection?' is a consensus trap; 'Should municipalities be legally required "
        "to assign a named contact person to every child reported for suspected abuse?' "
        "is not. Dig into what the document actually proposes and frame the question "
        "around the specific measure, not the desirable outcome everyone already agrees on.\n"
        "   POLICY STANCE RULE: The question must ask whether a policy is right, not what "
        "the Riksdag did or should procedurally do. Never frame questions as 'Did the Riksdag "
        "vote for X?', 'Was it right that riksdagen decided Y?', or 'Should riksdagen pass Z?' — "
        "ask about the underlying policy: 'Should X be done?' If you cannot frame it as a "
        "genuine policy opinion question, do not include it.\n"
        "   NO PARTY NAMES IN QUESTIONS: Never mention specific party names (S, SD, M, V, C, "
        "KD, MP, L, Socialdemokraterna, Sverigedemokraterna, Moderaterna, etc.) in the question "
        "text. The question must stand on its own without telling the reader who voted how. "
        "If a question cannot be written without naming parties, do not include it.\n"
        "   Every question MUST include a 'punkt' field with the punkt number it corresponds to.\n"
        "2) Skip ratifications of specific past budgets, pure procedural one-offs, COVID-only "
        "temporary measures, or anything without concrete policy content.\n\n"
        "Output ONLY the raw JSON object — no analysis, no explanation, no reasoning text "
        "before or after. If nothing is suitable, output {\"questions\": []}.\n\n"
        "Required shape:\n"
        f"{schema_hint}\n\n"
        "--- DOCUMENT ---\n\n"
        f"{document_body}"
    )

    if len(prompt) > MAX_USER_MESSAGE_CHARS:
        raise ValueError("context_too_large", len(prompt))

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model=MODEL,
        max_tokens=16384,
        messages=[{"role": "user", "content": prompt}],
    )
    in_tok, out_tok = msg.usage.input_tokens, msg.usage.output_tokens
    _total_in += in_tok
    _total_out += out_tok
    cost_sek = (in_tok * PRICE_IN + out_tok * PRICE_OUT) * USD_TO_SEK
    running_cost = (_total_in * PRICE_IN + _total_out * PRICE_OUT) * USD_TO_SEK
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"    [{ts}] tokens: {in_tok} in / {out_tok} out  |  {cost_sek:.3f} kr  |  running: {running_cost:.2f} kr", flush=True)

    full_text = msg.content[0].text.strip()

    # 1. Try a ```json ... ``` block anywhere in the response
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", full_text, re.DOTALL)
    # 2. Fall back to first { ... last }
    brace_match = re.search(r"\{.*\}", full_text, re.DOTALL)

    raw = None
    if fence_match:
        raw = fence_match.group(1)
    elif brace_match:
        raw = brace_match.group(0)

    if not raw:
        # Sonnet returned only analysis with no JSON — treat as zero valid questions
        print(f"    (no JSON in response — Sonnet found nothing suitable)", flush=True)
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        preview = raw[:300].replace("\n", "\\n")
        raise ValueError(f"json_decode_error: {exc} | response preview: {preview}") from exc

    items = data.get("questions")
    if not isinstance(items, list):
        raise ValueError("missing_questions_array")

    _PARTY_NAMES = {
        "socialdemokraterna", "sverigedemokraterna", "moderaterna", "vänsterpartiet",
        "centerpartiet", "kristdemokraterna", "miljöpartiet", "liberalerna",
        " s ", " sd ", " m ", " v ", " c ", " kd ", " mp ", " l ",
    }

    def _has_party_name(text):
        lower = f" {text.lower()} "
        return any(p in lower for p in _PARTY_NAMES)

    _PROCEDURAL_TRIGGERS_SV = [
        "röstade riksdagen", "röstat riksdagen", "var det rätt att riksdagen",
        "var det rätt att göra det", "ska riksdagen besluta", "bör riksdagen besluta",
        "bör riksdagen anta", "ska riksdagen anta",
    ]
    _PROCEDURAL_TRIGGERS_EN = [
        "did parliament", "did the riksdag", "was it right that", "should parliament vote",
        "should the riksdag vote", "should the riksdag decide", "should parliament decide",
        "should parliament pass", "should the riksdag pass",
    ]

    def _is_procedural(qsv, qen):
        lower_sv = qsv.lower()
        lower_en = qen.lower()
        return (
            any(t in lower_sv for t in _PROCEDURAL_TRIGGERS_SV)
            or any(t in lower_en for t in _PROCEDURAL_TRIGGERS_EN)
        )

    validated = []
    for row in items:
        if not isinstance(row, dict):
            continue
        qsv = (row.get("question_sv") or "").strip()
        qen = (row.get("question_en") or "").strip()
        pk = str(row.get("punkt") or "").strip()
        if not qsv or not qen or not pk:
            continue
        if _has_party_name(qsv) or _has_party_name(qen):
            continue
        if _is_procedural(qsv, qen):
            continue
        validated.append({"question_sv": qsv, "question_en": qen, "punkt": pk})
    return validated

# ── stats mode ────────────────────────────────────────────────────────────────
if _STATS_MODE:
    print("Loading all sessions for stats (no Sonnet calls)...\n")
    all_votes, bet_data, bet_cache = ensure_data(999_999)

    docs_total = docs_in_cache = docs_with_forslag = 0
    punkter_total = punkter_with_forslag = punkter_with_votes = punkter_full_match = 0
    by_rm = defaultdict(lambda: {"docs": 0, "full_match": 0})

    seen_docs = set()
    for bet, punkter_votes in bet_data.items():
        first_vote = next(
            (v for vl in punkter_votes.values() for mv in vl.values() for v in mv),
            None,
        )
        if not first_vote:
            continue
        rm = first_vote.get("rm", "")
        latest_date = max(
            (v.get("datum") or "" for vl in punkter_votes.values() for mv in vl.values() for v in mv),
            default="",
        )
        if _SINCE_DATE and latest_date[:10] < _SINCE_DATE:
            continue
        if (rm, bet) in seen_docs:
            continue
        seen_docs.add((rm, bet))
        docs_total += 1
        cache_key = f"{rm}|{bet}"
        cache_entry = bet_cache.get(cache_key, {})
        cache_punkter = cache_entry.get("punkter", {})

        has_any_forslag = any(p.get("forslag") for p in cache_punkter.values())
        if cache_entry:
            docs_in_cache += 1
        if has_any_forslag:
            docs_with_forslag += 1

        doc_full = 0
        for punkt in punkter_votes:
            punkter_total += 1
            ck = _resolve_punkt_key(punkt, cache_punkter)
            has_forslag = bool(ck and cache_punkter.get(ck, {}).get("forslag"))
            has_votes = bool(punkter_votes[punkt])
            if has_forslag:
                punkter_with_forslag += 1
            if has_votes:
                punkter_with_votes += 1
            if has_forslag and has_votes:
                punkter_full_match += 1
                doc_full += 1

        by_rm[rm]["docs"] += 1
        by_rm[rm]["full_match"] += doc_full

    W = 50
    print(f"{'─'*W}")
    print(f"  PIPELINE STATS (no Sonnet)" + (f" — since {_SINCE_DATE}" if _SINCE_DATE else ""))
    print(f"{'─'*W}")
    print(f"  Voted betänkanden total       : {docs_total:>6}")
    print(f"  In bet-cache                  : {docs_in_cache:>6}")
    print(f"  With ≥1 forslag text          : {docs_with_forslag:>6}")
    print()
    print(f"  Voted punkter total           : {punkter_total:>6}")
    print(f"  With forslag text in cache    : {punkter_with_forslag:>6}")
    print(f"  With vote rows                : {punkter_with_votes:>6}")
    print(f"  FULL MATCH (votes + forslag)  : {punkter_full_match:>6}  ← max possible questions before Sonnet")
    print()
    print(f"  BY SESSION")
    print(f"  {'rm':<12} {'docs':>6}  {'full match punkter':>20}")
    print(f"  {'─'*42}")
    for rm in sorted(by_rm, reverse=True):
        print(f"  {rm:<12} {by_rm[rm]['docs']:>6}  {by_rm[rm]['full_match']:>20}")
    print(f"{'─'*W}")
    sys.exit(0)

# ── main ──────────────────────────────────────────────────────────────────────
all_votes, bet_data, bet_cache = ensure_data(N_DOCS)

doc_dates = {}
for v in all_votes:
    if v.get("avser") != "sakfrågan":
        continue
    bet_val, rm_val = v.get("beteckning", ""), v.get("rm", "")
    if not bet_val or not rm_val:
        continue
    k = (rm_val, bet_val)
    d = v.get("datum") or ""
    if d > doc_dates.get(k, ""):
        doc_dates[k] = d

all_doc_keys = sorted(doc_dates.keys(), key=lambda k: doc_dates[k], reverse=True)

if _SINCE_DATE:
    all_doc_keys = [k for k in all_doc_keys if doc_dates[k][:10] >= _SINCE_DATE]

selected_docs = all_doc_keys[:N_DOCS]
selected_doc_dates = {k: doc_dates[k] for k in selected_docs}

print(f"Distinct voted betänkanden available: {len(all_doc_keys)}" +
      (f" (since {_SINCE_DATE})" if _SINCE_DATE else ""))
print(f"Processing the {N_DOCS} most recent (by latest vote date)...\n")

if os.path.exists(OUTPUT):
    with open(OUTPUT, encoding="utf-8") as f:
        all_results = json.load(f)
    results = [r for r in all_results if r.get("question_sv") and r.get("question_en")]
    existing_ids = {r["id"] for r in results}
    dropped = len(all_results) - len(results)
    print(f"Loaded {len(results)} existing questions from {OUTPUT}" + (f" ({dropped} empty entries queued for retry)" if dropped else ""))
else:
    results = []
    existing_ids = set()

_points_done = len(existing_ids)
_save_lock   = threading.Lock()
_bet_cache_lock = threading.Lock()

def process_document(rm, bet):
    datum = (selected_doc_dates.get((rm, bet), "") or "")[:10]
    cache_key = f"{rm}|{bet}"
    bet_info = bet_cache.get(cache_key, {})
    titel = bet_info.get("titel", bet)
    dok_id = bet_info.get("dok_id", "")
    all_bet_punkter = dict(bet_info.get("punkter", {}))

    if not all_bet_punkter and dok_id:
        fresh = _fetch_dokumentstatus_punkter(dok_id)
        if fresh:
            all_bet_punkter.update(fresh)
            with _bet_cache_lock:
                entry = bet_cache.setdefault(cache_key, {"titel": titel, "dok_id": dok_id, "punkter": {}})
                entry.setdefault("punkter", {}).update(fresh)
                if dok_id and not entry.get("dok_id"):
                    entry["dok_id"] = dok_id

    if not any((all_bet_punkter.get(k) or {}).get("forslag") for k in all_bet_punkter):
        print(f"  {bet} [{rm}]: no forslag text, skipping", flush=True)
        _record_error(rm, bet, "no_forslag_text")
        return []

    body = _build_document_body(titel, all_bet_punkter, bet_data_for_bet=bet_data.get(bet))
    try:
        print(f"  {bet} [{rm}] ({titel[:45]}): calling Sonnet...", flush=True)
        rows = extract_questions_for_document(titel, body)
    except ValueError as e:
        if e.args and e.args[0] == "context_too_large":
            nch = e.args[1] if len(e.args) > 1 else None
            _record_error(rm, bet, "context_too_large", nch)
            print(f"    SKIP context too large ({nch} chars in full prompt)", flush=True)
        else:
            _record_error(rm, bet, "value_error", str(e))
            print(f"    Error: {e}", flush=True)
        return []
    except Exception as e:
        _record_error(rm, bet, "claude_error", str(e))
        print(f"    Claude error on {bet}: {e}", flush=True)
        return []

    committee_code, cat_sv, cat_en = _get_category(bet)
    dok_id_out = bet_info.get("dok_id", dok_id)
    bet_vote_data = bet_data.get(bet, {})
    new_items = []
    skipped_no_votes = 0
    for qi, row in enumerate(rows):
        item_id = f"{rm}_{bet}_q{qi}"
        if item_id in existing_ids:
            continue
        punkt = row.get("punkt", "")
        ck = _resolve_punkt_key(punkt, all_bet_punkter) if punkt else None
        pd = all_bet_punkter.get(ck, {}) if ck else {}

        # Resolve punkt key against vote data (votering may use different string form)
        vote_punkt_key = _resolve_punkt_key(punkt, bet_vote_data) if punkt else None
        if not vote_punkt_key:
            skipped_no_votes += 1
            continue

        vote_tally = tally_votes({"_": bet_vote_data}, "_", vote_punkt_key)
        forslag_text = pd.get("forslag", "").lower()
        committee_approves = "bifaller" in forslag_text
        party_stances = stances_from_votes(vote_tally, committee_approves)
        if not party_stances:
            skipped_no_votes += 1
            continue

        punkt_type = _detect_punkt_type(pd.get("forslag", "")) if pd.get("forslag") else "other"
        new_items.append({
            "id":            item_id,
            "datum":         datum,
            "rm":            rm,
            "beteckning":    bet,
            "titel":         titel,
            "punkt":         punkt or "",
            "rubrik":        pd.get("rubrik", f"Punkt {punkt}" if punkt else ""),
            "type":          punkt_type,
            "category_code": committee_code,
            "category_sv":   cat_sv,
            "category_en":   cat_en,
            "question_sv":   row["question_sv"],
            "question_en":   row["question_en"],
            "url":           f"https://data.riksdagen.se/dokument/{dok_id_out}" if dok_id_out else "",
            "party_stances": party_stances,
        })
    if skipped_no_votes:
        print(f"    {bet}: {skipped_no_votes} question(s) skipped — no matching vote data", flush=True)
    return new_items

print(f"Running with {WORKERS} parallel workers\n")
with ThreadPoolExecutor(max_workers=WORKERS) as executor:
    futures = {executor.submit(process_document, rm, bet): (rm, bet) for rm, bet in selected_docs}
    for future in as_completed(futures):
        new_items = future.result()
        with _save_lock:
            for item in new_items:
                if item["id"] not in existing_ids:
                    results.append(item)
                    existing_ids.add(item["id"])
                    _points_done += 1
            print(f"  [{_points_done} questions saved] +{len(new_items)} from {futures[future][1]}", flush=True)
            with open(OUTPUT, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

save_bet_cache(bet_cache)

if _extraction_errors:
    prev = []
    if os.path.exists(ERRORS_LOG):
        try:
            with open(ERRORS_LOG, encoding="utf-8") as ef:
                prev = json.load(ef)
        except Exception:
            prev = []
    merged = prev + _extraction_errors
    with open(ERRORS_LOG, "w", encoding="utf-8") as ef:
        json.dump(merged, ef, ensure_ascii=False, indent=2)
    print(f"\nLogged {len(_extraction_errors)} issue(s) to {ERRORS_LOG} (total entries: {len(merged)})", flush=True)

total_cost_sek = (_total_in * PRICE_IN + _total_out * PRICE_OUT) * USD_TO_SEK
print(f"\nDone. {len(results)} questions written to {OUTPUT}")
print(f"Total tokens: {_total_in} in / {_total_out} out  |  total cost: {total_cost_sek:.2f} kr")

empty = [r for r in results if not r.get("question_sv") or not r.get("question_en")]
if empty:
    print(f"\nWARNING: {len(empty)} questions have empty question text:")
    for r in empty:
        print(f"  {r['id']}")
    print(f"\nRe-run extract_questions.py to fill them.")
else:
    print(f"All {len(results)} questions have question text.")

import random as _random
_sample = _random.sample(results, min(25, len(results)))
print(f"\n{'─'*60}")
print(f"  SAMPLE — 25 random Swedish questions")
print(f"{'─'*60}")
for i, r in enumerate(_sample, 1):
    print(f"  {i:>2}. [{r.get('beteckning','')}] {r.get('question_sv','')}")
print(f"{'─'*60}")
