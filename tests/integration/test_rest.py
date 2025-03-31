import json
from client.rest import build_graph
from langchain_core.messages import HumanMessage

def test_rest_integration():
    CONTEXT_FILES = [
        {
            "path": "example.tf",
            "content": """
            resource "aws_s3_bucket" "example" {
              bucket = "my-public-bucket"
              acl    = "public-read"
            }
            """
        }
    ]

    CHANGES = [
        {
            "file": "example.tf",
            "content": """
            resource "aws_security_group" "example" {
              name        = "example-sg"
              description = "Security group with open ingress"

              ingress {
                  from_port   = 0
                  to_port     = 0
                  protocol    = "-1"
                  cidr_blocks = ["0.0.0.0/0"]
              }
            }
            """
        }
    ]

    ANALYSIS_REPORTS = (
        "Security Warning: The security group allows unrestricted ingress (0.0.0.0/0)."
    )

    tf_input = {
        "context_files": CONTEXT_FILES,
        "changes": CHANGES,
        "static_analyzer_output": ANALYSIS_REPORTS
    }

    graph = build_graph()
    inputs = {"messages": [HumanMessage(content=json.dumps(tf_input))]}
    result = graph.invoke(inputs)

    assert "messages" in result
    assert result["messages"]
    print("REST Output:", result["messages"][-1].content)