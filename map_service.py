# import geopy.geocoders as gg

# geolocator = gg.Nominatim(user_agent="geoapi")

# def geocode_address(address):
#     try:
#         location = geolocator.geocode(address)
#         if location:
#             return location.latitude, location.longitude
#     except:
#         return None, None
from dataclasses import dataclass
import os
from typing import Optional, Protocol
import googlemaps
import requests

class GoogleMapsClient(Protocol):
    def geocode(client, address=None, place_id=None, components=None, bounds=None, region=None, language=None): Dict: ...
    def find_place(client, input, input_type, fields=None, location_bias=None, language=None): Dict: ...

@dataclass
class GeocodingResult:
    place_id: str
    lat: float
    lon: float

class MapService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client: GoogleMapsClient = googlemaps.Client(api_key)

    def geocode_address(self, name: str, address: Optional[str]) -> Optional[GeocodingResult]:
        # Try Geocoding API
        if address:
            geo_results = self.client.geocode(address)
            if geo_results:
                place = geo_results[0]
                location = place["geometry"]["location"]
                return GeocodingResult(
                    place_id=place["place_id"],
                    lat=location["lat"],
                    lon=location["lng"]
                )

        # Fallback to Places API
        query = f"{name}, {address}" if address else name
        place_results = self.client.find_place(input=query, input_type="textquery", fields=["geometry", "place_id"])
        candidates = place_results.get("candidates", [])
        if candidates:
            place = candidates[0]
            location = place["geometry"]["location"]
            location = place["geometry"]["location"]
            return GeocodingResult(
                place_id=place["place_id"],
                lat=location["lat"],
                lon=location["lng"]
            )

        # No result found
        return None

    def download_static_map(
        self,
        lat: float,
        lon: float,
        zoom: int = 18,
        size: str = "2048x2048",
        maptype: str = "satellite",
        save_dir: str = "maps",
        save_as: str = None
    ) -> str | None:
        os.makedirs(save_dir, exist_ok=True)
        # Default filename if none is given
        if not save_as:
            save_as = f"tile_{lat}_{lon}_z{zoom}.png"

        filepath = os.path.join(save_dir, save_as)

        url = (
            f"https://maps.googleapis.com/maps/api/staticmap?"
            f"center={lat},{lon}"
            f"&zoom={zoom}"
            f"&size={size}"
            f"&maptype={maptype}"
            f"&key={self.api_key}"
        )

        response = requests.get(url)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"✅ Saved: {filepath}")
            return filepath
        else:
            print(f"❌ Error {response.status_code}: Failed to download map.")
            print(response.text)
            return None

# - có nhà kính ?
# - có luống cây ?
# - đất trống ?
# - không phải sân bóng ?
# - là trường ?
# - là công viên ?
