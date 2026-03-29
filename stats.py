import json
from collections import defaultdict

with open("questions.json", encoding="utf-8") as f:
    questions = json.load(f)

total = len(questions)
empty = [q for q in questions if not q.get("question_sv") or not q.get("question_en")]

by_rm = defaultdict(list)
for q in questions:
    by_rm[q.get("rm", "?")].append(q)

by_cat = defaultdict(list)
for q in questions:
    by_cat[q.get("category_code", "?")].append(q)

by_type = defaultdict(int)
for q in questions:
    by_type[q.get("type", "?")] += 1

print(f"{'─'*50}")
print(f"  QUESTIONS.JSON STATS")
print(f"{'─'*50}")
print(f"  Total questions : {total}")
print(f"  Missing text    : {len(empty)}")
print()

print(f"  BY SESSION (rm)")
print(f"  {'rm':<12} {'count':>6}  {'missing':>8}")
print(f"  {'─'*30}")
for rm in sorted(by_rm, reverse=True):
    qs = by_rm[rm]
    miss = sum(1 for q in qs if not q.get("question_sv"))
    print(f"  {rm:<12} {len(qs):>6}  {miss:>8}")
print()

print(f"  BY CATEGORY")
print(f"  {'code':<8} {'count':>6}  {'missing':>8}")
print(f"  {'─'*30}")
for cat in sorted(by_cat, key=lambda c: -len(by_cat[c])):
    qs = by_cat[cat]
    miss = sum(1 for q in qs if not q.get("question_sv"))
    print(f"  {cat:<8} {len(qs):>6}  {miss:>8}")
print()

print(f"  BY TYPE")
for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
    print(f"  {t:<30} {n:>6}")
print(f"{'─'*50}")
