"""
Enhanced Node class with operator overloading for intuitive workflow building.

This module extends LangGraph with a more fluent API for workflow construction,
allowing developers to use >> operators to build workflows naturally.

Example:
    ```python
    from langgraph.graph.fluent import FluentNode, FluentWorkflow

    # Create workflow
    workflow = FluentWorkflow(StateSchema)

    # Create and add nodes
    start_node = FluentNode("start").with_function(start_func)
    process_node = FluentNode("process").with_function(process_func)

    workflow >> start_node >> process_node >> "END"

    # Compile and run
    app = workflow.compile()
    ```
"""
from typing import Callable, Any, Dict, Union, Optional, TYPE_CHECKING
from langgraph.graph import StateGraph, END

if TYPE_CHECKING:
    pass


class FluentNode:
    """
    A fluent Node class that supports operator overloading for intuitive workflow building.

    This class provides a more natural way to construct LangGraph workflows using
    the >> operator for both adding nodes to workflows and creating edges between nodes.

    Attributes:
        name (str): The unique name of the node
        function (Optional[Callable]): The function to execute when the node is activated

    Example:
        ```python
        # Create a node
        my_node = FluentNode("my_node").with_function(my_function)

        # Add to workflow
        workflow >> my_node

        # Create edges
        my_node >> other_node >> "END"
        ```
    """

    def __init__(self, name: str):
        """
        Initialize a new FluentNode.

        Args:
            name: Unique identifier for the node
        """
        self.name = name
        self.function: Optional[Callable] = None
        self._workflow: Optional['FluentWorkflow'] = None

    def with_function(self, func: Callable) -> 'FluentNode':
        """
        Set the function for this node using method chaining.

        Args:
            func: The function to execute when this node is activated

        Returns:
            Self for method chaining

        Example:
            ```python
            node = FluentNode("process").with_function(process_data)
            ```
        """
        self.function = func
        return self

    def __rshift__(self, other: Union['FluentNode', str]) -> Union['FluentNode', 'FluentNode']:
        """
        Create an edge from this node to another node or endpoint using >> operator.

        Args:
            other: Target node (FluentNode) or endpoint (string like "END")

        Returns:
            The target node for chaining, or self if targeting an endpoint

        Raises:
            ValueError: If node is not added to a workflow or target is invalid

        Example:
            ```python
            # Chain nodes
            node1 >> node2 >> node3 >> "END"

            # Single edge
            start_node >> end_node
            ```
        """
        if self._workflow is None:
            raise ValueError(f"Node '{self.name}' must be added to a workflow before creating edges")

        if isinstance(other, FluentNode):
            if other._workflow != self._workflow:
                raise ValueError("Both nodes must belong to the same workflow")
            self._workflow._graph.add_edge(self.name, other.name)
            return other
        elif isinstance(other, str):
            # Support for END or other string constants
            if other == "END" or other == END:
                self._workflow._graph.add_edge(self.name, END)
            else:
                self._workflow._graph.add_edge(self.name, other)
            return self
        else:
            raise ValueError("Can only create edges to other FluentNode instances or string endpoints")

    def __str__(self) -> str:
        """String representation of the node."""
        return f"FluentNode({self.name})"

    def __repr__(self) -> str:
        """Detailed string representation of the node."""
        func_name = self.function.__name__ if self.function else None
        return f"FluentNode(name='{self.name}', function={func_name})"


class FluentWorkflow:
    """
    Enhanced workflow builder with operator overloading support for LangGraph.

    This class extends the standard LangGraph StateGraph with a more intuitive API
    that allows for fluent workflow construction using operator overloading.

    Attributes:
        _graph (StateGraph): The underlying LangGraph StateGraph instance
        _nodes (Dict[str, FluentNode]): Dictionary of nodes added to the workflow
        _entry_point (Optional[str]): Name of the entry point node

    Example:
        ```python
        from typing import TypedDict

        class MyState(TypedDict):
            data: str
            step: int

        # Create workflow
        workflow = FluentWorkflow(MyState)

        # Create and add nodes
        start = FluentNode("start").with_function(start_func)
        process = FluentNode("process").with_function(process_func)

        workflow >> start >> process >> "END"

        # Set entry point and compile
        workflow.set_entry_point("start")
        app = workflow.compile()
        ```
    """

    def __init__(self, state_schema):
        """
        Initialize a new FluentWorkflow.

        Args:
            state_schema: The TypedDict or similar schema defining the workflow state
        """
        self._graph = StateGraph(state_schema)
        self._nodes: Dict[str, FluentNode] = {}
        self._entry_point: Optional[str] = None

    def __rshift__(self, node: FluentNode) -> FluentNode:
        """
        Add a node to the workflow using >> operator.

        Args:
            node: FluentNode instance to add to the workflow

        Returns:
            The added node for chaining

        Raises:
            ValueError: If the input is not a FluentNode or if the node has no function

        Example:
            ```python
            workflow >> node1 >> node2
            ```
        """
        if not isinstance(node, FluentNode):
            raise ValueError("Can only add FluentNode instances to workflow")

        if node.function is None:
            raise ValueError(f"FluentNode '{node.name}' must have a function assigned before adding to workflow")

        # Add to internal tracking
        self._nodes[node.name] = node
        node._workflow = self

        # Add to underlying LangGraph
        self._graph.add_node(node.name, node.function)

        return node

    def add_node(self, node: FluentNode) -> 'FluentWorkflow':
        """
        Alternative method to add nodes (non-operator version).

        Args:
            node: FluentNode instance to add

        Returns:
            Self for method chaining
        """
        self >> node
        return self

    def set_entry_point(self, node_name_or_node: Union[str, FluentNode]) -> 'FluentWorkflow':
        """
        Set the entry point for the workflow.

        Args:
            node_name_or_node: Node name (string) or FluentNode instance

        Returns:
            Self for method chaining

        Raises:
            ValueError: If the specified node is not found in the workflow
        """
        if isinstance(node_name_or_node, FluentNode):
            entry_name = node_name_or_node.name
        else:
            entry_name = node_name_or_node

        if entry_name not in self._nodes:
            raise ValueError(f"Node '{entry_name}' not found in workflow. Available nodes: {list(self._nodes.keys())}")

        self._entry_point = entry_name
        self._graph.set_entry_point(entry_name)
        return self

    def add_conditional_edges(
        self,
        source: Union[str, FluentNode],
        condition_func: Callable,
        mapping: Dict[str, Union[str, FluentNode]]
    ) -> 'FluentWorkflow':
        """
        Add conditional edges with support for FluentNode objects.

        Args:
            source: Source node (string name or FluentNode)
            condition_func: Function that returns the condition key
            mapping: Dictionary mapping condition keys to target nodes

        Returns:
            Self for method chaining
        """
        if isinstance(source, FluentNode):
            source_name = source.name
        else:
            source_name = source

        # Convert FluentNode objects in mapping to their names
        converted_mapping = {}
        for key, value in mapping.items():
            if isinstance(value, FluentNode):
                converted_mapping[key] = value.name
            else:
                converted_mapping[key] = value

        self._graph.add_conditional_edges(source_name, condition_func, converted_mapping)
        return self

    def get_node(self, name: str) -> Optional[FluentNode]:
        """
        Get a node by name.

        Args:
            name: Name of the node to retrieve

        Returns:
            FluentNode instance if found, None otherwise
        """
        return self._nodes.get(name)

    def compile(self, **kwargs) -> Any:
        """
        Compile the workflow into an executable LangGraph application.

        Args:
            **kwargs: Additional arguments passed to the underlying graph compile method

        Returns:
            Compiled workflow application

        Raises:
            ValueError: If no entry point has been set
        """
        if not self._entry_point:
            raise ValueError("Entry point must be set before compiling. Use set_entry_point() method.")
        return self._graph.compile(**kwargs)

    @property
    def graph(self) -> StateGraph:
        """Get the underlying LangGraph StateGraph instance."""
        return self._graph

    @property
    def nodes(self) -> Dict[str, FluentNode]:
        """Get a dictionary of all nodes in the workflow."""
        return self._nodes.copy()

    def __str__(self) -> str:
        """String representation of the workflow."""
        return f"FluentWorkflow(nodes={list(self._nodes.keys())}, entry_point={self._entry_point})"

    def __repr__(self) -> str:
        """Detailed string representation of the workflow."""
        return f"FluentWorkflow(nodes={len(self._nodes)}, entry_point='{self._entry_point}')"


# Convenience function to create a new workflow builder
def create_workflow(state_schema) -> FluentWorkflow:
    """
    Create a new FluentWorkflow instance.

    Args:
        state_schema: The TypedDict or similar schema defining the workflow state

    Returns:
        New FluentWorkflow instance

    Example:
        ```python
        from typing import TypedDict

        class MyState(TypedDict):
            messages: list
            step: str

        workflow = create_workflow(MyState)
        ```
    """
    return FluentWorkflow(state_schema)


__all__ = ["FluentNode", "FluentWorkflow", "create_workflow"]
