# 6.3 LangGraph Exercises

These exercises will guide you through building and understanding simple LangGraph graphs, based on Module 4. You'll need `langgraph` and `langchain_core` installed.

**Exercise 1: Simple Counter Graph**

1.  **State:** Define a `TypedDict` state called `CounterState` with one key: `count` (int).
2.  **Nodes:**
    *   `increment_node(state: CounterState)`: Increments `state['count']` by 1. Returns `{"count": new_count}`.
    *   `decrement_node(state: CounterState)`: Decrements `state['count']` by 1. Returns `{"count": new_count}`.
    *   `entry_node(state: CounterState)`: Takes an initial `count` from the input (or defaults to 0) and sets it in the state. Returns `{"count": initial_count}`.
3.  **Conditional Edge Logic:**
    *   `should_continue(state: CounterState)`:
        *   If `state['count'] < 3`, return `"go_increment"`.
        *   If `state['count'] > 7`, return `"go_decrement"`.
        *   If `state['count']` is between 3 and 7 (inclusive), return `END` (from `langgraph.graph`).
4.  **Graph Construction:**
    *   Initialize `StatefulGraph(CounterState)`.
    *   Add the nodes: "entry", "increment", "decrement".
    *   Set "entry" as the entry point.
    *   From "entry", add a conditional edge to `should_continue`, mapping:
        *   `"go_increment"` to "increment"
        *   `"go_decrement"` to "decrement"
        *   `END` to `END`
    *   From "increment", add a conditional edge to `should_continue` (same mapping).
    *   From "decrement", add a conditional edge to `should_continue` (same mapping).
5.  **Compile and Run:**
    *   Compile the graph.
    *   Invoke the graph with an initial state like `{"count": 0}`. Set `{"recursion_limit": 20}` in the config. Print the final state.
    *   Invoke it with `{"count": 10}`. Print the final state.
    *   Invoke it with `{"count": 5}`. Print the final state.
    *   Use `app.stream(...)` to observe the steps for one of the runs.

**Exercise 2: Simple Question Classifier and Responder**

This exercise will simulate a very basic agent that decides how to respond based on a question type.

1.  **State:**
    ```python
    from typing import TypedDict, Optional, List, Annotated # Added List, Annotated
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage # For messages
    from langgraph.graph.message import add_messages # To append messages

    class QnAGraphState(TypedDict):
        original_question: str
        classified_type: Optional[str] # e.g., "greeting", "fact", "opinion"
        response: Optional[str]
        messages: Annotated[List[BaseMessage], add_messages]
    ```
2.  **Nodes:**
    *   `classify_question_node(state: QnAGraphState)`:
        *   Takes `state['original_question']`.
        *   Simple rule-based classification:
            *   If "hello" or "hi" in question, `classified_type` is "greeting".
            *   If "what is" or "who is" in question, `classified_type` is "fact".
            *   Otherwise, `classified_type` is "opinion".
        *   Adds the original question as a `HumanMessage` to `messages`.
        *   Returns `{"classified_type": type, "messages": [HumanMessage(content=state['original_question'])]}`.
    *   `greeting_responder_node(state: QnAGraphState)`:
        *   Sets `response` to "Hello there! How can I help you today?".
        *   Adds this response as an `AIMessage` to `messages`.
        *   Returns `{"response": ..., "messages": [AIMessage(content=...)]}`.
    *   `fact_responder_node(state: QnAGraphState)`:
        *   Sets `response` to "That's a factual question. I'd usually look that up in my knowledge base!". (No actual KB lookup for this exercise).
        *   Adds this response as an `AIMessage` to `messages`.
        *   Returns `{"response": ..., "messages": [AIMessage(content=...)]}`.
    *   `opinion_responder_node(state: QnAGraphState)`:
        *   Sets `response` to "That sounds like you're asking for an opinion. As an AI, I don't have personal opinions, but I can share common perspectives if you'd like!".
        *   Adds this response as an `AIMessage` to `messages`.
        *   Returns `{"response": ..., "messages": [AIMessage(content=...)]}`.

3.  **Conditional Edge Logic (after `classify_question_node`):**
    *   `route_after_classification(state: QnAGraphState)`:
        *   Reads `state['classified_type']`.
        *   Returns `"greeting_node"` if "greeting", `"fact_node"` if "fact", `"opinion_node"` if "opinion".

4.  **Graph Construction:**
    *   Initialize `StatefulGraph(QnAGraphState)`.
    *   Add nodes: "classifier", "greeting_node", "fact_node", "opinion_node".
    *   Set "classifier" as the entry point.
    *   Add a conditional edge from "classifier" to `route_after_classification`, mapping the outputs to the respective responder nodes.
    *   Add direct edges from "greeting_node" to `END`, "fact_node" to `END`, and "opinion_node" to `END`.
5.  **Compile and Run:**
    *   Compile the graph.
    *   Test with different questions:
        *   `{"original_question": "Hello AI!"}`
        *   `{"original_question": "What is the capital of Spain?"}`
        *   `{"original_question": "Do you think pineapple belongs on pizza?"}`
    *   For each, print the final `state['response']` and `state['messages']`.
    *   Use `app.stream(...)` for one input to see the flow.

These exercises provide a starting point. Feel free to expand on them, for example, by integrating a simple LLM call within a node in the LangGraph exercise.
