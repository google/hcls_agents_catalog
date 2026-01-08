# RxNorm Drug Information Agent

This project provides a conversational agent that interfaces with the National Institutes of Health (NIH) RxNorm API https://lhncbc.nlm.nih.gov/RxNav/APIs/index.html. It can correct the spelling of drug names and retrieve detailed information about them, such as their standardized name, active ingredients, strength, and dose form.

The agent is built using the Google Agent Development Kit (ADK) and is deployed as a Vertex AI Agent Engine.

## Project Structure
The packaging was created following direction form the foundation lab https://codelabs.developers.google.com/devsite/codelabs/build-agents-with-adk-foundation

```
.
├── agent_engine_app.py       # Main application to deploy the agent to Vertex AI.
├── pyproject.toml            # Project metadata and dependencies.
├── README.md                 # This file.
├── rxnorm_agent/
│   ├── __init__.py
│   ├── agent.py              # Core agent logic, including tool definitions and instructions.
│   └── callRxnorm.py         # Functions to call the external RxNorm API.
└── ...
```

- **`agent_engine_app.py`**: This script handles the initialization and deployment of the agent to Google Cloud's Vertex AI Agent Engine service. It reads configuration from environment variables.
- **`pyproject.toml`**: Defines the project, its dependencies (`google-adk`), and that it requires Python 3.12+.
- **`rxnorm_agent/agent.py`**: This is the heart of the agent. It defines two primary tools:
    1.  `correct_drug_spelling`: Corrects a given drug name.
    2.  `get_drug_information_table`: Fetches detailed information for a drug and formats it into a markdown table.
- **`rxnorm_agent/callRxnorm.py`**: Contains the logic for making HTTP requests to the public RxNav API to get spelling suggestions and drug data.

## Prerequisites

- Python 3.12 or higher
- `uv` package manager (or `pip`)
- Google Cloud SDK authenticated to a project.

## Setup and Installation

1.  **Clone the repository** (if you haven't already).

2.  **Create a virtual environment**:
    It is highly recommended to use a virtual environment to manage dependencies.

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    This project uses `uv` for dependency management. If you have `uv` installed, you can sync the environment from the `uv.lock` file.

    ```bash
    uv sync
    ```
    Alternatively, you can use `pip` with the `pyproject.toml` file:
    ```bash
    pip install .
    ```

## Configuration

The application requires Google Cloud credentials and configuration to be set in the environment.

1.  **Create a `.env` file** in the root of the project.
2.  **Add the following environment variables** to the `.env` file, replacing the placeholder values with your actual Google Cloud project details:

    ```env
    GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
    GOOGLE_CLOUD_LOCATION="your-gcp-region" # e.g., us-central1
    ```

3.  The deployment script in `agent_engine_app.py` will automatically create a Google Cloud Storage bucket named `gs://<your-gcp-project-id>-agent-engine-deploy` for staging. Ensure your authenticated user has permissions to create and write to this bucket.

## Running the Application

This application is designed to be deployed as a Vertex AI Agent Engine, not run as a standalone local server.

To deploy the agent, run the `agent_engine_app.py` script:

```bash
python agent_engine_app.py
```

This script will:
1.  Initialize a connection to your Google Cloud project.
2.  Define the agent using the tools and instructions from `rxnorm_agent/agent.py`.
3.  Check if an agent with the display name "RxNorm Drug Information Agent" (or as configured in the script) already exists.
4.  If it exists, it updates the agent; otherwise, it creates a new one.

After deployment, the agent can be invoked through the Vertex AI API or used in other Google Cloud services that integrate with Agent Engines.
