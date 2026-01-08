#!/bin/bash

# Define variables
PROJECT_ID="uhgaa-434720"
APP_ID="projects/1073512725854/locations/global/collections/default_collection/engines/optumrx-agentspace-us_1747852782252/assistants/default_assistant/agents/1836601913225368778"

# Execute the curl command using the variables
curl -X GET \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: $PROJECT_ID" \
"https://discoveryengine.googleapis.com/v1alpha/$APP_ID"
