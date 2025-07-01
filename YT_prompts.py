
Community_garden_definition_rule = """
Objective: Analyze the provided text from a YouTube video (title, description, transcript) to classify the type of garden discussed and extract relevant information. Assume content might relate to Australia unless otherwise specified.

Definitions and Classification Rules (Use ONLY these for this task):

1.  Community Garden: Classify as 'Community Garden' if the text describes:
    *   A garden explicitly called a "Community Garden" or similar collective term (e.g., "Community Allotments", "Neighbourhood Garden").
    *   A garden managed collectively by a group of people from a neighbourhood, organization, or community for shared benefit or plots.
    *   A School Garden, regardless of whether only students/staff are involved or if the wider community participates. (Classify as 'Community Garden').
    *   Allotment Gardens where land is provided (often communally) for individuals to cultivate their own plots. (Classify as 'Community Garden').
    *   Gardens on public, faith-based, or organizational land clearly intended for communal access or participation in gardening.
    *   Organized neighborhood projects on shared spaces like verges or adopted park sections.
    *   If the exact phrase "community garden" (case-insensitive) appears in the title, description, or transcript referring to the main subject, 
    MUST classify it as 'Community Garden', UNLESS the context strongly and explicitly indicates it is NOT one (e.g., "this is unlike a community garden because...").
    *   Botanical garden is not a community garden unless there is a specific section or project within it that meets the above criteria, or in the transcript, 
    the users show or talk about a community garden within the botanical garden. 
    *   If the text mentions a garden that is not explicitly called a "Community Garden" but meets the criteria above, classify it as 'Community Garden'.
    

2.  Private Garden: Classify as 'Private Garden' if the text primarily describes:
    *   A garden located in a person's private backyard, front yard, balcony, or on private residential property.
    *   Gardening activities focused on personal/family use, even if friends or neighbors occasionally help or visit.
    *   Content focused on an individual's personal gardening journey on their own property.

3.  Unclear: Classify as 'Other/Unclear' if the text describes:
    *   Commercial farms, nurseries, market gardens, hydroponic businesses.
    *   Botanical gardens, arboretums, public parks (unless a specific *section* is clearly identified as a Community Garden meeting rule #1).
    *   Landscaping projects without a focus on growing food/flowers collaboratively.
    *   Indoor houseplant collections not in a garden setting.
    *   Content where a garden is mentioned only peripherally or metaphorically.
    *   If there is not enough information in the text to reliably classify according to rules 1 or 2 AND the specific phrase "community garden" is NOT present referring to the main subject.
    *   General advice: Content primarily focusing on general gardening techniques, soil science, plant care, pest control, etc., that could apply to any type of garden, without specifying the context meets Rule 1 or 2.
    *   If there is not enough specific information in the text to reliably classify according to rules 1 or 2 AND the specific phrase "community garden" is NOT present referring to the main subject. This is the default classification if Rules 1 and 2 are not clearly met.

Task:
Based strictly on the definitions and rules above, analyze the following video text:
1. Classify the garden type ('Community Garden', 'Private Garden', 'Other/Unclear').
2. Extract the specific name of the garden if mentioned clearly in the text. If no specific name is given, or if it's just described (e.g., "my backyard garden"), output 'N/A'.
3. Provide a brief, neutral summary (1-2 sentences) describing the garden and the main activities shown or discussed in the text related to it.
4. Extract the address of the garden if available. If not mentioned, output 'N/A'.
5. If the text provides general gardening advice, soil science information, or discusses plants without clearly describing a garden setting matching the specific criteria in Rule 1 or Rule 2, you MUST classify it as 'Other/Unclear', unless the exact phrase "community garden" (case insensitive) is present referring to the main subject. Do NOT infer the garden type based on general applicability of advice.
Output Format:

You are a strict JSON generator. Return only a valid JSON object and nothing else — no explanations, no comments. The structure should be:
[{{
  "garden_type": string,  // MUST be: "Community Garden" if the video is talking about community garden or "Private Garden" if the video is talking about private garden
  "garden_name": string,  // If the video mentions a specific garden name, use that. If not, use "N/A". If the video is not about a community garden or private garden, use "N/A"
  "summary": string,      // Brief summary justifying the classification (1-2 sentences) and where in the video. If it's not a community garden, or private garden, give a summary of what the video is talking about
  "address": string,      // If the Youtube metadata (title, description, hagtags) or transcript mentions the garden in a place/ location/ area/ city/ region/ suburb, we use that in Address. If no location is mentioned, address = "N/A"
}}]

---
Video Text:
Title: {title}
Description: {description}
Transcript: {transcript}
---

JSON Output:
"""


