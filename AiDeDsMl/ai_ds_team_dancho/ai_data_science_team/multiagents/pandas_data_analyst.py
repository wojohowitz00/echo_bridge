from langchain_core.messages import BaseMessage
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.types import Checkpointer
from langgraph.graph import START, END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from typing import (
    TYPE_CHECKING,
    TypedDict,
    Annotated,
    Sequence,
    Union,
    Dict,
    Any,
    Optional,
    List,
    cast,
)
import operator

import pandas as pd
import json
from IPython.display import Markdown

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

from ai_data_science_team.templates import BaseAgent
from ai_data_science_team.agents import DataWranglingAgent, DataVisualizationAgent
from ai_data_science_team.utils.plotly import plotly_from_dict
from ai_data_science_team.utils.regex import remove_consecutive_duplicates, get_generic_summary

AGENT_NAME = "pandas_data_analyst"

class PandasDataAnalyst(BaseAgent):
    """
    PandasDataAnalyst is a multi-agent class that combines data wrangling and visualization capabilities.

    Parameters:
    -----------
    model:
        The language model to be used for the agents.
    data_wrangling_agent: DataWranglingAgent
        The Data Wrangling Agent for transforming raw data.
    data_visualization_agent: DataVisualizationAgent
        The Data Visualization Agent for generating plots.
    checkpointer: Checkpointer (optional)
        The checkpointer to save the state of the multi-agent system.

    Methods:
    --------
    ainvoke_agent(user_instructions, data_raw, **kwargs)
        Asynchronously invokes the multi-agent with user instructions and raw data.
    invoke_agent(user_instructions, data_raw, **kwargs)
        Synchronously invokes the multi-agent with user instructions and raw data.
    get_data_wrangled()
        Returns the wrangled data as a Pandas DataFrame.
    get_plotly_graph()
        Returns the Plotly graph as a Plotly object.
    get_data_wrangler_function(markdown=False)
        Returns the data wrangling function as a string, optionally in Markdown.
    get_data_visualization_function(markdown=False)
        Returns the data visualization function as a string, optionally in Markdown.
    """

    def __init__(
        self,
        model: Any,  # langchain_core.language_models.chat_models.BaseChatModel
        data_wrangling_agent: DataWranglingAgent,
        data_visualization_agent: DataVisualizationAgent,
        checkpointer: Optional[Checkpointer] = None,
    ) -> None:
        self._params: Dict[str, Any] = {
            "model": model,
            "data_wrangling_agent": data_wrangling_agent,
            "data_visualization_agent": data_visualization_agent,
            "checkpointer": checkpointer,
        }
        self._compiled_graph: CompiledStateGraph = self._make_compiled_graph()
        self.response: Optional[Dict[str, Any]] = None

    def _make_compiled_graph(self) -> CompiledStateGraph:
        """
        Create or rebuild the compiled graph. Resets response to None.

        Returns
        -------
        CompiledStateGraph
            The compiled state graph for the pandas data analyst.
        """
        self.response = None
        return make_pandas_data_analyst(
            model=self._params["model"],
            data_wrangling_agent=self._params["data_wrangling_agent"]._compiled_graph,
            data_visualization_agent=self._params["data_visualization_agent"]._compiled_graph,
            checkpointer=self._params["checkpointer"],
        )

    def update_params(self, **kwargs: Any) -> None:
        """
        Updates parameters and rebuilds the compiled graph.

        Parameters
        ----------
        **kwargs : Any
            Parameters to update (model, data_wrangling_agent, etc.)
        """
        for k, v in kwargs.items():
            self._params[k] = v
        self._compiled_graph = self._make_compiled_graph()

    async def ainvoke_agent(
        self,
        user_instructions: str,
        data_raw: Union[pd.DataFrame, Dict[str, Any], List[Union[pd.DataFrame, Dict[str, Any]]]],
        max_retries: int = 3,
        retry_count: int = 0,
        **kwargs: Any
    ) -> None:
        """
        Asynchronously invokes the multi-agent.

        Parameters
        ----------
        user_instructions : str
            Instructions for data analysis and visualization.
        data_raw : Union[pd.DataFrame, Dict[str, Any], List[Union[pd.DataFrame, Dict[str, Any]]]]
            The raw data to analyze (DataFrame, dict, or list of DataFrames/dicts).
        max_retries : int, default=3
            Maximum retry attempts.
        retry_count : int, default=0
            Current retry attempt.
        **kwargs : Any
            Additional keyword arguments to pass to ainvoke().
        """
        response = await self._compiled_graph.ainvoke({
            "user_instructions": user_instructions,
            "data_raw": self._convert_data_input(data_raw),
            "max_retries": max_retries,
            "retry_count": retry_count,
        }, **kwargs)
        if response.get("messages"):
            response["messages"] = remove_consecutive_duplicates(response["messages"])
        self.response = response

    def invoke_agent(
        self,
        user_instructions: str,
        data_raw: Union[pd.DataFrame, Dict[str, Any], List[Union[pd.DataFrame, Dict[str, Any]]]],
        max_retries: int = 3,
        retry_count: int = 0,
        **kwargs: Any
    ) -> None:
        """
        Synchronously invokes the multi-agent.

        Parameters
        ----------
        user_instructions : str
            Instructions for data analysis and visualization.
        data_raw : Union[pd.DataFrame, Dict[str, Any], List[Union[pd.DataFrame, Dict[str, Any]]]]
            The raw data to analyze (DataFrame, dict, or list of DataFrames/dicts).
        max_retries : int, default=3
            Maximum retry attempts.
        retry_count : int, default=0
            Current retry attempt.
        **kwargs : Any
            Additional keyword arguments to pass to invoke().
        """
        response = self._compiled_graph.invoke({
            "user_instructions": user_instructions,
            "data_raw": self._convert_data_input(data_raw),
            "max_retries": max_retries,
            "retry_count": retry_count,
        }, **kwargs)
        if response.get("messages"):
            response["messages"] = remove_consecutive_duplicates(response["messages"])
        self.response = response

    def get_data_wrangled(self) -> Optional[pd.DataFrame]:
        """
        Returns the wrangled data as a Pandas DataFrame.

        Returns
        -------
        Optional[pd.DataFrame]
            The wrangled DataFrame, or None if not available.
        """
        if self.response and self.response.get("data_wrangled"):
            return pd.DataFrame(self.response.get("data_wrangled"))
        return None

    def get_plotly_graph(self) -> Any:
        """
        Returns the Plotly graph as a Plotly object.

        Returns
        -------
        Any
            The Plotly graph object, or None if not available.
        """
        if self.response and self.response.get("plotly_graph"):
            plotly_graph_dict = self.response.get("plotly_graph")
            if plotly_graph_dict and isinstance(plotly_graph_dict, dict):
                return plotly_from_dict(plotly_graph_dict)
        return None

    def get_data_wrangler_function(self, markdown: bool = False) -> Union[str, Markdown, None]:
        """
        Returns the data wrangling function as a string.

        Parameters
        ----------
        markdown : bool, default=False
            If True, returns the function as an IPython Markdown code block.

        Returns
        -------
        Union[str, Markdown, None]
            The data wrangling function code, or None if not available.
        """
        if self.response and self.response.get("data_wrangler_function"):
            code = self.response.get("data_wrangler_function")
            return Markdown(f"```python\n{code}\n```") if markdown else code
        return None

    def get_data_visualization_function(self, markdown: bool = False) -> Union[str, Markdown, None]:
        """
        Returns the data visualization function as a string.

        Parameters
        ----------
        markdown : bool, default=False
            If True, returns the function as an IPython Markdown code block.

        Returns
        -------
        Union[str, Markdown, None]
            The data visualization function code, or None if not available.
        """
        if self.response and self.response.get("data_visualization_function"):
            code = self.response.get("data_visualization_function")
            return Markdown(f"```python\n{code}\n```") if markdown else code
        return None

    def get_workflow_summary(self, markdown: bool = False) -> Union[str, Markdown, None]:
        """
        Returns a summary of the workflow.

        Parameters
        ----------
        markdown : bool, default=False
            If True, returns the summary as an IPython Markdown object.

        Returns
        -------
        Union[str, Markdown, None]
            The workflow summary, or None if no messages available.
        """
        if self.response and self.response.get("messages"):
            agents = [msg.role for msg in self.response["messages"]]
            agent_labels = [f"- **Agent {i+1}:** {role}\n" for i, role in enumerate(agents)]
            header = f"# Pandas Data Analyst Workflow Summary\n\nThis workflow contains {len(agents)} agents:\n\n" + "\n".join(agent_labels)
            reports = [get_generic_summary(json.loads(msg.content)) for msg in self.response["messages"]]
            summary = "\n\n" + header + "\n\n".join(reports)
            return Markdown(summary) if markdown else summary
        return None

    @staticmethod
    def _convert_data_input(
        data_raw: Union[pd.DataFrame, Dict[str, Any], List[Union[pd.DataFrame, Dict[str, Any]]]]
    ) -> Union[Dict[str, Any], List[Union[Dict[str, Any], pd.DataFrame]]]:
        """
        Converts input data to the expected format (dict or list of dicts).

        Parameters
        ----------
        data_raw : Union[pd.DataFrame, Dict[str, Any], List[Union[pd.DataFrame, Dict[str, Any]]]]
            Input data in various formats.

        Returns
        -------
        Union[Dict[str, Any], List[Union[Dict[str, Any], pd.DataFrame]]]
            Converted data ready for graph processing.

        Raises
        ------
        ValueError
            If data_raw is not a DataFrame, dict, or list of DataFrames/dicts.
        """
        if isinstance(data_raw, pd.DataFrame):
            return data_raw.to_dict()
        if isinstance(data_raw, dict):
            return data_raw
        if isinstance(data_raw, list):
            return [item.to_dict() if isinstance(item, pd.DataFrame) else item for item in data_raw]
        raise ValueError("data_raw must be a DataFrame, dict, or list of DataFrames/dicts")

def make_pandas_data_analyst(
    model: Any,  # langchain_core.language_models.chat_models.BaseChatModel
    data_wrangling_agent: CompiledStateGraph,
    data_visualization_agent: CompiledStateGraph,
    checkpointer: Optional[Checkpointer] = None
) -> CompiledStateGraph:
    """
    Creates a multi-agent system that wrangles data and optionally visualizes it.

    Parameters:
    -----------
    model: The language model to be used.
    data_wrangling_agent: CompiledStateGraph
        The Data Wrangling Agent.
    data_visualization_agent: CompiledStateGraph
        The Data Visualization Agent.
    checkpointer: Checkpointer (optional)
        The checkpointer to save the state.

    Returns:
    --------
    CompiledStateGraph: The compiled multi-agent system.
    """
    
    llm = model
    
    routing_preprocessor_prompt = PromptTemplate(
        template="""
        You are an expert in routing decisions for a Pandas Data Manipulation Wrangling Agent, a Charting Visualization Agent, and a Pandas Table Agent. Your job is to tell the agents which actions to perform and determine the correct routing for the incoming user question:
        
        1. Determine what the correct format for a Users Question should be for use with a Pandas Data Wrangling Agent based on the incoming user question. Anything related to data wrangling and manipulation should be passed along. Anything related to data analysis can be handled by the Pandas Agent. Anything that uses Pandas can be passed along. Tables can be returned from this agent. Don't pass along anything about plotting or visualization.
        2. Determine whether or not a chart should be generated or a table should be returned based on the users question.
        3. If a chart is requested, determine the correct format of a Users Question should be used with a Data Visualization Agent. Anything related to plotting and visualization should be passed along.
        
        Use the following criteria on how to route the the initial user question:
        
        From the incoming user question, remove any details about the format of the final response as either a Chart or Table and return only the important part of the incoming user question that is relevant for the Pandas Data Wrangling and Transformation agent. This will be the 'user_instructions_data_wrangling'. If 'None' is found, return the original user question.
        
        Next, determine if the user would like a data visualization ('chart') or a 'table' returned with the results of the Data Wrangling Agent. If unknown, not specified or 'None' is found, then select 'table'.  
        
        If a 'chart' is requested, return the 'user_instructions_data_visualization'. If 'None' is found, return None.
        
        Return JSON with 'user_instructions_data_wrangling', 'user_instructions_data_visualization' and 'routing_preprocessor_decision'.
        
        INITIAL_USER_QUESTION: {user_instructions}
        """,
        input_variables=["user_instructions"]
    )

    routing_preprocessor = routing_preprocessor_prompt | llm | JsonOutputParser()

    class PrimaryState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], operator.add]
        user_instructions: str
        user_instructions_data_wrangling: str
        user_instructions_data_visualization: str
        routing_preprocessor_decision: str
        data_raw: Union[dict, list]
        data_wrangled: dict
        data_wrangler_function: str
        data_visualization_function: str
        plotly_graph: dict
        plotly_error: str
        max_retries: int
        retry_count: int
        
        
    def preprocess_routing(state: PrimaryState) -> Dict[str, str]:
        """
        Preprocess and route user instructions to appropriate agents.

        Parameters
        ----------
        state : PrimaryState
            The current state containing user instructions.

        Returns
        -------
        Dict[str, str]
            Dictionary with routing decisions and processed instructions.
        """
        print("---PANDAS DATA ANALYST---")
        print("*************************")
        print("---PREPROCESS ROUTER---")
        question = state.get("user_instructions")

        # Chart Routing and SQL Prep
        response = routing_preprocessor.invoke({"user_instructions": question})

        return {
            "user_instructions_data_wrangling": response.get('user_instructions_data_wrangling'),
            "user_instructions_data_visualization": response.get('user_instructions_data_visualization'),
            "routing_preprocessor_decision": response.get('routing_preprocessor_decision'),
        }

    def router_chart_or_table(state: PrimaryState) -> str:
        """
        Route to either chart or table based on routing decision.

        Parameters
        ----------
        state : PrimaryState
            The current state with routing decision.

        Returns
        -------
        str
            Either 'chart' or 'table' routing decision.
        """
        print("---ROUTER: CHART OR TABLE---")
        return "chart" if state.get('routing_preprocessor_decision') == "chart" else "table"


    def invoke_data_wrangling_agent(state: PrimaryState) -> Dict[str, Any]:
        """
        Invoke the data wrangling agent.

        Parameters
        ----------
        state : PrimaryState
            The current state with data and instructions.

        Returns
        -------
        Dict[str, Any]
            Results from data wrangling including wrangled data and function.
        """
        response = data_wrangling_agent.invoke({
            "user_instructions": state.get("user_instructions_data_wrangling"),
            "data_raw": state.get("data_raw"),
            "max_retries": state.get("max_retries"),
            "retry_count": state.get("retry_count"),
        })

        return {
            "messages": response.get("messages"),
            "data_wrangled": response.get("data_wrangled"),
            "data_wrangler_function": response.get("data_wrangler_function"),
            "plotly_error": response.get("data_visualization_error"),

        }

    def invoke_data_visualization_agent(state: PrimaryState) -> Dict[str, Any]:
        """
        Invoke the data visualization agent.

        Parameters
        ----------
        state : PrimaryState
            The current state with data and instructions.

        Returns
        -------
        Dict[str, Any]
            Results from visualization including plotly graph and function.
        """
        response = data_visualization_agent.invoke({
            "user_instructions": state.get("user_instructions_data_visualization"),
            "data_raw": state.get("data_wrangled") if state.get("data_wrangled") else state.get("data_raw"),
            "max_retries": state.get("max_retries"),
            "retry_count": state.get("retry_count"),
        })

        return {
            "messages": response.get("messages"),
            "data_visualization_function": response.get("data_visualization_function"),
            "plotly_graph": response.get("plotly_graph"),
            "plotly_error": response.get("data_visualization_error"),
        }

    def route_printer(state: PrimaryState) -> Dict[str, Any]:
        """
        Print the final routing decision.

        Parameters
        ----------
        state : PrimaryState
            The current state with routing decision.

        Returns
        -------
        Dict[str, Any]
            Empty dict (no state updates).
        """
        print("---ROUTE PRINTER---")
        print(f"    Route: {state.get('routing_preprocessor_decision')}")
        print("---END---")
        return {}
    
    workflow = StateGraph(PrimaryState)
    
    workflow.add_node("routing_preprocessor", preprocess_routing)
    workflow.add_node("data_wrangling_agent", invoke_data_wrangling_agent)
    workflow.add_node("data_visualization_agent", invoke_data_visualization_agent)
    workflow.add_node("route_printer", route_printer)

    workflow.add_edge(START, "routing_preprocessor")
    workflow.add_edge("routing_preprocessor", "data_wrangling_agent")
    
    workflow.add_conditional_edges(
        "data_wrangling_agent", 
        router_chart_or_table,
        {
            "chart": "data_visualization_agent",
            "table": "route_printer"
        }
    )
    
    workflow.add_edge("data_visualization_agent", "route_printer")
    workflow.add_edge("route_printer", END)

    app = workflow.compile(
        checkpointer=checkpointer, 
        name=AGENT_NAME
    )
    
    return app
