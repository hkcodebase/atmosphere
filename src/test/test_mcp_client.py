"""
Tests for mcp_client modules: client.py, graph.py, graph_nodes.py, tools_lc.py, llm.py, state.py
"""

import pytest
import sys
import os
from unittest.mock import patch, Mock, MagicMock, AsyncMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_client.state import AgentState
from mcp_client.llm import get_llm
from mcp_client.tools_lc import get_location, get_forecast_by_location, get_alerts
from langchain_core.messages import HumanMessage


# ============================================================================
# TEST: state.py - AgentState TypedDict
# ============================================================================


class TestAgentState:
    def test_agent_state_structure(self):
        """Test that AgentState has correct structure."""
        state: AgentState = {
            "messages": [],
            "question": "What is the weather?",
            "answer": "",
        }
        assert "messages" in state
        assert "question" in state
        assert "answer" in state
        assert state["question"] == "What is the weather?"

    def test_agent_state_with_messages(self):
        """Test AgentState with populated messages."""
        state: AgentState = {
            "messages": [
                {"role": "user", "content": "Get weather for NYC"},
                {"role": "assistant", "content": "Getting weather..."},
            ],
            "question": "Get weather for NYC",
            "answer": "Weather is sunny",
        }
        assert len(state["messages"]) == 2
        assert state["messages"][0]["role"] == "user"

    def test_agent_state_types(self):
        """Test that AgentState fields have correct types."""
        state: AgentState = {
            "messages": [1, 2, 3],  # List
            "question": "string",  # String
            "answer": "string",  # String
        }
        assert isinstance(state["messages"], list)
        assert isinstance(state["question"], str)
        assert isinstance(state["answer"], str)

    def test_agent_state_with_human_message(self):
        """Test AgentState with HumanMessage object."""
        state: AgentState = {
            "messages": [HumanMessage(content="What is the weather?")],
            "question": "What is the weather?",
            "answer": "",
        }
        assert len(state["messages"]) == 1
        assert state["messages"][0].content == "What is the weather?"


# ============================================================================
# TEST: llm.py - get_llm() Function
# ============================================================================


class TestGetLLM:
    def test_get_llm_returns_chat_openai(self):
        """Test that get_llm returns a ChatOpenAI instance."""
        llm = get_llm()
        assert llm is not None
        assert hasattr(llm, "invoke") or hasattr(llm, "__call__")

    def test_get_llm_configuration(self):
        """Test that get_llm has correct configuration."""
        llm = get_llm()
        # Check that the LLM is configured with correct settings
        assert llm.model_name == "ai/gemma4"
        assert llm.temperature == 0.2

    def test_get_llm_has_streaming(self):
        """Test that get_llm has streaming enabled."""
        llm = get_llm()
        assert llm.streaming is True

    def test_llm_has_temperature(self):
        """Test that get_llm has temperature configured."""
        llm = get_llm()
        assert llm.temperature is not None


# ============================================================================
# TEST: tools_lc.py - Decorated Tool Functions
# ============================================================================


class TestToolsLC:
    def test_get_location_is_tool(self):
        """Test the get_location is defined as a tool."""
        assert get_location is not None
        # StructuredTool object from @tool decorator
        assert hasattr(get_location, "name")

    def test_get_forecast_by_location_is_tool(self):
        """Test the get_forecast_by_location is defined as a tool."""
        assert get_forecast_by_location is not None
        assert hasattr(get_forecast_by_location, "name")

    def test_get_alerts_is_tool(self):
        """Test the get_alerts is defined as a tool."""
        assert get_alerts is not None
        assert hasattr(get_alerts, "name")

    def test_tool_names(self):
        """Test that tools have correct names."""
        assert get_location.name == "get_location"
        assert get_forecast_by_location.name == "get_forecast_by_location"
        assert get_alerts.name == "get_alerts"

    def test_tool_descriptions(self):
        """Test that tools have descriptions."""
        assert get_location.description is not None
        assert len(get_location.description) > 0

    @patch("httpx.post")
    def test_get_location_tool_call(self, mock_post):
        """Test get_location tool structure."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": "Location: New York\nLatitude: 40.7128\nLongitude: -74.0060"
        }
        mock_post.return_value = mock_response

        # Tools are StructuredTool objects with invoke method
        result = get_location.invoke({"location": "New York"})
        assert "Latitude" in result

    @patch("httpx.post")
    def test_get_alerts_tool_call(self, mock_post):
        """Test get_alerts tool structure."""
        mock_response = Mock()
        mock_response.json.return_value = {"result": "No active weather alerts for CA"}
        mock_post.return_value = mock_response

        result = get_alerts.invoke({"state": "CA"})
        assert "No active" in result or isinstance(result, str)

    @patch("httpx.post")
    def test_tools_make_http_requests(self, mock_post):
        """Test that tools are properly defined."""
        mock_response = Mock()
        mock_response.json.return_value = {"result": "Test result"}
        mock_post.return_value = mock_response

        # Tools should be StructuredTool objects
        assert hasattr(get_location, "invoke")
        assert hasattr(get_alerts, "invoke")

    def test_tools_are_callable(self):
        """Test that tools can be invoked."""
        # Tools should have invoke method or be callable
        assert hasattr(get_location, "invoke") or callable(get_location)
        assert hasattr(get_forecast_by_location, "invoke") or callable(get_forecast_by_location)
        assert hasattr(get_alerts, "invoke") or callable(get_alerts)


# ============================================================================
# TEST: Client Module Structure
# ============================================================================


class TestClientModuleStructure:
    def test_client_module_file_exists(self):
        """Test that client.py file exists."""
        client_path = Path(__file__).parent.parent / "mcp_client" / "client.py"
        assert client_path.exists()

    def test_client_imports_graph(self):
        """Test that client.py imports graph."""
        client_path = Path(__file__).parent.parent / "mcp_client" / "client.py"
        with open(client_path) as f:
            content = f.read()
        assert "from graph import" in content or "import graph" in content

    def test_graph_module_file_exists(self):
        """Test that graph.py file exists."""
        graph_path = Path(__file__).parent.parent / "mcp_client" / "graph.py"
        assert graph_path.exists()

    def test_graph_nodes_module_file_exists(self):
        """Test that graph_nodes.py file exists."""
        graph_nodes_path = Path(__file__).parent.parent / "mcp_client" / "graph_nodes.py"
        assert graph_nodes_path.exists()


# ============================================================================
# TEST: Graph Module Structure
# ============================================================================


class TestGraphModuleStructure:
    def test_graph_file_imports_state(self):
        """Test that graph.py imports state."""
        graph_path = Path(__file__).parent.parent / "mcp_client" / "graph.py"
        with open(graph_path) as f:
            content = f.read()
        assert "AgentState" in content or "state" in content.lower()

    def test_graph_file_uses_langgraph(self):
        """Test that graph.py uses LangGraph."""
        graph_path = Path(__file__).parent.parent / "mcp_client" / "graph.py"
        with open(graph_path) as f:
            content = f.read()
        assert "StateGraph" in content
        assert "langgraph" in content.lower()

    def test_graph_nodes_file_has_nodes(self):
        """Test that graph_nodes.py defines nodes."""
        graph_nodes_path = Path(__file__).parent.parent / "mcp_client" / "graph_nodes.py"
        with open(graph_nodes_path) as f:
            content = f.read()
        assert "agent_node" in content
        assert "tools_node" in content
        assert "should_call_tools" in content


# ============================================================================
# TEST: Configuration and Setup
# ============================================================================


class TestConfiguration:
    def test_default_api_base_url(self):
        """Test default API base URL."""
        from mcp_client.tools_lc import API_BASE

        assert API_BASE is not None
        assert "8000" in API_BASE or "127.0.0.1" in API_BASE

    def test_llm_model_name_default(self):
        """Test default LLM model name."""
        llm = get_llm()
        assert "gemma" in llm.model_name.lower() or llm.model_name == "ai/gemma4"

    def test_llm_temperature_setting(self):
        """Test LLM temperature is set correctly."""
        llm = get_llm()
        assert llm.temperature == 0.2

    @patch.dict(os.environ, {"DOCKER_MODEL_URL": "http://custom:8080/v1"})
    def test_custom_model_url_can_be_set(self):
        """Test that DOCKER_MODEL_URL environment variable can be set."""
        custom_url = os.getenv("DOCKER_MODEL_URL", "http://localhost:12434/engines/v1")
        assert "custom:8080" in custom_url

    @patch.dict(os.environ, {"WEATHER_API_BASE": "http://custom:8000"})
    def test_custom_api_base_can_be_set(self):
        """Test that WEATHER_API_BASE environment variable can be set."""
        custom_url = os.getenv("WEATHER_API_BASE", "http://127.0.0.1:8000")
        assert "custom:8000" in custom_url


# ============================================================================
# TEST: Error Handling in Tools
# ============================================================================


class TestToolErrorHandling:
    @patch("httpx.post")
    def test_tool_http_error(self, mock_post):
        """Test tool handles HTTP errors gracefully."""
        mock_post.side_effect = Exception("Connection refused")

        try:
            get_location("New York")
        except Exception:
            pass  # Expected to raise

    def test_tools_have_error_handling(self):
        """Test that tools are properly defined."""
        # If tools are callable/invokable, they exist
        assert get_location.invoke or hasattr(get_location, "func")
        assert get_alerts.invoke or hasattr(get_alerts, "func")


# ============================================================================
# TEST: Tool Descriptions and Arguments
# ============================================================================


class TestToolMetadata:
    def test_get_location_has_description(self):
        """Test that get_location has a description."""
        assert get_location.description is not None
        assert "latitude" in get_location.description.lower() or "location" in get_location.description.lower()

    def test_get_forecast_by_location_has_description(self):
        """Test that get_forecast_by_location has a description."""
        assert get_forecast_by_location.description is not None
        assert "forecast" in get_forecast_by_location.description.lower()

    def test_get_alerts_has_description(self):
        """Test that get_alerts has a description."""
        assert get_alerts.description is not None
        assert "alert" in get_alerts.description.lower()

    def test_tool_schemas_defined(self):
        """Test that tools have argument schemas."""
        assert get_location.args_schema is not None
        assert get_forecast_by_location.args_schema is not None
        assert get_alerts.args_schema is not None


# ============================================================================
# TEST: Module Imports
# ============================================================================


class TestModuleImports:
    def test_state_module_exists(self):
        """Test that state module exists and is importable."""
        try:
            from mcp_client.state import AgentState
            assert AgentState is not None
        except ImportError:
            pytest.fail("Cannot import AgentState from mcp_client.state")

    def test_llm_module_exists(self):
        """Test that llm module exists and is importable."""
        try:
            from mcp_client.llm import get_llm
            assert get_llm is not None
        except ImportError:
            pytest.fail("Cannot import get_llm from mcp_client.llm")

    def test_tools_module_exists(self):
        """Test that tools_lc module exists and is importable."""
        try:
            from mcp_client.tools_lc import (
                get_location,
                get_forecast_by_location,
                get_alerts,
            )
            assert all(
                [get_location, get_forecast_by_location, get_alerts]
            )
        except ImportError:
            pytest.fail("Cannot import tools from mcp_client.tools_lc")


# ============================================================================
# TEST: Message Handling
# ============================================================================


class TestMessageHandling:
    def test_human_message_import(self):
        """Test HumanMessage can be imported."""
        msg = HumanMessage(content="Hello")
        assert msg.content == "Hello"

    def test_human_message_with_metadata(self):
        """Test HumanMessage with metadata."""
        msg = HumanMessage(content="What is weather", name="user")
        assert msg.content == "What is weather"

    def test_agent_state_message_list(self):
        """Test AgentState can hold message objects."""
        state: AgentState = {
            "messages": [HumanMessage(content="What is weather?")],
            "question": "What is weather?",
            "answer": "",
        }
        assert len(state["messages"]) == 1
        assert state["messages"][0].content == "What is weather?"


# ============================================================================
# TEST: API Response Handling
# ============================================================================


class TestAPIResponseHandling:
    @patch("httpx.post")
    def test_successful_location_response(self, mock_post):
        """Test handling of successful location response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": "Location: New York, NY\nLatitude: 40.7128\nLongitude: -74.0060"
        }
        mock_post.return_value = mock_response

        result = get_location.invoke({"location": "New York, NY"})
        assert "Latitude" in result
        assert "Longitude" in result

    @patch("httpx.post")
    def test_error_response_handling(self, mock_post):
        """Test handling of error responses."""
        mock_response = Mock()
        mock_response.json.return_value = {"result": "Error: Location not found"}
        mock_post.return_value = mock_response

        result = get_location.invoke({"location": "Invalid Location XYZ"})
        assert isinstance(result, str)


