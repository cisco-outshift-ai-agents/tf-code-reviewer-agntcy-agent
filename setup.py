from setuptools import setup, find_packages

setup(
    name="tf-code-reviewer-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Core project dependencies
        "agp-api==0.0.5",

        # LangGraph / LangChain stack
        "langgraph==0.3.34",
        "langgraph-sdk==0.1.53",
        "langgraph-cli[inmem]==0.1.74",
        "langchain==0.3.19",
        "langchain-openai==0.3.8",

        # API framework
        "fastapi[standard]==0.115.11",
        "starlette==0.46.0",
        "uvicorn==0.34.0",

        # General utilities
        "requests==2.32.3",
        "aiohttp>=3.9.0",
        "packaging==24.2",
        "python-dotenv==1.0.1",

        # Data / settings
        "pydantic==2.10.6",
        "pydantic-settings==2.8.1",
        "python_json_logger==3.3.0"
    ],
    extras_require={
        # Pin test-only tools to the exact versions in requirements.txt
        "test": [
            "pytest==8.3.5",
            "pytest-asyncio==0.26.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "pytest-timeout>=2.2.0",
        ],
        # Optional AGP helpers
        "agp": [
            "agp-api==0.0.5",
        ],
    },
    python_requires=">=3.9",
)
