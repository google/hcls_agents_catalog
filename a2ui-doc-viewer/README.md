# A2UI Document Viewer Agent

A shippable, production-ready ReAct agent built on the [A2A Protocol](https://a2a-protocol.org/) to securely retrieve and render Google Cloud Storage (GCS) PDF documents inside Gemini Enterprise or local tester iframe environments.

---

## 🛠️ Configuration & Setup

To deploy this agent in your own Google Cloud environment, you only need to configure your Project ID.

### 1. Set Google Cloud Project ID
Open [deployment/terraform/single-project/vars/env.tfvars](file:///usr/local/google/home/hmp/src/a2ui-doc-viewer/deployment/terraform/single-project/vars/env.tfvars) and replace the default value with your own project ID:
```hcl
# Your Google Cloud project id
project_id = "your-gcp-project-id"
```

### 2. Configure GCP CLI
Authenticate and set your active project in the terminal:
```bash
gcloud auth login
gcloud config set project your-gcp-project-id
```

---

## 🚀 How to Run & Deploy

### Local Development (Tester Panel)
You can run a local mock server and web UI to interact with and test the agent:
```bash
# Start the local server
uv run python local_tester/server.py
```
Open your browser to `http://localhost:8000`. You can ask the agent:
> *"show me gs://hcls-ge-documents/roi_2025_health.pdf"*

### Deployment to GCP Cloud Run
Deploy the agent and configure it automatically using the `agents-cli`:
```bash
agents-cli deploy --project your-gcp-project-id
```

---

## 🧠 Architecture & How it Works

The A2UI Document Viewer Agent integrates the Gemini Large Language Model, Google Cloud Storage, and client-side iframe sandboxing.

```mermaid
sequenceDiagram
    autonumber
    User->>Gemini Enterprise: "show me gs://bucket/file.pdf"
    Gemini Enterprise->>Agent (Cloud Run): POST /jsonrpc (User prompt)
    Note over Agent (Cloud Run): Resolves GCS URI and constructs absolute proxy URL:<br/>https://[SERVICE_URL]/pdf?url=gs://bucket/file.pdf
    Agent (Cloud Run)-->>Gemini Enterprise: Return WebFrameSrcdoc redirecting to proxy URL
    Gemini Enterprise->>Iframe (Chrome Sandbox): Render iframe & execute redirect
    Iframe (Chrome Sandbox)->>Agent (Cloud Run): GET /pdf?url=gs://bucket/file.pdf
    Agent (Cloud Run)->>GCS Bucket: Download PDF bytes
    GCS Bucket-->>Agent (Cloud Run): PDF binary data
    Note over Agent (Cloud Run): 1. Base64-encodes PDF bytes<br/>2. Embeds into self-contained HTML page with PDF.js<br/>3. Returns text/html Response
    Agent (Cloud Run)-->>Iframe (Chrome Sandbox): Return HTML page (PDF.js + PDF base64 payload)
    Note over Iframe (Chrome Sandbox): PDF.js decodes base64 payload and renders<br/>pages directly on HTML5 Canvas.
```

### 1. The ReAct Agent Loop
- The agent is defined in [app/agent.py](file:///usr/local/google/home/hmp/src/a2ui-doc-viewer/app/agent.py).
- When a user asks to view a GCS document, the agent parses the prompt, extracts the GCS URI (e.g. `gs://bucket-name/path/to/document.pdf`), and constructs an absolute proxy URL pointing to `/pdf?url=gs://...` on its own service host.
- The agent outputs a `WebFrameUrl` component, which the ADK framework automatically converts into a `WebFrameSrcdoc` containing a script redirecting to the proxy endpoint.

### 2. Bypassing Chrome's Iframe Sandbox Plugin Blockage
- In Gemini Enterprise, extensions and interactive panels are loaded inside a **sandboxed iframe** with strict security properties.
- Chrome's sandboxing blocks standard PDF plugins (like the Adobe Reader or Chrome native PDF viewer) from initializing inside sandboxed contexts. Attempting to load a raw PDF file (`application/pdf`) directly inside the iframe results in the browser blocking the request with `"This page has been blocked by Chrome"`.
- To bypass this limitation, the agent's `/pdf` endpoint (in [app/fast_api_app.py](file:///usr/local/google/home/hmp/src/a2ui-doc-viewer/app/fast_api_app.py) and [local_tester/server.py](file:///usr/local/google/home/hmp/src/a2ui-doc-viewer/local_tester/server.py)):
  1. Base64-encodes the GCS PDF document bytes.
  2. Embeds the base64 string directly into a self-contained HTML page that loads **PDF.js** via CDN.
  3. Returns `text/html` instead of `application/pdf`.
- Because standard HTML and scripts are fully allowed inside the sandbox (`allow-scripts`), the browser renders the HTML page, and PDF.js decodes the embedded base64 data to draw the PDF pages directly on an HTML5 `<canvas>` element.

### 3. Local Environment SSL Conflict Fallback
- In certain local development environments, concurrent calls to the Gemini LLM (via gRPC/HTTPS) and GCS SDK (via HTTPS) can cause `pyOpenSSL` certificate context collisions (`Context has already been used to create a Connection`).
- The local server [local_tester/server.py](file:///usr/local/google/home/hmp/src/a2ui-doc-viewer/local_tester/server.py) has a built-in safety fallback: if the GCS SDK client fails due to an SSL mutation conflict, it falls back to calling the system's `gcloud storage cat` command in a separate process space, ensuring reliable local testing.

---

## 📂 Project Structure

```
a2ui-doc-viewer/
├── app/
│   ├── agent.py               # Main agent definition & instructions
│   ├── fast_api_app.py        # Cloud Run FastAPI server & /pdf endpoint
│   └── app_utils/             # Telemetry & helper modules
├── local_tester/
│   ├── server.py              # Local FastAPI runner with fallback CLI execution
│   └── index.html             # Local mock UI rendering client-side A2UI components
├── deployment/
│   └── terraform/             # Terraform infrastructure config
├── tests/                     # Unit & integration tests
├── pyproject.toml             # Project dependency definitions
└── agents-cli-manifest.yaml   # Manifest for cloud deployments
```

---

## 🛠️ Development & Commands

| Command | Description |
|---|---|
| `agents-cli install` | Install dependencies using `uv` |
| `agents-cli playground` | Launch interactive development prompt loop |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests |
| `agents-cli deploy` | Deploy the agent service to Cloud Run |
