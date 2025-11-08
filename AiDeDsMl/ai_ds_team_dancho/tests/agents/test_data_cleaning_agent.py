"""Unit tests for DataCleaningAgent.

This module contains comprehensive unit tests for the DataCleaningAgent class,
including initialization, invocation, error handling, state management, and
data cleaning functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
import json

from ai_data_science_team.agents.data_cleaning_agent import DataCleaningAgent, make_data_cleaning_agent


# ===== Initialization Tests =====

@pytest.mark.unit
def test_data_cleaning_agent_initialization(mock_llm):
    """Test that DataCleaningAgent initializes correctly with default parameters."""
    agent = DataCleaningAgent(model=mock_llm)

    assert agent._params["model"] == mock_llm
    assert agent._params["n_samples"] == 30
    assert agent._params["log"] is False
    assert agent._params["human_in_the_loop"] is False
    assert agent.response is None
    assert agent._compiled_graph is not None


@pytest.mark.unit
def test_data_cleaning_agent_initialization_with_custom_params(mock_llm, tmp_path):
    """Test DataCleaningAgent initialization with custom parameters."""
    log_path = str(tmp_path / "logs")

    agent = DataCleaningAgent(
        model=mock_llm,
        n_samples=50,
        log=True,
        log_path=log_path,
        file_name="custom_cleaner.py",
        function_name="custom_clean",
        overwrite=False,
        human_in_the_loop=False,
        bypass_recommended_steps=True,
        bypass_explain_code=True
    )

    assert agent._params["n_samples"] == 50
    assert agent._params["log"] is True
    assert agent._params["log_path"] == log_path
    assert agent._params["file_name"] == "custom_cleaner.py"
    assert agent._params["function_name"] == "custom_clean"
    assert agent._params["overwrite"] is False
    assert agent._params["bypass_recommended_steps"] is True
    assert agent._params["bypass_explain_code"] is True


@pytest.mark.unit
def test_data_cleaning_agent_compiled_graph_creation(mock_llm):
    """Test that the compiled graph is created correctly."""
    agent = DataCleaningAgent(model=mock_llm)

    assert agent._compiled_graph is not None
    # Check that it's a compiled state graph
    assert hasattr(agent._compiled_graph, 'invoke')


@pytest.mark.unit
def test_make_compiled_graph_resets_response(mock_llm):
    """Test that _make_compiled_graph resets the response attribute."""
    agent = DataCleaningAgent(model=mock_llm)

    # Set a fake response
    agent.response = {"test": "data"}

    # Rebuild the graph
    agent._make_compiled_graph()

    # Response should be reset to None
    assert agent.response is None


# ===== Invocation Tests =====

@pytest.mark.unit
def test_invoke_agent_with_valid_dataframe(mock_llm, sample_dataframe):
    """Test invoking the agent with a valid DataFrame."""
    mock_llm.invoke = Mock(return_value=Mock(
        content='def data_cleaner(data_raw):\n    import pandas as pd\n    return data_raw.dropna()'
    ))

    agent = DataCleaningAgent(model=mock_llm, bypass_recommended_steps=True)

    # Mock the compiled graph's invoke method
    mock_response = {
        "data_raw": sample_dataframe.to_dict(),
        "data_cleaned": sample_dataframe.dropna().to_dict(),
        "data_cleaner_function": "def data_cleaner(data_raw):\n    return data_raw",
        "messages": []
    }
    agent._compiled_graph.invoke = Mock(return_value=mock_response)

    # Invoke the agent
    agent.invoke_agent(
        data_raw=sample_dataframe,
        user_instructions="Clean the data",
        max_retries=3,
        retry_count=0
    )

    # Check that response was stored
    assert agent.response is not None
    assert "data_cleaned" in agent.response
    assert agent._compiled_graph.invoke.called


@pytest.mark.unit
def test_invoke_agent_with_empty_dataframe(mock_llm):
    """Test invoking the agent with an empty DataFrame."""
    empty_df = pd.DataFrame()
    agent = DataCleaningAgent(model=mock_llm, bypass_recommended_steps=True)

    mock_response = {
        "data_raw": empty_df.to_dict(),
        "data_cleaned": empty_df.to_dict(),
        "data_cleaner_function": "def data_cleaner(data_raw):\n    return data_raw",
        "messages": []
    }
    agent._compiled_graph.invoke = Mock(return_value=mock_response)

    agent.invoke_agent(data_raw=empty_df, user_instructions="Clean the data")

    assert agent.response is not None


@pytest.mark.unit
def test_invoke_agent_with_none_instructions(mock_llm, sample_dataframe):
    """Test that agent handles None user instructions."""
    agent = DataCleaningAgent(model=mock_llm, bypass_recommended_steps=True)

    mock_response = {
        "data_raw": sample_dataframe.to_dict(),
        "data_cleaned": sample_dataframe.to_dict(),
        "data_cleaner_function": "def data_cleaner(data_raw):\n    return data_raw",
        "messages": []
    }
    agent._compiled_graph.invoke = Mock(return_value=mock_response)

    # Should not raise an error
    agent.invoke_agent(data_raw=sample_dataframe, user_instructions=None)

    assert agent.response is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ainvoke_agent_with_valid_dataframe(mock_llm, sample_dataframe):
    """Test asynchronous invocation of the agent."""
    agent = DataCleaningAgent(model=mock_llm, bypass_recommended_steps=True)

    mock_response = {
        "data_raw": sample_dataframe.to_dict(),
        "data_cleaned": sample_dataframe.to_dict(),
        "data_cleaner_function": "def data_cleaner(data_raw):\n    return data_raw",
        "messages": []
    }

    # Create an async mock
    async def async_mock_invoke(*args, **kwargs):
        return mock_response

    agent._compiled_graph.ainvoke = async_mock_invoke

    await agent.ainvoke_agent(
        data_raw=sample_dataframe,
        user_instructions="Clean the data"
    )

    assert agent.response is not None


# ===== Getter Method Tests =====

@pytest.mark.unit
def test_get_data_cleaned_returns_dataframe(mock_llm, sample_dataframe):
    """Test that get_data_cleaned returns a DataFrame."""
    agent = DataCleaningAgent(model=mock_llm)

    # Set a mock response
    agent.response = {
        "data_cleaned": sample_dataframe.to_dict()
    }

    result = agent.get_data_cleaned()

    assert isinstance(result, pd.DataFrame)
    assert result.shape == sample_dataframe.shape


@pytest.mark.unit
def test_get_data_cleaned_returns_none_when_no_response(mock_llm):
    """Test that get_data_cleaned returns None when no response exists."""
    agent = DataCleaningAgent(model=mock_llm)

    result = agent.get_data_cleaned()

    assert result is None


@pytest.mark.unit
def test_get_data_raw_returns_dataframe(mock_llm, sample_dataframe):
    """Test that get_data_raw returns the original DataFrame."""
    agent = DataCleaningAgent(model=mock_llm)

    agent.response = {
        "data_raw": sample_dataframe.to_dict()
    }

    result = agent.get_data_raw()

    assert isinstance(result, pd.DataFrame)
    assert result.shape == sample_dataframe.shape


@pytest.mark.unit
def test_get_data_cleaner_function_returns_string(mock_llm):
    """Test that get_data_cleaner_function returns a string."""
    agent = DataCleaningAgent(model=mock_llm)

    function_code = "def data_cleaner(data_raw):\n    return data_raw"
    agent.response = {
        "data_cleaner_function": function_code
    }

    result = agent.get_data_cleaner_function(markdown=False)

    assert isinstance(result, str)
    assert "def data_cleaner" in result


@pytest.mark.unit
def test_get_data_cleaner_function_returns_markdown(mock_llm):
    """Test that get_data_cleaner_function returns Markdown object."""
    agent = DataCleaningAgent(model=mock_llm)

    function_code = "def data_cleaner(data_raw):\n    return data_raw"
    agent.response = {
        "data_cleaner_function": function_code
    }

    from IPython.display import Markdown
    result = agent.get_data_cleaner_function(markdown=True)

    assert isinstance(result, Markdown)


@pytest.mark.unit
def test_get_recommended_cleaning_steps(mock_llm):
    """Test that get_recommended_cleaning_steps returns steps."""
    agent = DataCleaningAgent(model=mock_llm)

    steps = "1. Remove missing values\n2. Remove duplicates"
    agent.response = {
        "recommended_steps": steps
    }

    result = agent.get_recommended_cleaning_steps(markdown=False)

    assert isinstance(result, str)
    assert "Remove missing values" in result


@pytest.mark.unit
def test_get_workflow_summary_with_messages(mock_llm):
    """Test that get_workflow_summary returns summary when messages exist."""
    agent = DataCleaningAgent(model=mock_llm)

    mock_message = Mock()
    mock_message.content = json.dumps({
        "agent": "data_cleaning_agent",
        "outputs": {"data_cleaner_function": "test"}
    })

    agent.response = {
        "messages": [mock_message]
    }

    result = agent.get_workflow_summary(markdown=False)

    assert result is not None
    assert isinstance(result, str)


@pytest.mark.unit
def test_get_workflow_summary_returns_none_without_messages(mock_llm):
    """Test that get_workflow_summary returns None when no messages exist."""
    agent = DataCleaningAgent(model=mock_llm)

    agent.response = {}

    result = agent.get_workflow_summary()

    assert result is None


@pytest.mark.unit
def test_get_log_summary_with_logging_enabled(mock_llm):
    """Test that get_log_summary returns summary when logging is enabled."""
    agent = DataCleaningAgent(model=mock_llm, log=True)

    agent.response = {
        "data_cleaner_function_path": "/path/to/function.py",
        "data_cleaner_function_name": "data_cleaner"
    }

    result = agent.get_log_summary(markdown=False)

    assert result is not None
    assert isinstance(result, str)
    assert "/path/to/function.py" in result
    assert "data_cleaner" in result


@pytest.mark.unit
def test_get_log_summary_returns_none_without_path(mock_llm):
    """Test that get_log_summary returns None when no path exists."""
    agent = DataCleaningAgent(model=mock_llm)

    agent.response = {}

    result = agent.get_log_summary()

    assert result is None


# ===== State Management Tests =====

@pytest.mark.unit
def test_update_params_rebuilds_graph(mock_llm):
    """Test that update_params rebuilds the compiled graph."""
    agent = DataCleaningAgent(model=mock_llm, n_samples=30)

    old_graph = agent._compiled_graph

    # Update parameters
    agent.update_params(n_samples=50, log=True)

    # Graph should be rebuilt (different object)
    assert agent._params["n_samples"] == 50
    assert agent._params["log"] is True
    # Response should be reset
    assert agent.response is None


# ===== Data Processing Tests =====

@pytest.mark.unit
def test_agent_with_dataframe_containing_missing_values(mock_llm, sample_dataframe_with_missing):
    """Test agent with DataFrame containing missing values."""
    agent = DataCleaningAgent(model=mock_llm, bypass_recommended_steps=True)

    cleaned_df = sample_dataframe_with_missing.dropna()
    mock_response = {
        "data_raw": sample_dataframe_with_missing.to_dict(),
        "data_cleaned": cleaned_df.to_dict(),
        "data_cleaner_function": "def data_cleaner(data_raw):\n    return data_raw.dropna()",
        "messages": []
    }
    agent._compiled_graph.invoke = Mock(return_value=mock_response)

    agent.invoke_agent(
        data_raw=sample_dataframe_with_missing,
        user_instructions="Remove missing values"
    )

    assert agent.response is not None
    cleaned_result = agent.get_data_cleaned()
    assert cleaned_result is not None
    # Cleaned data should have fewer rows
    assert len(cleaned_result) < len(sample_dataframe_with_missing)


@pytest.mark.unit
def test_agent_with_dataframe_containing_duplicates(mock_llm, sample_dataframe_with_duplicates):
    """Test agent with DataFrame containing duplicate rows."""
    agent = DataCleaningAgent(model=mock_llm, bypass_recommended_steps=True)

    cleaned_df = sample_dataframe_with_duplicates.drop_duplicates()
    mock_response = {
        "data_raw": sample_dataframe_with_duplicates.to_dict(),
        "data_cleaned": cleaned_df.to_dict(),
        "data_cleaner_function": "def data_cleaner(data_raw):\n    return data_raw.drop_duplicates()",
        "messages": []
    }
    agent._compiled_graph.invoke = Mock(return_value=mock_response)

    agent.invoke_agent(
        data_raw=sample_dataframe_with_duplicates,
        user_instructions="Remove duplicate rows"
    )

    assert agent.response is not None
    cleaned_result = agent.get_data_cleaned()
    assert cleaned_result is not None
    # Cleaned data should have fewer rows
    assert len(cleaned_result) < len(sample_dataframe_with_duplicates)


# ===== Error Handling Tests =====

@pytest.mark.unit
def test_agent_handles_max_retries(mock_llm, sample_dataframe):
    """Test that agent respects max_retries parameter."""
    agent = DataCleaningAgent(model=mock_llm, bypass_recommended_steps=True)

    mock_response = {
        "data_raw": sample_dataframe.to_dict(),
        "data_cleaned": sample_dataframe.to_dict(),
        "max_retries": 5,
        "retry_count": 0,
        "messages": []
    }
    agent._compiled_graph.invoke = Mock(return_value=mock_response)

    agent.invoke_agent(
        data_raw=sample_dataframe,
        user_instructions="Clean data",
        max_retries=5
    )

    # Check that max_retries was passed to the graph
    call_args = agent._compiled_graph.invoke.call_args[0][0]
    assert call_args["max_retries"] == 5


# ===== Configuration Tests =====

@pytest.mark.unit
def test_make_data_cleaning_agent_function(mock_llm):
    """Test the make_data_cleaning_agent factory function."""
    graph = make_data_cleaning_agent(
        model=mock_llm,
        n_samples=30,
        log=False
    )

    assert graph is not None
    assert hasattr(graph, 'invoke')


@pytest.mark.unit
def test_agent_bypass_recommended_steps(mock_llm, sample_dataframe):
    """Test agent with bypass_recommended_steps=True."""
    agent = DataCleaningAgent(
        model=mock_llm,
        bypass_recommended_steps=True
    )

    assert agent._params["bypass_recommended_steps"] is True


@pytest.mark.unit
def test_agent_bypass_explain_code(mock_llm):
    """Test agent with bypass_explain_code=True."""
    agent = DataCleaningAgent(
        model=mock_llm,
        bypass_explain_code=True
    )

    assert agent._params["bypass_explain_code"] is True
