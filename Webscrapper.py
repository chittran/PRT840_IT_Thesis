import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
import time
import csv
import json

# ===== CONFIG =====
SERP_API_KEY = "2a8a0e31e6167b8a24146c0fdd449076c9f4332fcd0bcad95730d9a37e98c2ce"
QUERIES = [
    "community garden Northern Australia",
    "garden in Northern Australia",
    "garden in Australia",
    "Australian community garden"
]
MAX_RESULTS_PER_QUERY = 250
NAU_POSTCODES = ['08', '67', '48', '46', '47']  # postcode prefix of Northern Australia


# ===== SerpAPI Functions =====
def get_urls_from_serpapi(query, max_results, api_key):
    urls = []
    for start in range(0, max_results, 100):
        params = {
            "q": query,
            "api_key": api_key,
            "engine": "google",
            "num": 100,
            "start": start
        }
        response = requests.get("https://serpapi.com/search", params=params)
        results = response.json()
        batch = [r["link"] for r in results.get("organic_results", [])]

        if not batch:
            break
        urls.extend(batch)
        if len(urls) >= max_results:
            break

    return urls[:max_results]


def scrape_info_from_url(url, geolocator):
    try:
        print(f"🔍 Processing: {url}")
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        if not soup.find(string=lambda t: t and "community garden" in t.lower()):
            return None

        name_tag = soup.find("h1") or soup.find("h2") or soup.title
        name = name_tag.get_text(strip=True) if name_tag else "unclear"

        address_tag = soup.find(string=lambda t: t and any(x in t for x in ["Northern", "Australia", "Territory", "QLD", "WA"]))
        address = address_tag.strip() if address_tag else "unclear"

        lat, lon = "", ""
        if address != "unclear":
            location = geolocator.geocode(address)
            if location:
                lat, lon = location.latitude, location.longitude

        return {
            "name": name,
            "address": address,
            "postcode": "",
            "latitude": lat,
            "longitude": lon,
            "imageUrl": ""
        }

    except Exception as e:
        print(f"❌ Error at {url}: {e}")
        return None


def fetch_serpapi_data():
    geolocator = Nominatim(user_agent="garden-locator")
    all_urls = []
    for query in QUERIES:
        urls = get_urls_from_serpapi(query, MAX_RESULTS_PER_QUERY, SERP_API_KEY)
        all_urls.extend(urls)

    all_urls = list(set(all_urls))  # remove duplicates
    print(f"🔗 Total unique URLs from SerpAPI: {len(all_urls)}")

    results = []
    for url in all_urls:
        info = scrape_info_from_url(url, geolocator)
        if info:
            results.append(info)
        time.sleep(1)
    return results


# ===== Scrape from communitygarden.org.au =====
listGarden = []


def addGarden(listTagGarden):
    for item in listTagGarden:
        name = item.get('data-title')
        address = item.get('data-address')
        postcodestr = address[-4:]
        if postcodestr.isnumeric() and postcodestr[:2] in NAU_POSTCODES:
            listGarden.append({
                "name": name,
                "address": address,
                "postcode": postcodestr,
                "latitude": item.get('data-latitude'),
                "longitude": item.get('data-longitude'),
                "imageUrl": item.get('data-image')
            })


def getGardensByLocation(url, start_page):
    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "referer": url,
        "user-agent": "Mozilla/5.0"
    }

    page = start_page
    max_page = start_page
    while page <= max_page:
        payload = f'keyword_search=&location_search=&search_radius=3&action=listeo_get_listings&page={page}&style=list'
        response = requests.post("https://communitygarden.org.au/wp-admin/admin-ajax.php", headers=headers, data=payload)
        if response.status_code != 200:
            print("❌ AJAX error")
            break

        data = response.json()
        html = data.get('html', "")
        if html:
            max_page = data.get("max_num_pages", max_page)
            soup = BeautifulSoup(html, 'html.parser')
            tagGardens = soup.find_all("div", class_="listing-item-container listing-geo-data list-layout listing-type-service")
            addGarden(tagGardens)
        page += 1


def GardenServiceCategory(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        print("❌ Failed to load:", url)
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    divs = soup.find_all("div", class_="listing-item-container listing-geo-data list-layout listing-type-service")
    if divs:
        addGarden(divs)

    if soup.find("ul", class_="pagination"):
        getGardensByLocation(url, 2)


def getGardensByListLocation(urls):
    for url in urls:
        GardenServiceCategory(url)


# ===== Save to CSV =====
def saveGardensToCSV(gardens, filename="all_community_gardens.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "address", "postcode", "latitude", "longitude", "imageUrl"])
        writer.writeheader()
        for garden in gardens:
            writer.writerow(garden)
    print(f"✅ Saved {len(gardens)} gardens to {filename}")


# ===== Main Entry =====
def main():
    print("🚀 Starting data collection...")

    urlServiceCategory = [
        "https://communitygarden.org.au/service-category/nt",
        "https://communitygarden.org.au/service-category/nsw/",
        "https://communitygarden.org.au/service-category/act/",
        "https://communitygarden.org.au/service-category/qld/",
        "https://communitygarden.org.au/service-category/sa/",
        "https://communitygarden.org.au/service-category/tas/",
        "https://communitygarden.org.au/service-category/vic/",
        "https://communitygarden.org.au/service-category/wa/"
    ]

    getGardensByListLocation(urlServiceCategory)
    print(f"🌱 Found {len(listGarden)} gardens from communitygarden.org.au")

    serpapi_gardens = fetch_serpapi_data()
    print(f"🔎 Found {len(serpapi_gardens)} gardens from Google SerpAPI")

    all_gardens = listGarden + serpapi_gardens
    unique_gardens = list({json.dumps(g, sort_keys=True) for g in all_gardens})
    unique_gardens = [json.loads(g) for g in unique_gardens]
    print(f"📦 Total unique gardens: {len(unique_gardens)}")

    saveGardensToCSV(unique_gardens)


if __name__ == "__main__":
    main()
