# 4.3 Building a Simple LangGraph Example

Let's build a very simple LangGraph that demonstrates the core concepts: state, nodes, and conditional edges.

Our example graph will:
1.  Take an initial number.
2.  Have a node that adds 1 to the number.
3.  Have a node that subtracts 1 from the number.
4.  Use a conditional edge to decide whether to add or subtract based on whether the number is currently less than 5 or not.
5.  End when the number reaches 5.

**1. Define the State**

The state will hold the current number.

```python
from typing import TypedDict, Annotated, List
# from langgraph.graph.message import add_messages # Not used for messages here
from langgraph.graph import END, StatefulGraph

class NumberGraphState(TypedDict):
    current_number: int
    history: List[str] # To track operations
```

**2. Define Nodes**

We need nodes to add, subtract, and potentially a node to log the start/end.

```python
def start_node(state: NumberGraphState) -> dict:
    initial_number = state.get("current_number", 0) # Get from input or default
    return {
        "current_number": initial_number,
        "history": [f"Started with {initial_number}"]
    }

def add_one_node(state: NumberGraphState) -> dict:
    current_num = state["current_number"]
    new_num = current_num + 1
    print(f"Node: add_one_node. Current: {current_num}, New: {new_num}")
    return {
        "current_number": new_num,
        "history": state["history"] + [f"Added 1 to {current_num}, got {new_num}"]
    }

def subtract_one_node(state: NumberGraphState) -> dict:
    current_num = state["current_number"]
    new_num = current_num - 1
    print(f"Node: subtract_one_node. Current: {current_num}, New: {new_num}")
    return {
        "current_number": new_num,
        "history": state["history"] + [f"Subtracted 1 from {current_num}, got {new_num}"]
    }

# This node won't modify the number, just log the end.
def end_node_log(state: NumberGraphState) -> dict:
    final_num = state["current_number"]
    new_history = state["history"] + [f"Ended with {final_num}."]
    print(f"Node: end_node_log. Final number: {final_num}.")
    # It's good practice for the designated "END" node (or the node leading to END)
    # to not make further state changes that would trigger more logic if not handled carefully.
    # Here, we are just updating history.
    # print(f"Final state history: {new_history}") # Printing history can be verbose during streaming
    return {"history": new_history}

```

**3. Define Conditional Logic (Edges)**

This function will decide where to go after each operation, or from the start.

```python
def decide_next_step(state: NumberGraphState) -> str:
    current_num = state["current_number"]
    if current_num == 5:
        print(f"Condition: Number is {current_num}. Reached target. Routing to end_point.")
        return "end_point" # Signal to go to the end_node_log then END
    elif current_num < 5:
        print(f"Condition: Number is {current_num}. Less than 5. Routing to add_node.")
        return "add_node"
    else: # current_num > 5
        print(f"Condition: Number is {current_num}. Greater than 5. Routing to subtract_node.")
        return "subtract_node"
```

**4. Construct the Graph**

```python
# Initialize the graph
workflow = StatefulGraph(NumberGraphState)

# Add nodes
workflow.add_node("start", start_node)
workflow.add_node("add_node", add_one_node)
workflow.add_node("subtract_node", subtract_one_node)
workflow.add_node("end_point", end_node_log) # This node will connect to the actual END

# Set the entry point
workflow.set_entry_point("start")

# Add edges
# After starting, always go to decision making using the 'decide_next_step' conditional router
workflow.add_conditional_edges(
    "start",
    decide_next_step,
    { # Map return values of decide_next_step to node names
        "add_node": "add_node",
        "subtract_node": "subtract_node",
        "end_point": "end_point"
    }
)

# After adding, decide again
workflow.add_conditional_edges(
    "add_node",
    decide_next_step,
    {
        "add_node": "add_node",       # Loop back to add_node if still < 5
        "subtract_node": "subtract_node", # Should not happen if logic is correct (add only if < 5)
        "end_point": "end_point"
    }
)

# After subtracting, decide again
workflow.add_conditional_edges(
    "subtract_node",
    decide_next_step,
    {
        "add_node": "add_node",         # Should not happen if logic is correct (subtract only if > 5)
        "subtract_node": "subtract_node", # Loop back to subtract_node if still > 5
        "end_point": "end_point"
    }
)

# The 'end_point' node will be the last actual operation before finishing.
workflow.add_edge("end_point", END)


# Compile the graph
app = workflow.compile()
```

**5. Run the Graph**

```python
# Run with an initial number, e.g., 2
initial_state_input_1 = {"current_number": 2}
print(f"\n--- Running graph with initial number: 2 ---")
# Using stream to see the flow. Use invoke for just the final state.
# A recursion limit is often needed for graphs with cycles.
for s_output in app.stream(initial_state_input_1, {"recursion_limit": 15}):
    # s_output is a dictionary where keys are node names and values are the output of that node (state update)
    print(s_output)
    print("----")

# Run with an initial number, e.g., 7
initial_state_input_2 = {"current_number": 7}
print(f"\n--- Running graph with initial number: 7 ---")
for s_output in app.stream(initial_state_input_2, {"recursion_limit": 15}):
    print(s_output)
    print("----")

# Run with an initial number already at the target, e.g., 5
initial_state_input_3 = {"current_number": 5}
print(f"\n--- Running graph with initial number: 5 ---")
for s_output in app.stream(initial_state_input_3, {"recursion_limit": 15}):
    print(s_output)
    print("----")

# You can also use invoke to get just the final state:
# final_state = app.invoke(initial_state_input_1, {"recursion_limit": 15})
# print(f"
Final state for input 2: {final_state}")
```

**To actually run this:**
You would save this code as a Python file (e.g., `simple_number_graph.py`) and run it.
Ensure you have `langgraph` and `langchain-core` installed: `pip install langgraph langchain-core`

This simple example illustrates how to:
*   Define a state.
*   Create nodes that modify the state.
*   Use conditional edges to control the flow based on the state.
*   Compile and run the graph.

More complex LangGraph applications will involve nodes that are LangChain chains or agents, interacting with LLMs, tools, and data.
```
