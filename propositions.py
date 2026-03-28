import requests

url = "http://data.riksdagen.se/dokumentlista/"
params = {
    "doktyp": "prop",
    "utformat": "json",
    "sort": "datum",
    "sortorder": "desc",
    "antal": 50
}

headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, params=params, headers=headers)
data = response.json()

docs = data["dokumentlista"]["dokument"]
propositions = [doc for doc in docs if doc.get("dokumentnamn") == "Proposition"][:10]
for doc in propositions:
    print(f"{doc['datum']} — {doc['beteckning']}: {doc['titel']}")
