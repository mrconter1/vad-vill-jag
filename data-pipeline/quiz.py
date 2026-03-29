import json
import random
import sys
import os

PARTIES = ["S", "SD", "M", "V", "C", "KD", "MP", "L"]
PARTY_NAMES = {
    "S":  "Socialdemokraterna",
    "SD": "Sverigedemokraterna",
    "M":  "Moderaterna",
    "V":  "Vänsterpartiet",
    "C":  "Centerpartiet",
    "KD": "Kristdemokraterna",
    "MP": "Miljöpartiet",
    "L":  "Liberalerna",
}
N = int(sys.argv[1]) if len(sys.argv) > 1 else 50

def load_questions():
    with open("questions.json", encoding="utf-8") as f:
        all_q = json.load(f)
    return [q for q in all_q if q.get("question_sv") not in (None, "", "N/A")
            and q.get("question_en") not in (None, "", "N/A")
            and q.get("party_stances")]

def pick_language():
    print("Language / Språk:")
    print("  1. Svenska")
    print("  2. English")
    choice = input("  > ").strip()
    return "en" if choice == "2" else "sv"

def get_question_text(q, lang):
    return q.get(f"question_{lang}") or q.get("question_sv", "")

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def run_quiz():
    questions = load_questions()
    sample = random.sample(questions, min(N, len(questions)))

    lang = pick_language()

    if lang == "sv":
        labels = {"for": "Ja", "against": "Nej", "skip": "Hoppa över"}
        prompt = "Ditt svar (j/n/hoppa): "
        align_header = "=== DITT POLITISKA RESULTAT ==="
        align_label = "Andel överensstämmelse"
        questions_label = "frågor besvarade"
        category_header = "Per ämne:"
    else:
        labels = {"for": "Yes", "against": "No", "skip": "Skip"}
        prompt = "Your answer (y/n/skip): "
        align_header = "=== YOUR POLITICAL ALIGNMENT ==="
        align_label = "Agreement"
        questions_label = "questions answered"
        category_header = "By topic:"

    answers = []  # list of (question, user_stance) where user_stance in ('for', 'against', None)

    for i, q in enumerate(sample):
        clear()
        cat = q.get(f"category_{lang}", q.get("category_sv", ""))
        print(f"  Question {i+1} of {len(sample)}  [{cat}]")
        print(f"  {q.get('datum', '')[:7]}")
        print()
        print(f"  {get_question_text(q, lang)}")
        print()
        print(f"  1 / j/y  = {labels['for']}")
        print(f"  2 / n    = {labels['against']}")
        print(f"  3 / enter = {labels['skip']}")
        print()

        while True:
            raw = input(f"  {prompt}").strip().lower()
            if raw in ("1", "j", "y", "ja", "yes"):
                stance = "for"
                break
            elif raw in ("2", "n", "no", "nej"):
                stance = "against"
                break
            elif raw in ("3", "", "s", "skip", "hoppa"):
                stance = None
                break
        answers.append((q, stance))

    clear()
    print(f"\n  {align_header}\n")

    # Score per party
    party_agree   = {p: 0 for p in PARTIES}
    party_total   = {p: 0 for p in PARTIES}
    cat_agree     = {}
    cat_total     = {}

    for q, user_stance in answers:
        if user_stance is None:
            continue
        stances = q.get("party_stances", {})
        cat = q.get(f"category_{lang}", q.get("category_sv", "?"))
        cat_agree.setdefault(cat, {p: 0 for p in PARTIES})
        cat_total.setdefault(cat, {p: 0 for p in PARTIES})

        for p in PARTIES:
            party_stance = stances.get(p)
            if party_stance == "abstain" or party_stance is None:
                continue
            party_total[p] += 1
            cat_total[cat][p] += 1
            if party_stance == user_stance:
                party_agree[p] += 1
                cat_agree[cat][p] += 1

    answered = sum(1 for _, s in answers if s is not None)
    print(f"  {answered} {questions_label}\n")

    scores = {
        p: (party_agree[p] / party_total[p] * 100) if party_total[p] > 0 else None
        for p in PARTIES
    }
    ranked = sorted(
        [(p, s) for p, s in scores.items() if s is not None],
        key=lambda x: -x[1]
    )

    bar_width = 30
    for p, score in ranked:
        filled = int(score / 100 * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        name = PARTY_NAMES.get(p, p)
        print(f"  {p:<3} {bar} {score:5.1f}%  ({party_agree[p]}/{party_total[p]})  {name}")

    if ranked:
        winner = ranked[0][0]
        print(f"\n  >>> {PARTY_NAMES.get(winner, winner)} ({winner}) <<<\n")

    # Per category breakdown
    if cat_total:
        print(f"\n  {category_header}\n")
        for cat in sorted(cat_total):
            cat_scores = {
                p: (cat_agree[cat][p] / cat_total[cat][p] * 100)
                for p in PARTIES
                if cat_total[cat].get(p, 0) > 0
            }
            if not cat_scores:
                continue
            top = sorted(cat_scores.items(), key=lambda x: -x[1])[:3]
            top_str = "  ".join(f"{p} {s:.0f}%" for p, s in top)
            print(f"  {cat:<35} {top_str}")

    print()

if __name__ == "__main__":
    run_quiz()
