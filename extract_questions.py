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
MODEL      = "claude-opus-4-6"
N_PUNKTER  = int(sys.argv[1]) if len(sys.argv) > 1 else 10
WORKERS    = int(sys.argv[2]) if len(sys.argv) > 2 else 5
OUTPUT     = "questions.json"
BET_CACHE  = "bet-cache.json"
BASE_URL   = "https://data.riksdagen.se/dataset"

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

PRICE_IN   = 5.0  / 1_000_000
PRICE_OUT  = 25.0 / 1_000_000
USD_TO_SEK = 10.5

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
            punkter = {}
            forslags = ds.get("dokutskottsforslag", {}).get("utskottsforslag", []) or []
            if isinstance(forslags, dict):
                forslags = [forslags]
            for uf in forslags:
                punkt  = uf.get("punkt", "")
                rubrik = uf.get("rubrik", "")
                raw_f  = uf.get("forslag", "") or ""
                forslag = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw_f)).strip()
                if punkt:
                    punkter[punkt] = {"rubrik": rubrik, "forslag": forslag}
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

def count_punkter(bet_data):
    return sum(len(punkter) for punkter in bet_data.values())

def ensure_data(n_needed):
    """
    Load votering sessions and bet periods until we have >= n_needed punkter.
    Returns (all_votes, bet_data, bet_dates, bet_rm, bet_cache).
    """
    all_votes = []
    loaded_stems = set()
    bet_cache = load_bet_cache()

    for rm, stem in VOTERING_SESSIONS:
        print(f"Loading session {rm} ({stem})...", flush=True)
        session_votes = _load_session(rm, stem)
        all_votes.extend(session_votes)
        loaded_stems.add(stem)

        bet_data, bet_dates, bet_rm = build_index(all_votes)
        n = count_punkter(bet_data)
        print(f"  {n} voted punkter so far\n")

        # Ensure bet data covers all rms in this batch
        rms_needed = set(bet_rm.values())
        loaded_bet_stems = set()
        for rm_val in rms_needed:
            bet_stem = _bet_stem_for_rm(rm_val)
            if not bet_stem:
                continue
            if bet_stem in loaded_bet_stems:
                continue
            # Check if bet_cache already covers this rm
            has_coverage = any(k.startswith(f"{rm_val}|") for k in bet_cache)
            if not has_coverage:
                print(f"  Fetching bet data for {rm_val} ({bet_stem})...", flush=True)
                _load_bet_period(bet_stem, bet_cache)
                save_bet_cache(bet_cache)
                print(f"  bet-cache.json updated ({len(bet_cache)} entries)\n")
            loaded_bet_stems.add(bet_stem)

        if n >= n_needed:
            break
    else:
        print(f"Ran out of sessions — only {count_punkter(bet_data)} punkter available.")

    return all_votes, bet_data, bet_dates, bet_rm, bet_cache

# ── party stance ──────────────────────────────────────────────────────────────
def derive_stance(party_tally, committee_approves):
    ja  = party_tally.get("Ja", 0)
    nej = party_tally.get("Nej", 0)
    av  = party_tally.get("Avstår", 0)
    if ja + nej + av == 0 or av >= ja and av >= nej:
        return "abstain"
    if committee_approves:
        return "for" if ja > nej else "against"
    return "against" if ja > nej else "for"

# ── Claude ────────────────────────────────────────────────────────────────────
_total_in = _total_out = 0

def extract_questions_for_bet(titel, punkter_data):
    global _total_in, _total_out
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    sections = []
    for punkt, pd in sorted(punkter_data.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        ptype = _detect_punkt_type(pd.get("forslag", ""))
        type_hint = ""
        if ptype in ("proposition", "proposition_and_motion"):
            type_hint = " [This involves a government proposition — frame the question around what the government proposes to do]"
        sections.append(f"PUNKT {punkt}: {pd['rubrik']}{type_hint}\n{pd['forslag'][:600]}")
    prompt = (
        f"Betänkande: {titel}\n\n"
        + "\n\n---\n\n".join(sections)
        + "\n\n---\n\n"
        "For each PUNKT above, write a single question in the style of quality journalism: "
        "clear and specific enough for an expert to find it accurate, but immediately "
        "understandable to anyone without political background. Focus on the real-world "
        "effect — what would actually change for people or society. "
        "When a punkt involves a government proposition, frame the question around the "
        "government's proposed change (e.g. 'Should the government be allowed to...'). "
        "When it involves opposition motions, frame it around the proposed alternative. "
        "Use neutral, formal language — no slang, no colloquialisms (e.g. never use 'schyssta', 'kolla', 'fixa'). "
        "Avoid procedural jargon like 'motion', 'betänkande', 'utskott', 'yrkande'. "
        "No em dashes. One sentence per punkt. Phrased so the person can answer yes or no.\n\n"
        "Reply ONLY with JSON where each key is the punkt number and the value has "
        "'sv' (Swedish) and 'en' (English) fields.\n"
        'Example: {"2": {"sv": "Ska arbetsgivare tvingas...", "en": "Should employers be required to..."}}'
    )
    msg = client.messages.create(model=MODEL, max_tokens=1024,
                                  messages=[{"role": "user", "content": prompt}])
    in_tok, out_tok = msg.usage.input_tokens, msg.usage.output_tokens
    _total_in  += in_tok
    _total_out += out_tok
    cost_sek = (in_tok * PRICE_IN + out_tok * PRICE_OUT) * USD_TO_SEK
    running_cost = (_total_in * PRICE_IN + _total_out * PRICE_OUT) * USD_TO_SEK
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"    [{ts}] tokens: {in_tok} in / {out_tok} out  |  {cost_sek:.3f} kr  |  running: {running_cost:.2f} kr", flush=True)
    raw = re.sub(r"^```[a-z]*\n?", "", msg.content[0].text.strip())
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)

# ── main ──────────────────────────────────────────────────────────────────────
_, bet_data, bet_dates, bet_rm, bet_cache = ensure_data(N_PUNKTER)

all_punkter = []
for bet in sorted(bet_dates, key=lambda b: bet_dates[b], reverse=True):
    for punkt in sorted(bet_data[bet], key=lambda x: int(x) if x.isdigit() else 0):
        all_punkter.append((bet, punkt, bet_dates[bet][:10], bet_rm.get(bet, "2025/26")))

print(f"Total voted punkter available: {len(all_punkter)}")
print(f"Processing the {N_PUNKTER} most recent...\n")
selected = all_punkter[:N_PUNKTER]

by_bet = defaultdict(list)
for bet, punkt, datum, rm in selected:
    by_bet[(rm, bet)].append((punkt, datum, rm))

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

def process_bet(bet, punkt_list):
    rm              = punkt_list[0][2]
    bet_info        = bet_cache.get(f"{rm}|{bet}", {})
    titel           = bet_info.get("titel", bet)
    all_bet_punkter = bet_info.get("punkter", {})

    relevant = {
        p: all_bet_punkter[p]
        for p, _, _ in punkt_list
        if p in all_bet_punkter and all_bet_punkter[p].get("forslag")
    }

    if not relevant:
        print(f"  {bet}: no forslag text, skipping", flush=True)
        questions_map = {}
    else:
        print(f"  {bet} [{rm}] ({titel[:45]}): calling Claude for {len(relevant)} punkter...", flush=True)
        try:
            questions_map = extract_questions_for_bet(titel, relevant)
        except Exception as e:
            print(f"    Claude error on {bet}: {e}", flush=True)
            questions_map = {}

    new_items = []
    for punkt, datum, rm in punkt_list:
        item_id = f"{rm}_{bet}_{punkt}"
        if item_id in existing_ids:
            continue

        tally = defaultdict(lambda: defaultdict(int))
        for vid, mp_votes in bet_data[bet][punkt].items():
            for v in mp_votes:
                tally[v.get("parti", "-")][v.get("rost", "?")] += 1

        ja_total           = sum(tally[p].get("Ja", 0) for p in tally)
        nej_total          = sum(tally[p].get("Nej", 0) for p in tally)
        committee_won      = ja_total > nej_total
        pd                 = all_bet_punkter.get(punkt, {})
        forslag_text       = pd.get("forslag", "").lower()
        committee_approves = "bifaller" in forslag_text

        if not forslag_text:
            outcome = "unknown"
        elif committee_won:
            outcome = "approved" if committee_approves else "rejected"
        else:
            outcome = "rejected" if committee_approves else "approved"

        party_stances = {
            party: derive_stance(tally[party], committee_approves)
            for party in PARTIES if party in tally
        }

        dok_id = bet_info.get("dok_id", "")
        committee_code, cat_sv, cat_en = _get_category(bet)
        punkt_type = _detect_punkt_type(pd.get("forslag", ""))
        new_items.append({
            "id":            item_id,
            "datum":         datum,
            "rm":            rm,
            "beteckning":    bet,
            "titel":         titel,
            "punkt":         punkt,
            "rubrik":        pd.get("rubrik", f"Punkt {punkt}"),
            "type":          punkt_type,
            "category_code": committee_code,
            "category_sv":   cat_sv,
            "category_en":   cat_en,
            "question_sv":   questions_map.get(punkt, {}).get("sv", ""),
            "question_en":   questions_map.get(punkt, {}).get("en", ""),
            "outcome":       outcome,
            "ja_total":      ja_total,
            "nej_total":     nej_total,
            "url":           f"https://data.riksdagen.se/dokument/{dok_id}" if dok_id else "",
            "party_stances": party_stances,
        })
    return new_items

print(f"Running with {WORKERS} parallel workers\n")
with ThreadPoolExecutor(max_workers=WORKERS) as executor:
    futures = {executor.submit(process_bet, bet, pl): bet for (rm, bet), pl in by_bet.items()}
    for future in as_completed(futures):
        new_items = future.result()
        with _save_lock:
            for item in new_items:
                if item["id"] not in existing_ids:
                    results.append(item)
                    existing_ids.add(item["id"])
                    _points_done += 1
            print(f"  [{_points_done}/{N_PUNKTER}] saved {len(new_items)} from {futures[future]}", flush=True)
            with open(OUTPUT, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

total_cost_sek = (_total_in * PRICE_IN + _total_out * PRICE_OUT) * USD_TO_SEK
print(f"\nDone. {len(results)} questions written to {OUTPUT}")
print(f"Total tokens: {_total_in} in / {_total_out} out  |  total cost: {total_cost_sek:.2f} kr")

empty = [r for r in results if not r.get("question_sv") or not r.get("question_en")]
if empty:
    print(f"\nWARNING: {len(empty)} questions have empty question text:")
    for r in empty:
        print(f"  {r['id']}")
    print(f"\nRe-run with --retry-empty to regenerate them.")
else:
    print(f"All {len(results)} questions have question text.")
