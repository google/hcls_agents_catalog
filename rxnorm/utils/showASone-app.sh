#!/bin/bash

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


# Define variables
PROJECT_ID="uhgaa-434720"
APP_ID="projects/1073512725854/locations/global/collections/default_collection/engines/optumrx-agentspace-us_1747852782252/assistants/default_assistant/agents/1836601913225368778"

# Execute the curl command using the variables
curl -X GET \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: $PROJECT_ID" \
"https://discoveryengine.googleapis.com/v1alpha/$APP_ID"
