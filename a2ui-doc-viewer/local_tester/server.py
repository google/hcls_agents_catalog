# local_tester/server.py
import os
import sys
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import logging
from dotenv import load_dotenv
from google.cloud import storage

# Path setup to import the agent
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
load_dotenv(os.path.join(parent_dir, '.env'))

import app.agent as agent
from google.adk import runners
from google.adk.sessions import in_memory_session_service
from google.adk.artifacts import in_memory_artifact_service
from google.adk.memory import in_memory_memory_service
from google.genai import types as genai_types

app_fastapi = FastAPI()

app_fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

adk_agent = agent.root_agent
runner = runners.Runner(
    app_name="app",
    agent=adk_agent,
    session_service=in_memory_session_service.InMemorySessionService(),
    artifact_service=in_memory_artifact_service.InMemoryArtifactService(),
    memory_service=in_memory_memory_service.InMemoryMemoryService(),
)

# Set the environment variable AGENT_URL if not set, so agent constructs URLs pointing to this tester
if not os.environ.get("AGENT_URL"):
    os.environ["AGENT_URL"] = "http://localhost:8000"

storage_client = storage.Client()

@app_fastapi.get("/.well-known/agent-card.json")
async def get_agent_card():
    return {
        "capabilities": {
            "streaming": False,
            "extensions": [{"uri": "https://a2ui.org/a2a-extension/a2ui/v0.8", "required": False}]
        },
        "name": adk_agent.name,
        "url": "/jsonrpc",
        "version": "1.0.0"
    }

@app_fastapi.get("/")
async def get_index():
    return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"))

@app_fastapi.get("/pdf")
async def get_pdf(url: str):
    # Proxy PDF endpoint for local tester
    if not url.startswith("gs://"):
        return Response("Invalid URL. Must start with gs://", status_code=400)
    
    try:
        path_without_scheme = url[5:]
        bucket_name, object_name = path_without_scheme.split("/", 1)
    except ValueError:
        return Response("Invalid GCS URI format", status_code=400)
        
    try:
        try:
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            content = blob.download_as_bytes()
        except Exception as e:
            if "Context has already been used to create a Connection" in str(e) or "cannot be mutated again" in str(e):
                logger.info("SSL context mutation error detected. Falling back to gcloud storage CLI...")
                import subprocess
                result = subprocess.run(
                    ["gcloud", "storage", "cat", url],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                content = result.stdout
            else:
                raise e

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
        logger.exception("Failed to fetch document from GCS")
        return Response(f"Error fetching document: {str(e)}", status_code=500)

@app_fastapi.get("/docx")
async def get_docx(url: str):
    # Proxy docx endpoint for local tester
    if not url.startswith("gs://"):
        return Response("Invalid URL. Must start with gs://", status_code=400)
    
    try:
        path_without_scheme = url[5:]
        bucket_name, object_name = path_without_scheme.split("/", 1)
    except ValueError:
        return Response("Invalid GCS URI format", status_code=400)
        
    try:
        try:
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            content = blob.download_as_bytes()
        except Exception as e:
            if "Context has already been used to create a Connection" in str(e) or "cannot be mutated again" in str(e):
                logger.info("SSL context mutation error detected. Falling back to gcloud storage CLI...")
                import subprocess
                result = subprocess.run(
                    ["gcloud", "storage", "cat", url],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                content = result.stdout
            else:
                raise e

        import base64
        docx_base64 = base64.b64encode(content).decode("utf-8")
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <title>Word Document Viewer</title>
          <script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>
          <script src="https://cdn.jsdelivr.net/npm/docx-preview@latest/dist/docx-preview.min.js"></script>
          <style>
            body {{ margin: 0; background-color: #f4f4f9; display: flex; flex-direction: column; align-items: center; font-family: sans-serif; }}
            #docx-container {{ width: 100%; display: flex; flex-direction: column; align-items: center; gap: 15px; padding: 20px 0; }}
            .docx-wrapper {{ box-shadow: 0 4px 8px rgba(0,0,0,0.15); max-width: 95%; border-radius: 4px; background: white; padding: 20px; }}
            #loading {{ margin-top: 50px; font-size: 18px; color: #666; }}
          </style>
        </head>
        <body>
          <div id="loading">Loading document...</div>
          <div id="docx-container"></div>
          <script>
            const docxData = "{docx_base64}";
            try {{
              const rawData = atob(docxData);
              const uint8Array = new Uint8Array(rawData.length);
              for (let i = 0; i < rawData.length; i++) {{
                uint8Array[i] = rawData.charCodeAt(i);
              }}
              
              const blob = new Blob([uint8Array], {{ type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" }});
              const container = document.getElementById('docx-container');
              
              docx.renderAsync(blob, container).then(() => {{
                document.getElementById('loading').remove();
              }}).catch(err => {{
                document.getElementById('loading').innerText = "Error rendering document: " + err.message;
              }});
            }} catch(err) {{
              document.getElementById('loading').innerText = "Error decoding document data: " + err.message;
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
        logger.exception("Failed to fetch document from GCS")
        return Response(f"Error fetching document: {str(e)}", status_code=500)


@app_fastapi.post("/jsonrpc")
async def handle_jsonrpc(request: Request):
    body = await request.json()
    if body.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": body.get("id")}
        
    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")
    
    if method == "message/send":
        message = params.get("message", {})
        query = message.get("text", "")
        session_id = params.get("session_id", "local_session")
        
        session = await runner.session_service.get_session(
            app_name="app", user_id="local_user", session_id=session_id,
        )
        if not session:
            session = await runner.session_service.create_session(
                app_name="app", user_id="local_user", state={}, session_id=session_id,
            )
            
        content = genai_types.Content(role="user", parts=[{"text": query}])
        parts = []
        text_responses = []
        A2UI_ACTIONS = {"beginRendering", "surfaceUpdate", "dataModelUpdate", "deleteSurface"}
        
        async for event in runner.run_async(
            user_id="local_user", session_id=session.id, new_message=content
        ):
            # Intercept tool responses in any event
            if event.content and event.content.parts:
                for part in event.content.parts:
                    func_resp = getattr(part, "function_response", None)
                    if func_resp and func_resp.name in A2UI_ACTIONS:
                        parts.append({
                            "data": func_resp.response,
                            "metadata": {"mimeType": "application/json+a2ui"}
                        })
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            text_responses.append(part.text)

        if text_responses:
            combined_text = "\n".join(text_responses).strip()
            if combined_text:
                parts.insert(0, {"text": combined_text})
                
        if not parts:
            resp = {"jsonrpc": "2.0", "result": {"message": {"text": "No response from agent"}}, "id": request_id}
            logger.info(f"Returning empty response: {resp}")
            return resp
            
        resp = {
            "jsonrpc": "2.0",
            "result": {
                "message": {
                    "parts": parts
                }
            },
            "id": request_id
        }
        logger.info(f"Returning successful response: {resp}")
        return resp
        
    return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": request_id}

if __name__ == "__main__":
    uvicorn.run(app_fastapi, host="0.0.0.0", port=8000)
