from abc import abstractmethod
import json

import openai
from pydantic import BaseModel
from YT_keywords import community_garden_keywords, region_keywords
from YT_prompts import Community_garden_definition_rule

class CommunityGarden(BaseModel):
    garden_type: str
    garden_name: str
    address: str
    summary: str

class AiClient:
    @abstractmethod
    def analyse(self, prompt):
        pass        

class OpenAiClient(AiClient):
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("OpenAI API key is required")
        openai.api_key = api_key

    def analyse(self, prompt) -> (CommunityGarden | None):
        response = openai.responses.parse(
            model="gpt-4.1-nano",
            input=prompt,
            text_format=CommunityGarden,
        )
        return response.output_parsed

class CommunityGardenAnalyzer:
    def __init__(self, ai_client):
        if ai_client is None:
            raise ValueError("AiClient instance is required")
        self.ai_client = ai_client

    def is_community_garden(self, title, description, transcript):
        text = f"{title} {description} {transcript}".lower()
        return any(k in text for k in community_garden_keywords) and any(r in text for r in region_keywords)
    
    def analyze(self, title, description, transcript) -> (CommunityGarden | None):
        if not self.is_community_garden(title, description, transcript):
            return None
        prompt = Community_garden_definition_rule.format(
            title=title,
            description=description,
            transcript=transcript
        )
        return self.ai_client.analyse(prompt)