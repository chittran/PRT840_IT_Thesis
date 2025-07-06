import logging
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig


class YouTubeClient:
    def __init__(self, youtube_api_key, proxy_username, proxy_password):
        self.logger = logging.getLogger(__name__)
        self.youtube_api_key = youtube_api_key
        self.transcript_api = YouTubeTranscriptApi()
        # self.transcript_api = YouTubeTranscriptApi(
        #     proxy_config=WebshareProxyConfig(
        #         proxy_username=proxy_username,
        #         proxy_password=proxy_password,
        #     )
        # )

    # Get YouTube Metadata
    def search(self, query, page_size=50, total_results=100):
        self.logger.info(f"Searching YouTube for query: {query}")

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
                "regionCode": "AU",
                "relevanceLanguage": "en",
                "key": self.youtube_api_key
            }
            if next_token:
                params["pageToken"] = next_token
            try:
                self.logger.debug(f"Requesting: {base_url} with params: {params}")
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                self.logger.error(f"Error during request: {e}")
                break

            collected_items.extend(data.get("items", []))
            next_token = data.get("nextPageToken")

            if not next_token:
                break
    
        self.logger.info(f"Found {len(collected_items)} items for query: {query}")
        return collected_items

    def get_video_details(self, vids):
        self.logger.info(f"Fetching video details for {len(vids)} videos")

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
                self.logger.debug(f"Requesting details for chunk: {chunk}")
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                self.logger.error(f"Error fetching details for chunk {chunk}: {e}")
                continue

            for item in data.get("items", []):
                details[item["id"]] = item.get("snippet", {})

        self.logger.info(f"Fetched details for {len(details)} videos")
        return details

    def get_video_transcript(self, vid):
        self.logger.info(f"Fetching transcript for video: {vid}")
        try:
            fetched_transcript = self.transcript_api.fetch(vid)
            transcript = " ".join(snippet.text for snippet in fetched_transcript)
            self.logger.info(f"Transcript fetched for video: {vid} (length: {len(transcript)} chars)")
            return transcript
        except Exception as e:
            self.logger.error(f"Unexpected error fetching transcript for {vid}: {e}")
            return ""
