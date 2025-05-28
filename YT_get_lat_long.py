import csv
import requests
from rapidfuzz import fuzz


# Increase CSV field size limit to handle large fields
csv.field_size_limit(10**8)

INPUT_CSV  = "youtube_gardens_chatGPT_all.csv"
THRESHOLD  = 90  
GOOGLE_MAPS_API_KEY = 'AIzaSyBXQQS-eHPMc1Tg1zzZPQJl_ULfo-_A2p8'


def geocode_google(query):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": query,
        "key": GOOGLE_MAPS_API_KEY,
        "region": "au",
        "result_type": "street_address|postal_code"
    }
    resp = requests.get(url, params=params)
    data = resp.json()

    if data.get("status") != "OK" or not data.get("results"):
        return None, None, "N/A"

    first = data["results"][0]
    lat = first["geometry"]["location"]["lat"]
    lng = first["geometry"]["location"]["lng"]

    comp = first.get("address_components", [])
    postcode = next(
        (c["long_name"] for c in comp if "postal_code" in c["types"]),
        None
    )
    if postcode:
        return lat, lng, postcode

    rev_resp = requests.get(url, params={
        "latlng": f"{lat},{lng}",
        "key": GOOGLE_MAPS_API_KEY,
        "result_type": "postal_code"
    })
    rev = rev_resp.json()
    if rev.get("status") == "OK" and rev.get("results"):
        comp2 = rev["results"][0].get("address_components", [])
        postcode2 = next(
            (c["long_name"] for c in comp2 if "postal_code" in c["types"]),
            None
        )
        return lat, lng, postcode2 or "N/A"

    return lat, lng, "N/A"


def completeness(g):
    keys = ["Garden Name", "Address", "Latitude", "Longitude", "Postcode", "Summary"]
    return sum(1 for k in keys if g.get(k) and g.get(k) != "N/A")


def fingerprint(g):
    name    = g.get("Garden Name", "").strip()
    address = g.get("Address", "").strip()
    return f"{name} {address}"


def remove_duplicates(listGarden, threshold=THRESHOLD):
    unique = []
    scores = []

    for g in listGarden:
        name = g.get("Garden Name","").strip()
        if name == "N/A":
            unique.append(g)
            scores.append(completeness(g))
            continue

        fp = fingerprint(g)
        matched = False
        for i, ug in enumerate(unique):
            if ug.get("Garden Name","") != "N/A" and \
               fuzz.ratio(fp, fingerprint(ug)) >= threshold:
                matched = True
                new_score = completeness(g)
                if new_score > scores[i]:
                    unique[i] = g
                    scores[i] = new_score
                break

        if not matched:
            unique.append(g)
            scores.append(completeness(g))

    return unique


NAU_POSTCODES = ['08','67','48','46','47']


def write_to_csv(records, output_file="final_gardens.csv"):
    """
    Ghi file CSV với header:
    garden type, garden name, address, lat, lng, postcode
    """
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["garden type", "garden name", "address", "lat", "lng", "postcode", "YouTube Link", "Published Date"])
        for garden_type, garden_name, address, lat, lng, postcode, Youtube_link, Published_date, dup_count, latest_upd in records:
            writer.writerow([garden_type, garden_name, address, lat, lng, postcode, Youtube_link, Published_date, dup_count, latest_upd])
    print(f"Wrote {len(records)} records to {output_file}")


def main():
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        gardens_all = list(reader)
    
    # Remove duplucates
    unique_gardens = remove_duplicates(gardens_all, threshold=THRESHOLD)

    # Filter, geocode, build listGarden
    listGarden = []
    for record in unique_gardens:
        gtype = record.get("Garden Type", "").strip()
        if gtype not in ("Community Garden"):
            continue

        name    = record.get("Garden Name","").strip()
        address = record.get("Address","").strip()
        if address == "N/A":
            lat, lng, postcode = "N/A", "N/A", "N/A"
        else:
            lat, lng, postcode = geocode_google(f"{name} {address}")

        if postcode != "N/A" and postcode[:2] not in NAU_POSTCODES:
            continue
               
        Youtube_link = record.get("YouTube Link", "").strip()
        Published_date = record.get("Published At", "").strip()

        # Count duplicate and extract latest_updated
        fp = fingerprint(record)
        cluster = [r for r in gardens_all
                   if r.get("Garden Type","") == gtype
                   and fuzz.ratio(fp, fingerprint(r)) >= THRESHOLD]
        dup_count = len(cluster)
        # Find lastest updates date
        dates = [r.get("Published At","") for r in cluster if r.get("Published At")]
        latest_upd = max(dates) if dates else "N/A"


        listGarden.append((gtype, name, address, lat, lng, postcode, Youtube_link, Published_date, dup_count, latest_upd))

    write_to_csv(listGarden, "YT_final_community_gardens_2.csv")


if __name__ == "__main__":
    main()
