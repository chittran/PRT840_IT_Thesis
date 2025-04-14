import requests
import pyodbc
import json
from bs4 import BeautifulSoup

listGarden = []

def insertGardenoDB(listGarden):
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                      'SERVER=localhost;'
                      'DATABASE=CommunityGardenNT;'
                      'UID=sa;'
                      'PWD=123')
    # Create a cursor object
    cursor = conn.cursor()

    # SQL query for inserting multiple rows
    insert_query = """
        INSERT INTO CommunityGarden (Name, Address, Postcode, Latitude, Longitude, ImageUrl)
        VALUES (?, ?, ?, ?, ?, ?)
    """

    # Prepare data to insert into the table as a list of tuples
    values_to_insert = [(record['name'], record['address'], record['postcode'], record['latitude'], record['longitude'], record['imageUrl']) for record in listGarden]

    # Execute the insertion for all rows
    cursor.executemany(insert_query, values_to_insert)

    # Commit the transaction
    conn.commit()

    # Close the cursor and connection
    cursor.close()
    conn.close()
    print("Data inserted successfully.")


NAupostcode = ['08','67','48','46','47']
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
                                    
                    
                    
def getGardensByLocation(urlServiceCategory,page):
    BASE_HEADERS = {
    "accept":"application/json, text/javascript, */*; q=0.01",
    "accept-language":"vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7,fr-FR;q=0.6,fr;q=0.5",
    "content-type":"application/x-www-form-urlencoded; charset=UTF-8",
    "origin":"https://communitygarden.org.au",
    "priority":"u=1, i",
    "referer":urlServiceCategory,
    "sec-ch-ua-mobile":"?0",
    "sec-ch-ua-platform":"macOS",
    "sec-fetch-mode":"cors",
    "sec-fetch-site":"same-origin",
    "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "x-requested-with":"XMLHttpRequest"
    }
    maxNumPage = page
    while page <= maxNumPage:
       
        raw_data = f'keyword_search=&location_search=&search_radius=3&action=listeo_get_listings&action=listeo_get_listings&page={page}&style=list&grid_columns=&per_page=&custom_class=&order=rand'
        page = page + 1
        response = requests.post("https://communitygarden.org.au/wp-admin/admin-ajax.php", headers=BASE_HEADERS, data=raw_data)
        if(response.status_code != 200):
            print("error")
            break
        data = response.json()
        html = data['html']
        if(html):
            try:
                max_num_pages = data['max_num_pages']
                maxNumPage = max_num_pages
                soupGardens = BeautifulSoup(html, 'html.parser')
                tagGardens = soupGardens.find_all("div", class_="listing-item-container listing-geo-data list-layout listing-type-service")
                addGarden(tagGardens)
            except:
              print("An exception occurred")

# Step 1: Fetch the Webpage

def GardenSeviceCategory(url):
    #url = "https://communitygarden.org.au/service-category/nsw"
    headers = {"User-Agent": "Mozilla/5.0"}
    page = requests.get(url, headers=headers)

    if page.status_code != 200:
        print("Failed to retrieve the webpage.")
        exit()
    soupPageGarden = BeautifulSoup(page.text, 'html')
    tagDivGardens = soupPageGarden.find_all("div", class_="listing-item-container listing-geo-data list-layout listing-type-service")
    tagUlGardens = soupPageGarden.find_all("ul", class_="pagination")

    if len(tagDivGardens)>0 :
        addGarden(tagDivGardens)
    if len(tagUlGardens)>0 :
        getGardensByLocation(url,2)


def getGardensByListLocation(listUrlServiceCategory):
    for item in listUrlServiceCategory:
        GardenSeviceCategory(item)


def main():
    urlServiceCategory = ["https://communitygarden.org.au/service-category/nt",
                          "https://communitygarden.org.au/service-category/nsw/",
                          "https://communitygarden.org.au/service-category/act/",
                          "https://communitygarden.org.au/service-category/qld/",
                          "https://communitygarden.org.au/service-category/sa/",
                          "https://communitygarden.org.au/service-category/tas/",
                          "https://communitygarden.org.au/service-category/vic/",
                          "https://communitygarden.org.au/service-category/wa/"
                        ]
    getGardensByListLocation(urlServiceCategory)

if __name__ == "__main__":
    main()
# Remove duplicates
unique_gardens = list({json.dumps(garden, sort_keys=True) for garden in listGarden})
# Convert back from JSON string to dict
unique_gardens = [json.loads(g) for g in unique_gardens]
for record in unique_gardens:
    print(record['name'],'/',record['address'],'/',record['latitude'],'/', record['longitude'],'/',record['imageUrl'],'\n')
insertGardenoDB(unique_gardens)
print(len(unique_gardens)) 

