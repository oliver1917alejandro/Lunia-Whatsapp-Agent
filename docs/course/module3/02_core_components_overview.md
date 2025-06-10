# 3.2 Core Components Overview

LangChain is built around several key components that can be chained together to create sophisticated LLM applications. Understanding these components is crucial for effectively using the framework.

Here's a high-level overview of the main components:

1.  **Schema (Not a component you directly use, but underpins interactions):**
    *   Defines the basic data structures used throughout LangChain.
    *   **Text:** The most common way to interact with LLMs.
    *   **ChatMessages:** Structured messages for chat models, including types like `HumanMessage`, `AIMessage`, `SystemMessage`, `FunctionMessage`, `ToolMessage`.
    *   **Documents:** A piece of text accompanied by metadata. Useful for data loading and indexing.
    *   **Examples:** Used for few-shot learning, providing concrete examples to the LLM.

2.  **Models (LLMs and Chat Models):**
    *   The interface to the language models themselves. LangChain provides a standard interface for various model providers.
    *   **LLMs:** Take a string as input and return a string.
        *   Example: `OpenAI`, `HuggingFacePipeline`.
    *   **Chat Models:** Take a list of chat messages as input and return a chat message. Generally more powerful for conversational tasks.
        *   Example: `ChatOpenAI`, `ChatAnthropic`.

3.  **Prompts:**
    *   Tools for constructing and managing the input to the models. Crafting good prompts is key to getting good results from LLMs.
    *   **Prompt Templates:** Parameterized templates for generating prompts. (e.g., "Tell me a joke about {topic}").
    *   **Chat Prompt Templates:** Specifically for chat models, managing sequences of `ChatMessage` templates.
    *   **Example Selectors:** For dynamically selecting few-shot examples to include in the prompt.
    *   **Output Parsers:** Structure the LLM's response (e.g., parse a string into JSON, or ensure a certain format).

4.  **Chains:**
    *   Allow for sequences of calls, either to an LLM or to other utilities. They are the "verbs" of LangChain, enabling more complex application logic.
    *   **LLMChain:** The most basic chain, combining a model and a prompt template.
    *   **Sequential Chains:** Run multiple chains in sequence, with the output of one being the input to the next.
    *   **Router Chains:** Dynamically select which chain to run next based on the input.
    *   Many specialized chains for tasks like question answering, summarization, etc.

5.  **Indexes and Retrievers:**
    *   Enable LLMs to work with external data, overcoming knowledge cutoffs and providing domain-specific information.
    *   **Document Loaders:** Load documents from various sources (text files, PDFs, web pages, databases, etc.).
    *   **Text Splitters:** Split large documents into smaller chunks suitable for processing by LLMs.
    *   **VectorStores:** Store text chunks as numerical embeddings, allowing for efficient similarity search.
        *   Examples: FAISS, Chroma, Pinecone, Weaviate.
    *   **Retrievers:** The interface for fetching relevant documents from a VectorStore (or other sources) based on a query.
        *   Common retrieval strategy: Semantic similarity search.

6.  **Memory:**
    *   Allows chains and agents to remember previous interactions, enabling context-aware conversations and operations.
    *   **ChatMessageHistory:** Stores the sequence of chat messages.
    *   **Buffer Memory:** Keeps a buffer of recent interactions.
    *   **Summary Memory:** Creates a summary of the conversation over time.
    *   **VectorStore-backed Memory:** Stores memories in a vector store for semantic retrieval.

7.  **Agents and Tools:**
    *   Enable LLMs to interact with their environment and make decisions.
    *   **Tools:** Functions that an agent can use (e.g., Google Search, Python REPL, database query, custom APIs). LangChain provides many pre-built tools and makes it easy to define custom ones.
    *   **Agents:** An LLM acting as a "reasoning engine" that decides which tool (if any) to use based on the input. It makes a sequence of decisions until a task is accomplished or a limit is reached.
    *   **Agent Executor:** The runtime environment for an agent, which calls the agent to get actions and executes those actions (calling tools).

**How They Fit Together (A Simple Example - Question Answering over Documents):**

1.  **Document Loaders** load your documents.
2.  **Text Splitters** break them into manageable chunks.
3.  These chunks are embedded and stored in a **VectorStore** (this is the "indexing" part).
4.  A user asks a question (this becomes the input to a **Prompt Template**).
5.  A **Retriever** fetches relevant document chunks from the VectorStore based on the question.
6.  The question and the retrieved chunks are formatted by the **Prompt Template**.
7.  The formatted prompt is sent to an **LLM** (or **Chat Model**) via a **Chain** (e.g., `RetrievalQA` chain).
8.  The LLM generates an answer based on the provided context.
9.  Optionally, **Memory** can be used to remember the conversation history for follow-up questions.

This modular design allows developers to swap out components, customize them, and combine them in novel ways. For instance, you could use a different LLM, a different vector store, or a custom prompt template without having to rewrite the entire application.

Each of these core components will be explored in more detail in the subsequent sections of this module.
