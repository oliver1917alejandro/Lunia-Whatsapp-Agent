# 5.2 LangChain & LangGraph in This Project

This project leverages LangGraph for its core agent logic and LlamaIndex (a related library often used with LangChain) for its knowledge base capabilities.

**LangGraph (`src/agents/lunia_agent_enhanced.py`):**

The `LuniaAgent` class in `lunia_agent_enhanced.py` is built around LangGraph's `StateGraph`.

*   **State (`AgentState`):** A custom state object (`AgentState` defined in `src/models/schemas.py`) is used to pass information between different processing steps (nodes) of the graph. This state likely includes:
    *   `input_message`: The user's current message.
    *   `sender_phone`: User's phone number.
    *   `response`: The agent's generated response.
    *   `intent`: The detected intent of the user's message.
    *   `conversation_history`: Past messages.
    *   Error flags and validation results.
*   **Nodes:** The agent defines several nodes, each being a method within the class:
    *   `_validate_input_node`: Checks the incoming message.
    *   `_process_message_node`: Tries to understand the intent of the message. It also calls out to `AgentServiceIntegration` to see if the message triggers a specific service action (like sending an email or booking a calendar event).
    *   `_generate_response_node`: Creates a text response. If a service action was taken by `_process_message_node` and provided a response, this node might use that. Otherwise, it generates responses for simple intents (like greetings) or indicates that a knowledge base query is needed.
    *   `_send_response_node`: Uses the `whatsapp_service` to send the generated response back to the user.
    *   `_handle_error_node`: Deals with any errors that occurred during processing.
*   **Edges:**
    *   The graph starts at `_validate_input_node`.
    *   A **conditional edge** (`_should_continue_after_validation`) determines if processing should continue to `_process_message_node` or go to `_handle_error_node`.
    *   After `_process_message_node`, it flows to `_generate_response_node`, then `_send_response_node`, and finally to `END`. Errors also lead to `END`.
*   **How it works:** When a new message comes in, an initial `AgentState` is created. The LangGraph executor then invokes the graph with this state. Each node receives the current state, performs its function (potentially modifying the state by returning a dictionary of updates), and the graph transitions to the next node based on the defined edges. This continues until an `END` state is reached.

**LlamaIndex (`src/services/knowledge_base.py`):**

The `KnowledgeBaseService` uses LlamaIndex to provide Retrieval Augmented Generation (RAG) capabilities.

*   **Indexing:** It loads documents (likely from `data/lunia_info/`) and builds a `VectorStoreIndex`. This involves:
    *   Reading text files.
    *   Splitting text into manageable chunks (implicitly done by LlamaIndex).
    *   Generating numerical embeddings for each chunk using an OpenAI embedding model (`text-embedding-3-small`).
    *   Storing these chunks and their embeddings in a vector store (persisted on disk in `Config.VECTOR_STORE_DIR`).
*   **Querying:**
    *   When the `LuniaAgent` needs to answer a question from the knowledge base, it calls the `query` method of `KnowledgeBaseService`.
    *   This method takes the user's question (and potentially conversation context) and uses the LlamaIndex `RetrieverQueryEngine` to:
        1.  Convert the query into an embedding.
        2.  Search the vector store for the most similar (relevant) document chunks.
        3.  Pass these relevant chunks, along with the original query, to an OpenAI LLM (e.g., `gpt-3.5-turbo` or as configured in `Config.OPENAI_MODEL`).
        4.  The LLM generates an answer based on the provided context (the retrieved chunks).
*   **Integration with Agent:** The `LuniaAgent` calls `knowledge_base.query()` typically as a fallback if no specific intent or service action is identified, or if a general inquiry is made.

**LangChain (Implicit/Potential):**

*   **LLM Wrappers:** LlamaIndex uses its own wrappers for LLMs and embedding models (e.g., `LlamaOpenAI`, `LlamaOpenAIEmbedding`), which are conceptually similar to LangChain's wrappers. They provide a standardized interface to models like those from OpenAI.
*   **No Explicit Chains Visible (Yet):** In the reviewed files, there aren't explicit LangChain `LLMChain` or `SequentialChain` objects being directly used within the agent's primary flow. The agent's "chaining" logic is managed by LangGraph. However, it's possible that:
    *   The `KnowledgeBaseService` or `AgentServiceIntegration` could internally use LangChain chains for more complex sub-tasks (e.g., if `AgentServiceIntegration` needed to summarize a long user request before trying to extract parameters for an email).
    *   Future enhancements might introduce LangChain chains as tools or specific nodes within the LangGraph structure if a particular sequence of LLM calls is needed for a sub-task.

**In summary:** LangGraph orchestrates the overall agent behavior and state, while LlamaIndex (a close cousin to LangChain in the LLM ecosystem) provides the tools for building and querying a knowledge base to make the agent data-aware.
