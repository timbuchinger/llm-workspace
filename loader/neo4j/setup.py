from setuptools import find_packages, setup

setup(
    name="notion-memgraph-sync",
    version="0.1.0",
    packages=find_packages(),
    package_dir={"": "src"},
    install_requires=[
        "chromadb",
        "langchain-chroma",
        "langchain-core",
        "langchain-google-genai",
        "langchain-groq",
        "langchain-ollama",
        "neo4j",
        "python-dotenv",
        "requests",
        "tiktoken",
    ],
    entry_points={
        "console_scripts": [
            "notion-sync=main:main",
        ],
    },
)
