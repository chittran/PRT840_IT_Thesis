from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import os
import random
import time
import pandas as pd

from dotenv import load_dotenv
from YT_YoutubeClient import YouTubeClient
from YT_search_queries import search_queries
from YT_CommunityGardenAnalyzer import CommunityGardenAnalyzer, OpenAiClient

logger = logging.getLogger(__name__)

def get_video_details(df):
    yt_client = YouTubeClient(
        os.getenv("YOUTUBE_API_KEY"),
        os.getenv("YOUTUBE_TRANSCRIPT_API_PROXY_USERNAME"),
        os.getenv("YOUTUBE_TRANSCRIPT_API_PROXY_PASSWORD")
    )

    logger.info("Starting YouTube search for all queries...")
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(yt_client.search, q, 10): q for q in search_queries}
        for future in as_completed(futures):
            q = futures[future]
            items = future.result()
            logger.info(f"Query '{q}' returned {len(items)} items.")

            for item in items:
                vid = item['id']['videoId']

                if vid in df.index:
                    logger.debug(f"Video {vid} already in DataFrame, skipping.")
                    continue # Skip if video already exists in DataFrame

                channel_id = item['snippet']['channelId']
                df.loc[vid] = {
                    "Search Query": q,
                    "YouTube Link": f"https://youtu.be/{vid}",
                    "Video Title": item['snippet']['title'],
                    "Channel Link": f"https://www.youtube.com/channel/{channel_id}",
                    "Channel Name": item['snippet']['channelTitle'],
                    "Published At": item['snippet'].get('publishedAt', ""),
                    "Description": item['snippet']['description'],
                    "Hashtags": "",
                    "Transcript": "",
                    "Garden Type": "",
                    "Garden Name": "",
                    "Address": "",
                    "Summary": "",
                }
                logger.debug(f"Added video {vid} to DataFrame.")

    def throttled_get_transcript(vid):
        time.sleep(random.uniform(1.0, 1.8)) # Throttle requests to avoid hitting API limits
        logger.info(f"Fetching transcript for video {vid}")
        return yt_client.get_video_transcript(vid)

    logger.info("Fetching transcripts for videos...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        videos_to_fetch = [vid for vid in df.index if not df.loc[vid, "Transcript"]]
        futures = {executor.submit(throttled_get_transcript, vid): vid for vid in videos_to_fetch}
        for future in as_completed(futures):
            vid = futures[future]
            tx = future.result()
            df.loc[vid, "Transcript"] = tx
            logger.info(f"Transcript fetched for video {vid}")

def analyze_videos(df):
    yt_open_id_client = OpenAiClient(os.getenv("OPENAI_API_KEY"))
    yt_community_analyzer = CommunityGardenAnalyzer(yt_open_id_client)

    def analyze_video(vid):
        title = df.loc[vid, "Video Title"]
        description = df.loc[vid, "Description"]
        transcript = df.loc[vid, "Transcript"]
        logger.info(f"Analyzing video {vid}")
        return yt_community_analyzer.analyze(title, description, transcript)

    logger.info("Starting analysis of videos...")
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(analyze_video, vid): vid for vid in df.index}
        for future in as_completed(futures):
            vid = futures[future]
            analysis = future.result()
            if analysis:
                df.loc[vid, "Garden Type"] = analysis.garden_type
                df.loc[vid, "Garden Name"] = analysis.garden_name
                df.loc[vid, "Address"] = analysis.address
                df.loc[vid, "Summary"] = analysis.summary
                logger.info(f"Analysis completed for video {vid}")
            else:
                logger.info(f"No community garden detected for video {vid}")

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)

    load_dotenv()  # looks for a file named .env in the current directory

    # Define column names
    columns = [
        "ID",  # YouTube video ID
        "Search Query", "YouTube Link", "Video Title", "Channel Link", "Channel Name",
        "Published At", "Description", "Hashtags", "Transcript",
        "Garden Type", "Garden Name", "Address", "Summary"
    ]

    # Create empty DataFrame
    df = pd.DataFrame(columns=columns)
    df.set_index("ID", inplace=True)

    try:
        df = pd.read_csv("youtube_garden_results.csv", index_col="ID")
        logger.info("Loaded existing youtube_garden_results.csv")
    except FileNotFoundError:
        logger.info("youtube_garden_results.csv not found, starting with empty DataFrame.")

    # Calling YouTube API and YouTube Transcription API to get video details
    # based on search queries (Title, Description, Transcript)
    get_video_details(df)

    # Using OpenAI model to transfer text-to-text based on the given prompts
    # and extract requested information
    # analyze_videos(df)

    # Get lat, lon, postcode

    df.to_csv("youtube_garden_results.csv")
    logger.info("Saved results to youtube_garden_results.csv")