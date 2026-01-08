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
