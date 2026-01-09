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

import vertexai
import os
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp
from dotenv import load_dotenv
from rxnorm_agent.agent import root_agent


def deploy_agent_engine_app():
    load_dotenv()

    GOOGLE_CLOUD_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
    GOOGLE_CLOUD_LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]
    STAGING_BUCKET = f"gs://{GOOGLE_CLOUD_PROJECT}-agent-engine-deploy"
    AGENT_DISPLAY_NAME = "RxNorm Drug Information Agent"

    vertexai.init(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        staging_bucket=STAGING_BUCKET,
    )

    app = AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    agent_config = {
        "agent_engine": app,
        "display_name": AGENT_DISPLAY_NAME,
        "requirements": [
            "google-cloud-aiplatform[agent_engines,adk]",
            "requests",
        ],
        "extra_packages": [
            "rxnorm_agent",
        ],
    }

    existing_agents = list(
        agent_engines.list(filter=f'display_name="{AGENT_DISPLAY_NAME}"')
    )

    if existing_agents:
        print(f"Found existing agent for {AGENT_DISPLAY_NAME}. Updating it.")

    if existing_agents:
        # update the existing agent
        remote_app = existing_agents[0].update(**agent_config)
    else:
        # create a new agent
        remote_app = agent_engines.create(**agent_config)

    return None


if __name__ == "__main__":
    deploy_agent_engine_app()
