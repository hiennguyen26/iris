import pandas as pd
from pydantic import BaseModel, Field, ConfigDict
from openai import AsyncOpenAI
import instructor
from typing import List, Dict, Any
import os
import asyncio
import json
from dotenv import load_dotenv
import glob
from tqdm.auto import tqdm

load_dotenv()
api_key = os.getenv('open_ai')

instructor_client = instructor.patch(AsyncOpenAI(api_key=api_key))

class StandardRequirement(BaseModel):
    id: str = Field(description="The ID of the standard requirement")
    name: str = Field(description="The name of the standard requirement")
    description: str = Field(description="The description of the standard requirement, including the key principles and why they are important to the process")
