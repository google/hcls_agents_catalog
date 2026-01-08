# RxNorm Agent

This agent is designed to handle RxNorm related tasks using the **Gemini 2.5 Flash** model. It interacts with the [RxNav API](https://rxnav.nlm.nih.gov/) to correct drug name spellings and retrieve detailed clinical drug information.

## Features

-   **Spelling Correction**: Detects and corrects misspelled drug names using the RxNav spelling suggestion API.
-   **Drug Information Retrieval**: Fetches detailed information about drugs, including:
    -   Standardized Name
    -   RxCUI (RxNorm Concept Unique Identifier)
    -   Active Ingredient
    -   Strength
    -   Dose Form

## Prerequisites

-   Python 3.12+
-   `uv` (for dependency management and running the agent)

## Configuration

The agent uses `agentops` for monitoring and observability. You can configure the API key using an environment variable.

1.  Create a `.env` file in the root directory (or use the existing one).
2.  Add your AgentOps API key:

```env
AGENTOPS_API_KEY=your_api_key_here
```

*Note: A default key is provided in the code for demonstration purposes, but it is recommended to use your own.*

## Usage

Run the agent from the root directory using `uv`:

```bash
uv run python rxnorm/agent.py
```

## Tools

The agent is equipped with the following tools:

### `correct_drug_spelling`
-   **Description**: Checks for spelling suggestions for a given drug name.
-   **Input**: `drug_name` (string)
-   **Output**: Original name, suggested name, and a status message.

### `get_drug_information_table`
-   **Description**: Retrieves detailed information for a drug. It automatically checks for spelling corrections before querying for information.
-   **Input**: `drug_name` (string)
-   **Output**: A Markdown table containing drug details (Name, RxCUI, Ingredient, Strength, Dose Form).
