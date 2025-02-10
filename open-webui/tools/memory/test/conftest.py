from unittest.mock import patch

import pytest
import pytest_asyncio


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


@pytest.fixture
def mock_tools():
    with patch("memory.server.tools") as mock:
        yield mock
        # yield mock
        # yield mock


import asyncio
import os
import signal
import socket
import subprocess
import time
from typing import AsyncGenerator

import pytest
import requests
from memory.client import Tools


def get_free_port():
    """Get a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def wait_for_server(url: str, timeout: int = 30):
    """Wait for server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/healthz")
            if response.status_code == 200:
                return True
            # response = requests.post(
            #     f"{url}/retrieve_all", data={"chroma_collection_name": "test_memories"}
            # )
            # if response.status_code == 200:
            #     return True
            # else:
            #     time.sleep(1)
        except requests.exceptions.RequestException:
            time.sleep(1)
    raise TimeoutError(f"Server didn't start within {timeout} seconds")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# @pytest.fixture(scope="session", autouse=True)
# def setup_test_env():
#     """Setup test environment variables."""
#     # Store original environment variables
#     original_env = {
#         "OLLAMA_HOST": os.environ.get("OLLAMA_HOST"),
#         "OLLAMA_PORT": os.environ.get("OLLAMA_PORT"),
#         "CHROMA_HOST": os.environ.get("CHROMA_HOST"),
#         "CHROMA_PORT": os.environ.get("CHROMA_PORT"),
#         "CHROMA_AUTH_TOKEN": os.environ.get("CHROMA_AUTH_TOKEN"),
#     }

#     # Set test environment variables if not already set
#     if not os.environ.get("OLLAMA_HOST"):
#         os.environ["OLLAMA_HOST"] = "ollama.buchinger.ca"
#     if not os.environ.get("OLLAMA_PORT"):
#         os.environ["OLLAMA_PORT"] = "443"
#     if not os.environ.get("CHROMA_HOST"):
#         os.environ["CHROMA_HOST"] = "chroma.buchinger.ca"
#     if not os.environ.get("CHROMA_PORT"):
#         os.environ["CHROMA_PORT"] = "443"

#     yield

#     # Restore original environment variables
#     for key, value in original_env.items():
#         if value is not None:
#             os.environ[key] = value
#         elif key in os.environ:
#             del os.environ[key]


@pytest.fixture(scope="session")
def server_port():
    """Get a free port for the test server."""
    return get_free_port()


@pytest.fixture(scope="session")
def server_url(server_port):
    """Get the server URL."""
    return f"http://localhost:{server_port}"


@pytest.fixture(scope="session", autouse=True)
def start_server(server_port):
    """Start the server for integration tests."""
    # Start the server process
    server_process = subprocess.Popen(
        [
            "uvicorn",
            "memory.server:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(server_port),
            "--log-level",
            "debug",
        ],
        # Redirect output to prevent cluttering test output
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
        preexec_fn=os.setsid,  # Used to kill the process group
    )
    print(os.getcwd())

    ###
    ### Useful for debugging cases where the server does not start
    ###
    # stdout, stderr = server_process.communicate()
    # if server_process.returncode != 0:
    #     raise RuntimeError(f"Server failed to start: {stderr.decode()}")

    # Wait for server to be ready
    try:
        wait_for_server(f"http://localhost:{server_port}")
    except TimeoutError as e:
        # Kill the server process if startup times out
        os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
        raise e

    yield server_process

    # Cleanup: Kill the server process and its children
    os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
    server_process.wait()


@pytest_asyncio.fixture
async def memory_tools(server_url) -> AsyncGenerator[Tools, None]:
    """Create a Tools instance configured for testing."""
    tools = Tools()
    tools.valves.server_url = server_url
    # Override the base URL to point to our test server
    os.environ["BASE_URL"] = server_url
    # Use a specific collection for integration tests
    tools.user_valves.chroma_collection = (
        "test_memories"  # TODO: Use dedicated collection
    )
    yield tools
    # Reset the base URL
    if "BASE_URL" in os.environ:
        del os.environ["BASE_URL"]
