## Overview
To create a manifest json for the code-reviewer agent that describes all the ACP specs of an agent, including schemas and protocol features.

## Requirements
- Python 3.12+
- A virtual environment is recommended for isolating dependencies.

## Installation
1. Clone the repository:

   ```bash
   git clone https://github.com/cisco-outshift-ai-agents/tf-code-reviewer-agntcy-agent
   cd tf-code-reviewer-agntcy-agent/manifest
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements-manifest.txt
   ```

## Running the Application

```bash
python generate_manifest.py
```

This will create a code_reviewer_manifest.json for the code-reviewer agent.