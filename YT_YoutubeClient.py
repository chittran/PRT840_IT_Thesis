import requests
from youtube_transcript_api import YouTubeTranscriptApi
     
class YouTubeClient:
    def __init__(self, youtube_api_key=None):
        self.youtube_api_key = youtube_api_key

    # Get YouTube Metadata
    def search(self, query, page_size=50, total_results=100):
        base_url = "https://www.googleapis.com/youtube/v3/search"
        page_size = min(page_size, 50)  # API limit
        collected_items = []

        next_token = None
        while len(collected_items) < total_results:
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": min(page_size, total_results - len(collected_items)),
                "key": self.youtube_api_key
            }
            if next_token:
                params["pageToken"] = next_token
            try:
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                print(f"Error during request: {e}")
                break

            collected_items.extend(data.get("items", []))
            next_token = data.get("nextPageToken")

            if not next_token:
                break
    
        return collected_items

    def get_video_details(self, vids):
        base_url = "https://www.googleapis.com/youtube/v3/videos"
        details = {}
        chunk_size = 50  # YouTube API max limit

        for i in range(0, len(vids), chunk_size):
            chunk = vids[i:i + chunk_size]
            params = {
                "part": "snippet",
                "id": ",".join(chunk),
                "key": self.youtube_api_key
            }
            try:
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                print(f"Error fetching details for chunk {chunk}: {e}")
                continue

            for item in data.get("items", []):
                details[item["id"]] = item.get("snippet", {})

        return details

    def get_video_transcript(self, vid):
        try:
            segments = YouTubeTranscriptApi.get_transcript(vid)
            return " ".join(segment["text"] for segment in segments)
        except Exception as e:
            print(f"Unexpected error fetching transcript for {vid}: {e}")
            return ""
