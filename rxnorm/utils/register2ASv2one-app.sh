#!/bin/bash

# Define variables for your agent configuration
# DISPLAY_NAME is the public-facing "advertisement" for your agent that users will see.
DISPLAY_NAME="RxNorm drug query 2"

# PROJECT_ID is the numeric ID of your Google Cloud project.
PROJECT_ID="1073512725854"

# APP_ID refers to the specific application ID within your project's Discovery Engine.
APP_ID="optumrx-agentspace-us_1747852782252"

# DESCRIPTION provides a brief overview of what your agent does for users.
DESCRIPTION="Answers prescription drug questions"

# TOOL_DESCRIPTION is the internal "instruction manual" for the AI, determining when your agent gets called.
TOOL_DESCRIPTION="The user can type in any drug name. The name might be misspelled. This agent can correct the drug name spelling and return the drug information."

# ADK_DEPLOYMENT_ID links to the deployed reasoning engine for your agent.
ADK_DEPLOYMENT_ID="2064574973707550720"

# Construct the JSON payload using a 'here document' for better readability
# and proper JSON formatting. Variables are expanded directly within the JSON.
JSON_PAYLOAD=$(cat <<EOF
{
  "displayName": "${DISPLAY_NAME}",
  "description": "${DESCRIPTION}",
  "adk_agent_definition": {
    "tool_settings": {
      "tool_description": "${TOOL_DESCRIPTION}"
    },
    "provisioned_reasoning_engine": {
      "reasoning_engine": "projects/${PROJECT_ID}/locations/us-central1/reasoningEngines/${ADK_DEPLOYMENT_ID}"
    }
  }
}
EOF
)

# Execute the curl command to create/update the agent.
# Using double quotes around variable expansions like "${PROJECT_ID}" is a good practice
# to prevent issues with spaces or special characters, even if not strictly necessary for IDs.
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/${APP_ID}/assistants/default_assistant/agents" \
  -d "${JSON_PAYLOAD}"
