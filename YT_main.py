from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import pandas as pd

from dotenv import load_dotenv
from YT_YoutubeClient import YouTubeClient
from YT_search_queries import search_queries
from YT_CommunityGardenAnalyzer import CommunityGardenAnalyzer, OpenAiClient

def get_video_details(df):
    yt_client = YouTubeClient(os.getenv("YOUTUBE_API_KEY"))

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(yt_client.search, q): q for q in search_queries}
        for future in as_completed(futures):
            q = futures[future]
            items = future.result()
            for item in items:
                vid = item['id']['videoId']
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

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(yt_client.get_video_transcript, vid): vid for vid in df.index}
        for future in as_completed(futures):
            vid = futures[future]
            tx = future.result()
            df.loc[vid, "Transcript"] = tx


def analyze_videos(df):
    yt_open_id_client = OpenAiClient(os.getenv("OPENAI_API_KEY"))
    yt_community_analyzer = CommunityGardenAnalyzer(yt_open_id_client)

    def analyze_video(vid):
        title = df.loc[vid, "Video Title"]
        description = df.loc[vid, "Description"]
        transcript = df.loc[vid, "Transcript"]
        return yt_community_analyzer.analyze(title, description, transcript)

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(analyze_video, vid): vid for vid in df.index}
        for future in as_completed(futures):
            vid = futures[future]
            analysis = future.result()
            if analysis:
                df.loc[vid, "Garden Type"] = analysis.garden_type
                df.loc[vid, "Garden Name"] = analysis.garden_name
                df.loc[vid, "Address"] = analysis.address
                df.loc[vid, "Summary"] = analysis.summary

if __name__=="__main__":
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
    df.set_index("ID", inplace=True)  # Gán "ID" làm index ngay từ đầu

    # Calling YouTube API and YouTube Transcription API to get video details
    # based on search queries (Title, Description, Transcript)
    get_video_details(df)

    # Using OpenAI model to transfer text-to-text based on the given prompts
    # and extract requested information
    analyze_videos(df)

    # Get lat, lon, postcode


    df.to_csv("youtube_garden_results.csv")
