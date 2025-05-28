import os
import requests
import csv
import re
import json
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
import openai

from YT_keywords import community_garden_keywords, region_keywords
from YT_search_queries import search_queries
from YT_prompts import Community_garden_definition_rule

openai.api_key = os.getenv("OPENAI_API_KEY", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "AIzaSyAPWRtOSYrn0t5BhtAXbeC4Q6kjKMa3CJk")

BATCH_SIZE = 10   # number of videos per single OpenAI call
hf_cache = {}     # cache results by video_id

# Get YouTube Meatadata 
def youtube_search(query, api_key, max_results_per_page=50, total_results=100):
    base = "https://www.googleapis.com/youtube/v3/search"
    items, token = [], None
    params = {"part":"snippet","q":query,"type":"video",
              "maxResults":max_results_per_page,"key":api_key}
    while True:
        if token: params["pageToken"] = token
        r = requests.get(base, params=params)
        if r.status_code!=200: break
        data = r.json()
        items.extend(data.get("items",[]))
        token = data.get("nextPageToken")
        if not token or len(items)>=total_results: break
    return items[:total_results]

def get_video_details(video_ids, api_key):
    base = "https://www.googleapis.com/youtube/v3/videos"
    details = {}
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        params = {"part":"snippet","id":",".join(chunk),"key":api_key}
        r = requests.get(base, params=params)
        if r.status_code!=200: continue
        for item in r.json().get("items", []):
            details[item["id"]] = item["snippet"]
    return details

def get_video_transcript(video_id):
    try:
        segs = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join(s["text"] for s in segs)
    except:
        return ""

# Local extraction
def extract_garden_name(text):
    pat = r"(?P<name>(?:\b[A-Z][a-zA-Z]+\b\s+){1,5}Community Garden)"
    m = re.search(pat, text, flags=re.IGNORECASE)
    return m.group("name").strip() if m else ""

def is_community_garden_video(text):
    t = text.lower()
    return any(k in t for k in community_garden_keywords) and any(r in t for r in region_keywords)

def format_published_time(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z","+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_str

# OpenAI extraction
def analyze_video_batch(combined_texts):
    """
    Send one prompt with multiple transcripts, return a list of dicts.
    """
    # Build prompt enumerating each transcript
    body = Community_garden_definition_rule + "\n"
    for idx, txt in enumerate(combined_texts, start=1):
        body += f"\n[{idx}]\nTranscript:\n{txt}\n"
    body += (
        f"\nReturn a JSON array of length {len(combined_texts)}, "
        "where each element is an object with keys: "
        "garden_type, garden_name, address, summary, "
        "in the same order as the inputs."
    )

    # Call ChatCompletion once
    resp = openai.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role":"system","content":"Return ONLY a JSON array of objects."},
            {"role":"user","content":body}
        ],
        temperature=0.0,
        max_tokens=4096
    )
    text = resp.choices[0].message.content.strip()

    # Extract JSON array
    start, end = text.find("["), text.rfind("]")
    if start==-1 or end==-1:
        raise ValueError("Batch response JSON not found")
    arr = json.loads(text[start:end+1])
    return arr

def save_results_to_csv(results, details_map, output_file):
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Search Query","YouTube Link","Video Title","Channel Link","Channel Name",
            "Published At","Description","Hashtags","Transcript",
            "Garden Type","Garden Name","Address","Summary"
        ])

        # Gather all uncached videos that pass local keyword filter
        to_process = []
        for item in results:
            vid = item['id']['videoId']
            title = item['snippet']['title']
            desc  = item['snippet']['description']
            tx    = get_video_transcript(vid)
            combined = f"{title} {desc} {tx}"
            if not is_community_garden_video(combined):
                continue
            if vid not in hf_cache:
                to_process.append((item, vid, combined))
            print(title)
            
        # Batch-call OpenAI for those uncached
        for i in range(0, len(to_process), BATCH_SIZE):
            batch = to_process[i:i+BATCH_SIZE]
            texts = [b[2] for b in batch]
            ai_results = analyze_video_batch(texts)
            # store into cache
            for (_, vid, _), res in zip(batch, ai_results):
                hf_cache[vid] = res

        # Write out every video that passed filter, pulling from cache
        for item in results:
            vid = item['id']['videoId']
            if vid not in hf_cache or not is_community_garden_video(
                    f"{item['snippet']['title']} {item['snippet']['description']} {get_video_transcript(vid)}"):
                continue

            snip = item['snippet']
            det  = details_map.get(vid, {})
            desc = det.get('description', "")
            tags = det.get('tags', [])
            pub  = format_published_time(det.get('publishedAt', ""))
            tx   = get_video_transcript(vid)

            gem = hf_cache[vid]
            gtype   = gem.get("garden_type",   "Other/Unclear")
            gname   = gem.get("garden_name",    extract_garden_name(tx) or "N/A")
            address = gem.get("address",        "N/A")
            summ    = gem.get("summary",        "")

            writer.writerow([
                item['search_query'],
                f"https://youtu.be/{vid}",
                snip['title'],
                f"https://www.youtube.com/channel/{snip['channelId']}",
                snip['channelTitle'],
                pub,
                desc,
                ",".join(tags),
                tx,
                gtype,
                gname,
                address,
                summ
            ])
          

def main():
    all_results = []
    for q in search_queries:
        vids = youtube_search(q, YOUTUBE_API_KEY, total_results=50)
        for v in vids:
            v['search_query'] = q
        all_results.extend(vids)

    # remove duplicates based on videoId
    seen = set()
    unique_results = []
    for item in all_results:
        vid = item.get('id', {}).get('videoId')
        if vid and vid not in seen:
            seen.add(vid)
            unique_results.append(item)


    video_ids = [v['id']['videoId'] for v in unique_results if v['id'].get('videoId')]
    details_map = get_video_details(video_ids, YOUTUBE_API_KEY) if video_ids else {}

    save_results_to_csv(unique_results, details_map, "youtube_gardens_chatGPT_all.csv")

if __name__=="__main__":
    main()