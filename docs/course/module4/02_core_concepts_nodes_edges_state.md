# 4.2 Core Concepts in LangGraph

LangGraph introduces a few core concepts to define and manage cyclical, stateful computations.

### 1. State (StatefulGraph)

The **State** is a central piece of LangGraph. It's a data structure (typically a Pydantic `BaseModel` or a `TypedDict`) that holds all the information relevant to the current execution of the graph.
*   Each node in the graph can read from and write to this shared state.
*   The state is persistent across the execution of the graph, allowing information to be passed and modified through multiple steps and cycles.
*   You define the schema of your state, specifying what kind of data it holds (e.g., user input, intermediate results, conversation history, number of retries).

**Example State Definition (using TypedDict):**
```python
from typing import TypedDict, List, Annotated
from langgraph.graph.message import add_messages # Helper to append messages

# Define the state for our graph
class MyGraphState(TypedDict):
    input_query: str
    # `add_messages` is a special function that ensures new messages are appended to the list
    # rather than overwriting it. This is useful for chat history.
    messages: Annotated[List[any], add_messages]
    intermediate_results: List[str]
    final_answer: str
    # Add other fields as needed for your application's state
```

### 2. Nodes

**Nodes** are the fundamental units of computation in a LangGraph. Each node represents a step or a function that performs some work.
*   A node can be any Python callable (a function, a LangChain Runnable like an LLMChain or an Agent).
*   When a node is executed, it receives the current `State` as input.
*   It can perform operations (e.g., call an LLM, run a tool, process data) and then return an update to the `State`. This update is a dictionary where keys match the fields in your `State` schema. LangGraph then merges this update into the main state.

**Example Node Function:**
```python
from langchain_core.messages import HumanMessage # Added for the example

def my_node_function(state: MyGraphState) -> dict:
    # Access data from the current state
    query = state["input_query"]
    current_messages = state["messages"]
    print(f"Node executing with query: {query}")

    # Perform some action (e.g., call an LLM, a tool, or just process data)
    result = f"Processed result for query: '{query}'"
    new_message_to_user = HumanMessage(content=f"Based on your query '{query}', I found this: {result}")


    # Return a dictionary to update the state
    return {
        "intermediate_results": [result], # This would overwrite existing intermediate_results
                                         # To append, you'd typically read state['intermediate_results'] first and extend it
        "messages": [new_message_to_user] # add_messages will append this
    }
```

### 3. Edges

**Edges** define the connections between nodes, dictating the flow of execution. After a node completes, LangGraph uses edges to determine which node to execute next.

*   **Standard Edges:** A simple edge connects one node to another. If node A is connected to node B, then after A finishes, B will run.
*   **Conditional Edges:** These are more powerful. A conditional edge takes the current `State` as input and returns the *name* of the next node to execute (or a special value to end the graph). This allows for dynamic routing and loops based on the state.
    *   You provide a function that inspects the state and decides where to go next.
    *   The function returns the string name of the next node or `END` (a special constant from `langgraph.graph`).

**Example Conditional Edge Function:**
```python
from langgraph.graph import END # Special marker to end the graph

def decide_next_node(state: MyGraphState) -> str:
    if "final_answer_found" in state.get("intermediate_results", []): # Example condition
        return END # End the graph
    elif len(state.get("messages", [])) > 5: # Another example condition
        return "final_summary_node" # Go to a specific node
    else:
        return "another_processing_node" # Go to a different node
```

### 4. Graph (StatefulGraph)

The **Graph** (specifically `StatefulGraph` or `MessageGraph` for chat applications) is what ties everything together.
*   You instantiate a graph with your defined `State` schema.
*   You add nodes to the graph, giving each a unique name.
*   You define the entry point for the graph (the first node to execute).
*   You add edges to connect the nodes, including conditional edges for complex logic.
*   Once defined, you compile the graph into a runnable LangChain object.
*   You can then `invoke` or `stream` the graph with an initial input, and it will manage the state and execute nodes according to the defined edges.

**Building the Graph (Conceptual):**
```python
from langgraph.graph import StatefulGraph, END
from langchain_core.messages import SystemMessage, HumanMessage # For example messages

# Assume MyGraphState, my_node_function, decide_next_node are defined as above
# For the sake of a runnable concept, let's define placeholder functions
def some_other_node_function(state: MyGraphState) -> dict:
    print("Executing some_other_node_function")
    # Example: append to intermediate_results instead of overwriting
    new_results = state.get("intermediate_results", []) + ["result from other_node"]
    return {"intermediate_results": new_results, "messages": [HumanMessage(content="Processed by other_node.")]}

def summary_node_function(state: MyGraphState) -> dict:
    print("Executing summary_node_function")
    final_summary = f"Final summary based on: {state.get('intermediate_results', [])}"
    return {"final_answer": final_summary, "messages": [SystemMessage(content=final_summary)]}


# 1. Initialize the graph with the state schema
workflow = StatefulGraph(MyGraphState)

# 2. Add nodes
workflow.add_node("start_node", my_node_function)
workflow.add_node("another_processing_node", some_other_node_function)
workflow.add_node("final_summary_node", summary_node_function)

# 3. Set the entry point
workflow.set_entry_point("start_node")

# 4. Add edges
workflow.add_edge("start_node", "another_processing_node") # Simple edge

# Add a conditional edge from 'another_processing_node'
workflow.add_conditional_edges(
    "another_processing_node",
    decide_next_node, # The function that decides where to go
    { # A dictionary mapping the return value of decide_next_node to actual node names
        "final_summary_node": "final_summary_node",
        "another_processing_node": "another_processing_node", # Loop back
        END: END # Map the END signal
    }
)
workflow.add_edge("final_summary_node", END) # Ensure the summary node can end the graph

# 5. Compile the graph
app = workflow.compile()

# 6. Run (invoke) the graph
# Initial input for the graph should match the structure expected by the entry point node
# and how it updates the state. Often, it's a dictionary matching parts of the state.
initial_input = {"input_query": "Tell me about LangGraph.", "messages": [SystemMessage(content="System init.")]}
# Example of streaming to see step-by-step execution
# for s_chunk in app.stream(initial_input, {"recursion_limit": 10}):
#     print(f"Stream chunk: {s_chunk}")
#     print("-" * 10)

# Example of invoking to get the final state
# final_state = app.invoke(initial_input, {"recursion_limit": 10})
# print(f"
Final State: {final_state}")
```

These core components—State, Nodes, and Edges—allow you to construct sophisticated, stateful, and cyclical applications with LangGraph.
