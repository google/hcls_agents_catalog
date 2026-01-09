# Copyright 2026 Healthcare Lifesciences Team, Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import Agent
import agentops
from .callRxnorm import get_spelling_suggestion, get_drug_info
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional, Union

# Load environment variables from .env file
load_dotenv()

AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")
if AGENTOPS_API_KEY:
    agentops.init(
        api_key=AGENTOPS_API_KEY,
        default_tags=['google adk']
    )

def correct_drug_spelling(drug_name: str) -> Dict[str, str]:
    """
    Checks the spelling of a drug name and provides a suggestion if misspelled.

    Args:
        drug_name: The drug name to check.

    Returns:
        A dictionary containing the original name, suggested name, and a status message.
    """
    suggestion = get_spelling_suggestion(drug_name)
    if not suggestion:
        return {
            "original_name": drug_name,
            "suggested_name": drug_name,
            "message": f"No spelling suggestion found for '{drug_name}'."
        }
    
    if suggestion.lower() == drug_name.lower():
        return {
            "original_name": drug_name,
            "suggested_name": drug_name,
            "message": f"Spelling for '{drug_name}' appears to be correct."
        }
    
    return {
        "original_name": drug_name,
        "suggested_name": suggestion,
        "message": f"Spelling suggestion for '{drug_name}': {suggestion}"
    }

def get_drug_details(drug_name: str) -> Dict[str, Union[str, List[Dict[str, str]]]]:
    """
    Retrieves detailed information for a drug, including spelling correction.

    Args:
        drug_name: The drug name to search for.

    Returns:
        A dictionary containing the status, queried name, and a list of drug details.
    """
    spelling_result = correct_drug_spelling(drug_name)
    drug_name_to_use = spelling_result["suggested_name"]
    
    drug_info_list = get_drug_info(drug_name_to_use)

    if not drug_info_list:
        return {
            "status": "no_info_found",
            "queried_name": drug_name_to_use,
            "message": f"No information found for '{drug_name_to_use}'.",
            "drug_details": []
        }

    return {
        "status": "success",
        "queried_name": drug_name_to_use,
        "message": f"Successfully retrieved information for '{drug_name_to_use}'.",
        "drug_details": drug_info_list
    }

root_agent = Agent(
    name="rxnorm_drug_assistant",
    model="gemini-1.5-flash",
    description="An agent that can correct drug name spellings and provide detailed drug information from RxNav.",
    instruction="""
You are a helpful assistant specializing in drug information from RxNav API.

Tools:
1. `correct_drug_spelling`: Use this if the user specifically asks to check or correct the spelling of a drug name.
2. `get_drug_details`: Use this if the user asks for information about a drug (e.g., "Tell me about Lipitor", "What is Amoxicillin?"). This tool automatically handles spelling correction.

Guidelines:
- When using `get_drug_details`, present the `drug_details` as a Markdown table with columns: Standardized Name, RxCUI, Active Ingredient, Strength, Dose Form.
- Always inform the user if a spelling correction was made.
- If no information is found, politely inform the user.
- If the user asks something unrelated to drugs, state that you can only assist with drug-related queries.
    """,
    tools=[correct_drug_spelling, get_drug_details]
)
