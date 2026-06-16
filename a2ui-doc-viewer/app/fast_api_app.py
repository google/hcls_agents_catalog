# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

# Monkeypatch to avoid ValueError: part_metadata parameter is only supported in Gemini Developer API mode
# in google-genai when running under Vertex AI mode.
try:
    import google.adk.a2a.converters.part_converter as pc
    original_convert = pc.convert_a2a_part_to_genai_part
    def patched_convert(a2a_part):
        genai_part = original_convert(a2a_part)
        if genai_part is not None:
            genai_part.part_metadata = None
        return genai_part
    pc.convert_a2a_part_to_genai_part = patched_convert
except Exception:
    pass

import google.auth
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentExtension, Part, DataPart
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    EXTENDED_AGENT_CARD_PATH,
)
from fastapi import FastAPI, Query, Response
from fastapi.responses import HTMLResponse
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor, A2aAgentExecutorConfig
from google.adk.a2a.converters.part_converter import convert_genai_part_to_a2a_part
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.cloud import logging as google_cloud_logging
from google.cloud import storage

from app.agent import app as adk_app
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

setup_telemetry()
_, project_id = google.auth.default()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)

# Artifact bucket for ADK (created by Terraform, passed via env var)
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
artifact_service = (
    GcsArtifactService(bucket_name=logs_bucket_name)
    if logs_bucket_name
    else InMemoryArtifactService()
)

runner = Runner(
    app=adk_app,
    artifact_service=artifact_service,
    session_service=InMemorySessionService(),
)

from typing import Optional, Union, List

def custom_gen_ai_part_converter(part) -> Optional[Union[Part, List[Part]]]:
    # Check if the part is a function response for our A2UI tools
    func_resp = getattr(part, "function_response", None)
    if func_resp and func_resp.name in {
        "beginRendering",
        "surfaceUpdate",
        "dataModelUpdate",
        "deleteSurface",
    }:
        response_dict = func_resp.response
        if response_dict and isinstance(response_dict, dict):
            # Wrap in A2A Part/DataPart with A2UI mimeType
            return Part(
                root=DataPart(
                    data=response_dict,
                    metadata={"mimeType": "application/json+a2ui"},
                )
            )

    return convert_genai_part_to_a2a_part(part)

request_handler = DefaultRequestHandler(
    agent_executor=A2aAgentExecutor(
        runner=runner,
        config=A2aAgentExecutorConfig(
            gen_ai_part_converter=custom_gen_ai_part_converter
        )
    ),
    task_store=InMemoryTaskStore(),
)

A2A_RPC_PATH = f"/a2a/{adk_app.name}"


async def build_dynamic_agent_card() -> AgentCard:
    """Builds the Agent Card dynamically from the root_agent."""
    agent_card_builder = AgentCardBuilder(
        agent=adk_app.root_agent,
        capabilities=AgentCapabilities(
            streaming=True,
            extensions=[
                AgentExtension(
                    uri="https://google.github.io/adk-docs/a2a/a2a-extension/",
                    description="Ability to use the new agent executor implementation",
                ),
                AgentExtension(
                    uri="https://a2ui.org/a2a-extension/a2ui/v0.8",
                    description="Ability to render A2UI",
                    required=True,
                    params={
                        "supportedCatalogIds": [
                            "https://a2ui.org/specification/v0_8/standard_catalog_definition.json",
                            "https://vertexaisearch.cloud.google.com/a2ui/v0_8/gemini_enterprise_custom_catalog.json"
                        ],
                        "acceptsInlineCatalogs": True
                    }
                )
            ],
        ),
        rpc_url=f"{os.getenv('APP_URL', 'http://0.0.0.0:8000')}{A2A_RPC_PATH}",
        agent_version=os.getenv("AGENT_VERSION", "0.1.0"),
    )
    agent_card = await agent_card_builder.build()
    agent_card.name = "Document Viewer Agent"
    
    # Register A2UI mimeTypes
    if "application/json+a2ui" not in agent_card.default_output_modes:
        agent_card.default_output_modes.append("application/json+a2ui")
    if "application/json" not in agent_card.default_input_modes:
        agent_card.default_input_modes.append("application/json")
        
    return agent_card


@asynccontextmanager
async def lifespan(app_instance: FastAPI) -> AsyncIterator[None]:
    agent_card = await build_dynamic_agent_card()
    a2a_app = A2AFastAPIApplication(agent_card=agent_card, http_handler=request_handler)
    a2a_app.add_routes_to_app(
        app_instance,
        agent_card_url=f"{A2A_RPC_PATH}{AGENT_CARD_WELL_KNOWN_PATH}",
        rpc_url=A2A_RPC_PATH,
        extended_agent_card_url=f"{A2A_RPC_PATH}{EXTENDED_AGENT_CARD_PATH}",
    )
    yield


app = FastAPI(
    title="a2ui-doc-viewer",
    description="API for interacting with the Agent a2ui-doc-viewer",
    lifespan=lifespan,
)

@app.get("/pdf")
async def get_pdf(url: str = Query(..., description="GCS URI of the PDF file (e.g., gs://bucket/path/file.pdf)")):
    if not url.startswith("gs://"):
        return Response("Invalid URL. Must start with gs://", status_code=400)
    
    try:
        path_without_scheme = url[5:]
        bucket_name, object_name = path_without_scheme.split("/", 1)
    except ValueError:
        return Response("Invalid GCS URI format", status_code=400)
        
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        content = blob.download_as_bytes()
        
        import base64
        pdf_base64 = base64.b64encode(content).decode("utf-8")
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <title>PDF Viewer</title>
          <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js"></script>
          <style>
            body {{ margin: 0; background-color: #f4f4f9; display: flex; flex-direction: column; align-items: center; font-family: sans-serif; }}
            #pdf-container {{ width: 100%; display: flex; flex-direction: column; align-items: center; gap: 15px; padding: 20px 0; }}
            canvas {{ box-shadow: 0 4px 8px rgba(0,0,0,0.15); max-width: 95%; border-radius: 4px; }}
            #loading {{ margin-top: 50px; font-size: 18px; color: #666; }}
          </style>
        </head>
        <body>
          <div id="loading">Loading document...</div>
          <div id="pdf-container"></div>
          <script>
            const pdfData = "{pdf_base64}";
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';

            try {{
              const rawData = atob(pdfData);
              const uint8Array = new Uint8Array(rawData.length);
              for (let i = 0; i < rawData.length; i++) {{
                uint8Array[i] = rawData.charCodeAt(i);
              }}
              
              pdfjsLib.getDocument({{ data: uint8Array }}).promise.then(pdf => {{
                document.getElementById('loading').remove();
                const container = document.getElementById('pdf-container');
                for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {{
                  pdf.getPage(pageNum).then(page => {{
                    const viewport = page.getViewport({{ scale: 1.5 }});
                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;
                    container.appendChild(canvas);

                    page.render({{ canvasContext: context, viewport: viewport }});
                  }});
                }}
              }}).catch(err => {{
                document.getElementById('loading').innerText = "Error loading PDF: " + err.message;
              }});
            }} catch(err) {{
              document.getElementById('loading').innerText = "Error decoding PDF data: " + err.message;
            }}
          </script>
        </body>
        </html>
        """
        return HTMLResponse(
            content=html_template,
            headers={
                "X-Frame-Options": "ALLOWALL",
            }
        )
    except Exception as e:
        return Response(f"Error fetching document: {str(e)}", status_code=500)


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
