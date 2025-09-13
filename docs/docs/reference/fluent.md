# FluentNode

FluentNode provides a more intuitive and expressive API for building LangGraph workflows using operator overloading. It allows you to construct workflows using the `>>` operator, making the code more readable and natural.

## Overview

The fluent API consists of two main classes:
- **FluentNode**: Individual workflow nodes with operator overloading support
- **FluentWorkflow**: Workflow builder that manages FluentNode instances

## Quick Start

```python
from typing import TypedDict
from langgraph.graph.fluent import FluentNode, FluentWorkflow

# Define state schema
class WorkflowState(TypedDict):
    messages: list
    current_step: str

# Define node functions
def start_node(state: WorkflowState) -> WorkflowState:
    return {"messages": ["Starting workflow"], "current_step": "start"}

def process_node(state: WorkflowState) -> WorkflowState:
    state["messages"].append("Processing data")
    state["current_step"] = "process"
    return state

def end_node(state: WorkflowState) -> WorkflowState:
    state["messages"].append("Workflow complete")
    state["current_step"] = "end"
    return state

# Create workflow using fluent API
workflow = FluentWorkflow(WorkflowState)

# Create and chain nodes
start = FluentNode("start").with_function(start_node)
process = FluentNode("process").with_function(process_node)
end = FluentNode("end").with_function(end_node)

# Build workflow with operator chaining
workflow >> start >> process >> end >> "END"

# Set entry point and compile
workflow.set_entry_point("start")
app = workflow.compile()

# Run the workflow
result = app.invoke({"messages": [], "current_step": ""})
```

## FluentNode Class

### Constructor

```python
FluentNode(name: str)
```

Creates a new FluentNode with the specified name.

**Parameters:**
- `name` (str): Unique identifier for the node

### Methods

#### `with_function(func: Callable) -> FluentNode`

Assigns a function to the node using method chaining.

**Parameters:**
- `func` (Callable): The function to execute when the node is activated

**Returns:**
- The FluentNode instance for method chaining

**Example:**
```python
node = FluentNode("my_node").with_function(my_function)
```

#### `__rshift__(other: Union[FluentNode, str]) -> Union[FluentNode, FluentNode]`

Creates an edge from this node to another node or endpoint using the `>>` operator.

**Parameters:**
- `other` (Union[FluentNode, str]): Target node or endpoint (like "END")

**Returns:**
- The target node for chaining, or self if targeting an endpoint

**Examples:**
```python
# Chain multiple nodes
node1 >> node2 >> node3 >> "END"

# Single edge
start_node >> end_node

# Edge to END
final_node >> "END"
```

### Properties

- `name` (str): The unique name of the node
- `function` (Optional[Callable]): The function assigned to the node

## FluentWorkflow Class

### Constructor

```python
FluentWorkflow(state_schema)
```

Creates a new FluentWorkflow with the specified state schema.

**Parameters:**
- `state_schema`: TypedDict or similar schema defining the workflow state

### Methods

#### `__rshift__(node: FluentNode) -> FluentNode`

Adds a node to the workflow using the `>>` operator.

**Parameters:**
- `node` (FluentNode): The node to add to the workflow

**Returns:**
- The added node for method chaining

**Example:**
```python
workflow >> node1 >> node2
```

#### `add_node(node: FluentNode) -> FluentWorkflow`

Alternative method to add nodes without using operators.

**Parameters:**
- `node` (FluentNode): The node to add

**Returns:**
- The workflow instance for method chaining

#### `set_entry_point(node_name_or_node: Union[str, FluentNode]) -> FluentWorkflow`

Sets the entry point for the workflow.

**Parameters:**
- `node_name_or_node` (Union[str, FluentNode]): Node name or FluentNode instance

**Returns:**
- The workflow instance for method chaining

**Example:**
```python
workflow.set_entry_point("start")
# or
workflow.set_entry_point(start_node)
```

#### `add_conditional_edges(source, condition_func, mapping) -> FluentWorkflow`

Adds conditional edges with support for FluentNode objects.

**Parameters:**
- `source` (Union[str, FluentNode]): Source node
- `condition_func` (Callable): Function that returns the condition key
- `mapping` (Dict): Maps condition keys to target nodes

**Example:**
```python
def route_condition(state):
    return "process" if state["data"] else "skip"

workflow.add_conditional_edges(
    start_node,
    route_condition,
    {
        "process": process_node,
        "skip": end_node
    }
)
```

#### `get_node(name: str) -> Optional[FluentNode]`

Retrieves a node by name.

**Parameters:**
- `name` (str): Name of the node

**Returns:**
- FluentNode instance if found, None otherwise

#### `compile(**kwargs) -> Any`

Compiles the workflow into an executable LangGraph application.

**Parameters:**
- `**kwargs`: Additional arguments passed to the underlying graph compile method

**Returns:**
- Compiled workflow application

### Properties

- `graph` (StateGraph): The underlying LangGraph StateGraph instance
- `nodes` (Dict[str, FluentNode]): Dictionary of all nodes in the workflow

## Convenience Functions

### `create_workflow(state_schema) -> FluentWorkflow`

Creates a new FluentWorkflow instance.

**Parameters:**
- `state_schema`: The state schema for the workflow

**Returns:**
- New FluentWorkflow instance

**Example:**
```python
workflow = create_workflow(MyState)
```

## Advanced Examples

### Conditional Workflows

```python
from typing import TypedDict
from langgraph.graph.fluent import FluentNode, FluentWorkflow

class ConditionalState(TypedDict):
    data: str
    should_process: bool
    result: str

def check_condition(state: ConditionalState) -> ConditionalState:
    state["should_process"] = len(state["data"]) > 5
    return state

def process_data(state: ConditionalState) -> ConditionalState:
    state["result"] = f"Processed: {state['data'].upper()}"
    return state

def skip_processing(state: ConditionalState) -> ConditionalState:
    state["result"] = f"Skipped: {state['data']}"
    return state

def route_decision(state: ConditionalState) -> str:
    return "process" if state["should_process"] else "skip"

# Build workflow
workflow = FluentWorkflow(ConditionalState)

check = FluentNode("check").with_function(check_condition)
process = FluentNode("process").with_function(process_data)
skip = FluentNode("skip").with_function(skip_processing)

# Add nodes and basic flow
workflow >> check
workflow >> process >> "END"
workflow >> skip >> "END"

# Add conditional routing
workflow.add_conditional_edges(
    check,
    route_decision,
    {
        "process": process,
        "skip": skip
    }
)

workflow.set_entry_point("check")
app = workflow.compile()
```

### Complex Workflow Patterns

```python
from typing import TypedDict, List
from langgraph.graph.fluent import FluentNode, FluentWorkflow

class ProcessingState(TypedDict):
    items: List[str]
    processed_items: List[str]
    current_item: str
    completed: bool

def initialize(state: ProcessingState) -> ProcessingState:
    return {
        **state,
        "processed_items": [],
        "current_item": "",
        "completed": False
    }

def get_next_item(state: ProcessingState) -> ProcessingState:
    if state["items"]:
        state["current_item"] = state["items"].pop(0)
    else:
        state["completed"] = True
    return state

def process_item(state: ProcessingState) -> ProcessingState:
    processed = f"PROCESSED_{state['current_item']}"
    state["processed_items"].append(processed)
    return state

def should_continue(state: ProcessingState) -> str:
    return "continue" if not state["completed"] else "finish"

# Build processing loop
workflow = FluentWorkflow(ProcessingState)

init = FluentNode("init").with_function(initialize)
get_item = FluentNode("get_item").with_function(get_next_item)
process = FluentNode("process").with_function(process_item)

# Create workflow with loop
workflow >> init >> get_item
workflow >> process >> get_item  # Loop back

# Add conditional edges for loop control
workflow.add_conditional_edges(
    get_item,
    should_continue,
    {
        "continue": process,
        "finish": "END"
    }
)

workflow.set_entry_point("init")
app = workflow.compile()
```

## Best Practices

### 1. Method Chaining
Always use method chaining when creating nodes:
```python
# Good
node = FluentNode("process").with_function(process_func)

# Avoid
node = FluentNode("process")
node.function = process_func  # Direct assignment
```

### 2. Operator Chaining
Use the `>>` operator for clean, readable workflow construction:
```python
# Good - clear flow
workflow >> start >> process >> validate >> end >> "END"

# Less readable
workflow.add_node(start)
workflow.add_node(process)
# ... more add_node calls
```

### 3. Error Handling
Always set entry points before compilation:
```python
# Good
workflow.set_entry_point("start")
app = workflow.compile()

# Will raise ValueError
app = workflow.compile()  # No entry point set
```

### 4. State Schema Design
Use clear, descriptive TypedDict schemas:
```python
# Good
class ProcessingState(TypedDict):
    input_data: str
    processing_step: str
    output_data: str
    error_message: Optional[str]

# Less clear
class State(TypedDict):
    data: Any
    step: int
```

## Migration from Standard LangGraph

Converting existing LangGraph workflows to use FluentNode is straightforward:

### Before (Standard LangGraph):
```python
from langgraph.graph import StateGraph, END

graph = StateGraph(MyState)
graph.add_node("start", start_function)
graph.add_node("process", process_function)
graph.add_edge("start", "process")
graph.add_edge("process", END)
graph.set_entry_point("start")
app = graph.compile()
```

### After (FluentNode):
```python
from langgraph.graph.fluent import FluentNode, FluentWorkflow

workflow = FluentWorkflow(MyState)
start = FluentNode("start").with_function(start_function)
process = FluentNode("process").with_function(process_function)

workflow >> start >> process >> "END"
workflow.set_entry_point("start")
app = workflow.compile()
```

## API Reference Summary

| Class/Function | Purpose |
|----------------|---------|
| `FluentNode` | Individual workflow node with operator overloading |
| `FluentWorkflow` | Workflow builder that manages FluentNode instances |
| `create_workflow()` | Convenience function to create new workflows |

| Operator | Purpose |
|----------|---------|
| `>>` | Add nodes to workflow or create edges between nodes |

The FluentNode API provides a more expressive and intuitive way to build LangGraph workflows while maintaining full compatibility with the underlying LangGraph system.
