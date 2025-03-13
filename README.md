# tf-code-reviewer-agntcy-agent
Terraform Code Reviewer AI Agent

## Overview

This repository contains a Terraform Code Reviewer AI Agent Protocol FastAPI application. It also includes examples of JSON-based logging, CORS configuration, and route tagging.

## Requirements

- Python 3.12+
- A virtual environment is recommended for isolating dependencies.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/cisco-ai-agents/tf-code-reviewer-agntcy-agent
   cd tf-code-reviewer-agntcy-agent
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Environment Setup

Before using the agent, you need to configure **API keys** for OpenAI or Azure OpenAI.

### **1️⃣ Create a `.env` File**

```sh
touch .env
```

### **2️⃣ Add API Keys**

#### **✅ OpenAI API Configuration**

```
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL_NAME=gpt-4o
OPENAI_TEMPERATURE=0.7
...
```

#### **✅ Azure OpenAI API Configuration**

```
AZURE_OPENAI_API_KEY=your-azure-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2025-01-01-preview
...
```

---

## Running the Application

### Server

You can run the application by executing:

```bash
cd app

python main.py
```

### Expected Console Output

On a successful run, you should see logs in your terminal similar to the snippet below. The exact timestamps, process IDs, and file paths will vary:

```bash
python main.py
{"timestamp": "2025-03-07 13:50:39,724", "level": "INFO", "message": "Logging is initialized. This should appear in the log file.", "module": "logging_config", "function": "configure_logging", "line": 142, "logger": "app", "pid": 53195}
{"timestamp": "2025-03-07 13:50:39,725", "level": "INFO", "message": "Starting FastAPI application...", "module": "main", "function": "main", "line": 203, "logger": "app", "pid": 53195}
{"timestamp": "2025-03-07 13:50:39,725", "level": "INFO", "message": ".env file loaded from /Users/jasvdhil/Documents/Projects/subagents/tf-code-reviewer-agntcy-agent/.env", "module": "main", "function": "load_environment_variables", "line": 43, "logger": "root", "pid": 53195}
INFO:     Started server process [53195]
INFO:     Waiting for application startup.
{"timestamp": "2025-03-07 13:50:39,738", "level": "INFO", "message": "Starting TF Code Reviewer Agent...", "module": "main", "function": "lifespan", "line": 67, "logger": "root", "pid": 53195}
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8123 (Press CTRL+C to quit)
```

This output confirms that:

1. Logging is properly initialized.
2. The server is listening on `0.0.0.0:8123`.
3. Your environment variables (like `.env file loaded`) are read.

### Client

Change to `client` folder

```bash
python rest.py
```

On a successful remote graph run you should see logs in your terminal similar to the snippet below:

```bash
{"timestamp": "2025-03-07 13:52:09,594", "level": "INFO", "message": "{'event': 'final_result', 'result': {'messages': [HumanMessage(content='{\"context_files\": [{\"path\": \"example.py\", \"content\": [\"\\\\n    resource \\\\\"aws_s3_bucket\\\\\" \\\\\"example\\\\\" {\\\\n    bucket = \\\\\"my-public-bucket\\\\\"\\\\n    acl    = \\\\\"public-read\\\\\"\\\\n    }\\\\n    \"]}], \"changes\": [{\"file\": \"example.py\", \"diff\": \"\\\\n    resource \\\\\"aws_security_group\\\\\" \\\\\"example\\\\\" {\\\\n    name        = \\\\\"example-sg\\\\\"\\\\n    description = \\\\\"Security group with open ingress\\\\\"\\\\n    \\\\n    ingress {\\\\n        from_port   = 0\\\\n        to_port     = 0\\\\n        protocol    = \\\\\"-1\\\\\"\\\\n        cidr_blocks = [\\\\\"0.0.0.0/0\\\\\"]\\\\n    }\\\\n    }\\\\n    \"}], \"static_analyzer_output\": \"Security Warning: The security group allows unrestricted ingress (0.0.0.0/0).\"}', additional_kwargs={}, response_metadata={}, id='968ed363-5286-4dbd-abbe-9512181524cd'), AIMessage(content=[{'filename': 'example.py', 'line_number': 2, 'comment': 'The security group allows unrestricted ingress on all ports (0.0.0.0/0), which poses a significant security risk. Consider restricting the ingress rules to specific IP addresses or ranges to enhance security.', 'status': 'added'}], additional_kwargs={}, response_metadata={}, id='a1873bf4-889e-4809-be85-1c73a8fcc3ec')]}}", "module": "rest", "function": "<module>", "line": 242, "logger": "graph_client", "pid": 54199}
```

## Logging

- **Format**: The application is configured to use JSON logging by default. Each log line provides a timestamp, log level, module name, and the message.
- **Location**: Logs typically go to stdout when running locally. If you configure a file handler or direct logs to a centralized logging solution, they can be written to a file (e.g., `logs/app.log`) or shipped to another service.
- **Customization**: You can change the log level (`info`, `debug`, etc.) or format by modifying environment variables or the logger configuration in your code. If you run in Docker or Kubernetes, ensure the logs are captured properly and aggregated where needed.

## API Endpoints

By default, the API documentation is available at:

```bash
http://0.0.0.0:8123/docs
```

(Adjust the host and port if you override them via environment variables.)

## Running as a LangGraph Studio

You need to install Rust: <https://www.rust-lang.org/tools/install>

Run the server

Change to `client` folder

```bash
langgraph dev
```

Paste sample input:

```json
{
   "context_files":[
      {
         "path":"example.tf",
         "content":[
            "\\n    resource \"aws_s3_bucket\" \"example\" {\\n    bucket = \"my-public-bucket\"\\n    acl    = \"public-read\"\\n    }\\n    "
         ]
      }
   ],
   "changes":[
      {
         "file":"example.tf",
         "diff":"\\n    resource \"aws_security_group\" \"example\" {\\n    name        = \"example-sg\"\\n    description = \"Security group with open ingress\"\\n\\n    ingress {\\n        from_port   = 0\\n        to_port     = 0\\n        protocol    = \"-1\"\\n        cidr_blocks = [\"0.0.0.0/0\"]\\n    }\\n    }\\n    "
      }
   ],
   "static_analyzer_output":"Security Warning: The security group allows unrestricted ingress (0.0.0.0/0)."
}

```

Expected Output:

![Langgraph Studio](./docs/imgs/studio.png "Studio")

## Roadmap

See the [open issues](https://github.com/cisco-ai-agents/tf-code-reviewer-agntcy-agent/issues) for a list
of proposed features (and known issues).

## Contributing

Contributions are what make the open source community such an amazing place to
learn, inspire, and create. Any contributions you make are **greatly
appreciated**. For detailed contributing guidelines, please see
[CONTRIBUTING.md](CONTRIBUTING.md)

## License

Distributed under the `Apache-2.0` License. See [LICENSE](LICENSE) for more
information.

## Contact

Jasvir Dhillon - [@jsd784](https://github.com/jsd784) - jasvdhil@cisco.com

Project Link:
[https://github.com/cisco-ai-agents/tf-code-reviewer-agntcy-agent](https://github.com/cisco-ai-agents/tf-code-reviewer-agntcy-agent)

## Acknowledgements

This template was adapted from
[https://github.com/othneildrew/Best-README-Template](https://github.com/othneildrew/Best-README-Template).
