import json
from collections import defaultdict

with open("questions.json", encoding="utf-8") as f:
    questions = json.load(f)

with open("bet-cache.json", encoding="utf-8") as f:
    bet_cache = json.load(f)

empty = [q for q in questions if not q.get("question_sv")]

print(f"=== EMPTY QUESTION INVESTIGATION ===\n")
print(f"Total empty: {len(empty)}\n")

# Check 1: Do these bets exist in bet_cache at all?
missing_from_cache = 0
in_cache_no_punkter = 0
in_cache_has_punkter_no_forslag = 0
in_cache_has_forslag = 0

examples_no_cache = []
examples_no_forslag = []
examples_has_forslag = []

for q in empty:
    key = f"{q['rm']}|{q['beteckning']}"
    bet = bet_cache.get(key)
    if not bet:
        missing_from_cache += 1
        if len(examples_no_cache) < 3:
            examples_no_cache.append(key)
    else:
        punkter = bet.get("punkter", {})
        p = q["punkt"]
        if p not in punkter:
            in_cache_no_punkter += 1
        else:
            forslag = punkter[p].get("forslag", "")
            if not forslag:
                in_cache_has_punkter_no_forslag += 1
                if len(examples_no_forslag) < 3:
                    examples_no_forslag.append((key, p))
            else:
                in_cache_has_forslag += 1
                if len(examples_has_forslag) < 3:
                    examples_has_forslag.append((key, p, forslag[:200]))

print(f"Root cause breakdown:")
print(f"  Not in bet_cache at all          : {missing_from_cache}")
print(f"  In cache but punkt missing        : {in_cache_no_punkter}")
print(f"  In cache, punkt exists, no forslag: {in_cache_has_punkter_no_forslag}")
print(f"  In cache WITH forslag (fixable!)  : {in_cache_has_forslag}")

if examples_no_cache:
    print(f"\nExamples not in cache:")
    for e in examples_no_cache:
        print(f"  {e}")

if examples_no_forslag:
    print(f"\nExamples in cache but no forslag:")
    for key, p in examples_no_forslag:
        print(f"  {key} punkt {p}")

if examples_has_forslag:
    print(f"\nExamples IN CACHE WITH FORSLAG (should have been processed):")
    for key, p, f in examples_has_forslag:
        print(f"  {key} punkt {p}")
        print(f"  forslag: {f}")
        print()

# Check 2: Forslag text length distribution for valid vs empty questions
print(f"\n=== FORSLAG LENGTH DISTRIBUTION ===")
valid = [q for q in questions if q.get("question_sv")]

def get_forslag(q):
    key = f"{q['rm']}|{q['beteckning']}"
    bet = bet_cache.get(key, {})
    return bet.get("punkter", {}).get(q["punkt"], {}).get("forslag", "")

empty_lengths = [len(get_forslag(q)) for q in empty]
valid_lengths  = [len(get_forslag(q)) for q in valid[:500]]

print(f"  Empty questions  — avg forslag length: {sum(empty_lengths)/max(len(empty_lengths),1):.0f} chars")
print(f"  Valid questions  — avg forslag length: {sum(valid_lengths)/max(len(valid_lengths),1):.0f} chars")
print(f"  Empty with zero-length forslag: {sum(1 for l in empty_lengths if l == 0)}")

# Check 3: Sample a few bet-cache entries from 2016/17 to see what's there
print(f"\n=== SAMPLE 2016/17 BET-CACHE ENTRIES ===")
sample_keys = [k for k in bet_cache if k.startswith("2016/17")][:5]
for key in sample_keys:
    bet = bet_cache[key]
    punkter = bet.get("punkter", {})
    forslag_lengths = [len(p.get("forslag","")) for p in punkter.values()]
    print(f"  {key}: {len(punkter)} punkter, forslag lengths: {forslag_lengths[:8]}")
