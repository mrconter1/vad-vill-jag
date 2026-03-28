import requests

url = "http://data.riksdagen.se/dokumentlista/"
params = {
    "doktyp": "prop",
    "utformat": "json",
    "sort": "datum",
    "sortorder": "desc",
    "antal": 10
}

headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, params=params, headers=headers)
data = response.json()

docs = data["dokumentlista"]["dokument"]
for doc in docs:
    print(f"{doc['datum']} — {doc['beteckning']}: {doc['titel']}")
