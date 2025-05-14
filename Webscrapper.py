import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
import time
import csv
import json

# === SERP API CONFIG ===
SERP_API_KEY = "2a8a0e31e6167b8a24146c0fdd449076c9f4332fcd0bcad95730d9a37e98c2ce"
QUERY = "community garden Northern Australia" or "garden in Northern Australia" or "garden in Australia" or "Australian community garden"
MAX_RESULTS = 10000


# === SerpAPI functions (source 1) ===
def get_urls_from_serpapi(query, max_results):
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google",
        "num": max_results,
    }
    response = requests.get("https://serpapi.com/search", params=params)
    results = response.json()
    urls = [r["link"] for r in results.get("organic_results", [])]
    return urls

def scrape_info_from_url(url, geolocator):
    try:
        print(f"🔍 processing (serpapi): {url}")
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        if not soup.find(string=lambda t: t and "community garden" in t.lower()):
            return None

        name_tag = soup.find("h1") or soup.find("h2") or soup.title
        name = name_tag.get_text(strip=True) if name_tag else "unclear"

        address_tag = soup.find(string=lambda t: t and ("Nothern Australia" in t or "Northern Territory" in t or "Queenland" in t or "Western Australia" in t))
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
        print(f"❌ error at {url}: {e}")
        return None

def fetch_serpapi_data():
    geolocator = Nominatim(user_agent="garden-locator")
    urls = get_urls_from_serpapi(QUERY, MAX_RESULTS)

    results = []
    for url in urls:
        info = scrape_info_from_url(url, geolocator)
        if info:
            results.append(info)
        time.sleep(1)
    return results


# === Web scrape from communitygarden.org.au (source 2) ===
listGarden = []
NAupostcode = ['08', '67', '48', '46', '47']

def addGarden(listTagGarden):
    for item in listTagGarden:
        nameGarden = item.get('data-title')
        addressGarden = item.get('data-address')
        postcodestr = addressGarden[-4:]
        postcode = ''
        if postcodestr.isnumeric() and postcodestr[:2] in NAupostcode:
            postcode = postcodestr
            latitudeGarden = item.get('data-latitude')
            longitudeGarden = item.get('data-longitude')
            imageGarden = item.get('data-image')
            listGarden.append({
                "name": nameGarden,
                "address": addressGarden,
                "postcode": postcode,
                "latitude": latitudeGarden,
                "longitude": longitudeGarden,
                "imageUrl": imageGarden
            })

def getGardensByLocation(urlServiceCategory, page):
    BASE_HEADERS = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://communitygarden.org.au",
        "referer": urlServiceCategory,
        "user-agent": "Mozilla/5.0"
    }
    maxNumPage = page
    while page <= maxNumPage:
        raw_data = f'keyword_search=&location_search=&search_radius=3&action=listeo_get_listings&page={page}&style=list'
        page += 1
        response = requests.post("https://communitygarden.org.au/wp-admin/admin-ajax.php", headers=BASE_HEADERS, data=raw_data)
        if response.status_code != 200:
            print("❌ error fetching ajax")
            break
        data = response.json()
        html = data['html']
        if html:
            try:
                maxNumPage = data['max_num_pages']
                soupGardens = BeautifulSoup(html, 'html.parser')
                tagGardens = soupGardens.find_all("div", class_="listing-item-container listing-geo-data list-layout listing-type-service")
                addGarden(tagGardens)
            except:
                print("⚠️ Exception in parsing HTML")

def GardenSeviceCategory(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    page = requests.get(url, headers=headers)
    if page.status_code != 200:
        print("❌ Failed to load:", url)
        return
    soupPageGarden = BeautifulSoup(page.text, 'html.parser')
    tagDivGardens = soupPageGarden.find_all("div", class_="listing-item-container listing-geo-data list-layout listing-type-service")
    tagUlGardens = soupPageGarden.find_all("ul", class_="pagination")
    if len(tagDivGardens) > 0:
        addGarden(tagDivGardens)
    if len(tagUlGardens) > 0:
        getGardensByLocation(url, 2)

def getGardensByListLocation(listUrlServiceCategory):
    for item in listUrlServiceCategory:
        GardenSeviceCategory(item)


# === Save to CSV (shared) ===
def saveGardensToCSV(listGarden, filename="all_community_gardens.csv"):
    fieldnames = ["name", "address", "postcode", "latitude", "longitude", "imageUrl"]
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in listGarden:
            writer.writerow(record)
    print(f"✅ Data saved to {filename}")


# === MAIN ===
def main():
    print("🚀 Starting data collection...")
    
    # 1. Crawl from communitygarden.org.au
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

    # 2. Crawl from SerpAPI
    serpapi_gardens = fetch_serpapi_data()
    print(f"🔎 Found {len(serpapi_gardens)} gardens from Google SerpAPI")

    # 3. Merge & remove duplicates
    all_gardens = listGarden + serpapi_gardens
    unique_gardens = list({json.dumps(g, sort_keys=True) for g in all_gardens})
    unique_gardens = [json.loads(g) for g in unique_gardens]
    print(f"📦 Merged total: {len(unique_gardens)} unique gardens")

    # 4. Save
    saveGardensToCSV(unique_gardens)

if __name__ == "__main__":
    main()
