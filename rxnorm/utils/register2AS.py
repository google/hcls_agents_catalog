# Copyright 2026 Google LLC
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

import vertexai
from vertexai.preview import reasoning_engines

PROJECT_ID = "agentspace-demo-1145-b"
LOCATION = "us-central1"
vertexai.init(
      project=PROJECT_ID,
      location=LOCATION,
      # api_endpoint="us-central1-aiplatform.googleapis.com",
  )
engines = reasoning_engines.ReasoningEngine.list(filter='display_name="Corporate Analyst"')

if not engines:
    print("Reasoning engine for Corporate Analyst missing")
    exit

print ("Reasoning engine: " + engines[0].resource_name)

engine = reasoning_engines.ReasoningEngine(engines[0].resource_name)

#session = engine.create_session(session_id="session1")

sessions_data = engine.list_sessions()
print (sessions_data)


# Check if the response is a string and if so, attempt to parse as JSON
if isinstance(sessions_data, str):
  try:
    sessions_data = json.loads(sessions_data)
  except json.JSONDecodeError as e:
      print(f"Error decoding JSON: {e}")
      print(f"Received string: {sessions_data}")
      #Handle the error case. maybe return or exit
      exit()


# Now check if it's a dictionary with a 'session_ids' key
if isinstance(sessions_data, dict) and 'session_ids' in sessions_data:
    session_ids = sessions_data['session_ids']
    if not session_ids:  # Check if the list is empty
        print("Creating new session")
        session = engine.create_session(session_id="session1")
    else:
        print(f"Existing sessions found: {session_ids}")
else:
    print(
        "Unexpected format for session data. Expected a dictionary with a 'session_ids' key."
    )
    print(f"Received: {sessions_data}")
    # Handle the error case. maybe return or exit
    exit()

session = engine.get_session(session_id="session1")

from google.genai import types
output = engine.agent_run(
    session_id="session1",
    message=types.Content(
        parts=[types.Part(text="AAPL")],
        role="user",
    ).model_dump_json(),
)

print(output)
