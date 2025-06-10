# 3.7 Memory

By default, Chains and Agents in LangChain are stateless. This means each incoming query or request is processed independently, without any knowledge of previous interactions. **Memory** is the component that allows Chains and Agents to remember past interactions, enabling context-aware conversations and more sophisticated applications.

**Why is Memory Important?**

*   **Conversational Context:** For chatbots, memory is essential to understand follow-up questions, refer to earlier parts of the conversation, and maintain a natural flow.
*   **User Personalization:** Remembering user preferences or past inputs can help tailor responses.
*   **Complex Task Execution:** Some tasks require accumulating information over multiple steps.

LangChain provides various types of memory, each suited for different needs. Memory components typically store and manage `ChatMessage` objects.

### Key Concepts:

*   **`ChatMessageHistory`:** The core class for storing sequences of chat messages. It can be backed by various stores (in-memory, file, database, etc.).
*   **Memory Variables:** When integrating memory with a chain, the prompt template will usually expect specific input variables that the memory component will populate. Common memory variables include:
    *   `history`: Contains the formatted chat history.
    *   `input`: The current user input (often implicitly handled).
*   **Return Messages:** Some memory types can be configured to return the history as a list of `ChatMessage` objects, which is useful for chat models.

### Common Memory Types:

1.  **`ConversationBufferMemory`:**
    *   Keeps a buffer of the most recent messages in the conversation.
    *   Simple and widely used.
    *   The entire buffer is passed as context to the LLM.

    ```python
    # Required: pip install langchain-openai
    import os
    # os.environ["OPENAI_API_KEY"] = "your_actual_api_key"

    from langchain_openai import OpenAI
    from langchain.chains import ConversationChain # A chain specifically designed for conversation
    from langchain.memory import ConversationBufferMemory
    from langchain_core.prompts import PromptTemplate

    # Initialize LLM
    try:
        llm = OpenAI(model_name="gpt-3.5-turbo-instruct", temperature=0) # Assuming API key is set

        # Define a prompt template that expects a 'history' variable and 'input'
        # ConversationChain has a default prompt, but we can customize it
        template = """You are a friendly conversational AI.

        Current conversation:
        {history}
        Human: {input}
        AI:"""
        prompt = PromptTemplate(input_variables=["history", "input"], template=template)

        # Initialize ConversationBufferMemory
        # memory_key="history" tells the chain to use this key for memory variables
        memory = ConversationBufferMemory(memory_key="history")

        # Initialize ConversationChain
        # verbose=True helps see what the chain is doing
        conversation_chain = ConversationChain(
            llm=llm,
            prompt=prompt, # Using our custom prompt
            memory=memory,
            verbose=True
        )

        print("--- ConversationBufferMemory Example ---")
        response1 = conversation_chain.invoke({"input": "Hi there! My name is Sam."})
        print(f"AI: {response1['response']}")

        response2 = conversation_chain.invoke({"input": "What is my name?"})
        print(f"AI: {response2['response']}")

        response3 = conversation_chain.invoke({"input": "What was the first thing I said?"})
        print(f"AI: {response3['response']}")

        print("\nFinal Memory State:")
        print(memory.load_memory_variables({})) # See what's stored

    except Exception as e:
        print(f"Error in ConversationBufferMemory example: {e}")
        print("Ensure OpenAI API key is set.")
    ```
    *Output (will vary slightly):*
    ```
    --- ConversationBufferMemory Example ---

    > Entering new ConversationChain chain...
    Prompt after formatting:
    You are a friendly conversational AI.

    Current conversation:

    Human: Hi there! My name is Sam.
    AI:
    > Finished chain.
    AI:  Hello Sam! It's nice to meet you. How can I help you today?

    > Entering new ConversationChain chain...
    Prompt after formatting:
    You are a friendly conversational AI.

    Current conversation:
    Human: Hi there! My name is Sam.
    AI:  Hello Sam! It's nice to meet you. How can I help you today?
    Human: What is my name?
    AI:
    > Finished chain.
    AI:  Your name is Sam.

    > Entering new ConversationChain chain...
    Prompt after formatting:
    You are a friendly conversational AI.

    Current conversation:
    Human: Hi there! My name is Sam.
    AI:  Hello Sam! It's nice to meet you. How can I help you today?
    Human: What is my name?
    AI:  Your name is Sam.
    Human: What was the first thing I said?
    AI:
    > Finished chain.
    AI:  The first thing you said was "Hi there! My name is Sam."

    Final Memory State:
    {'history': "Human: Hi there! My name is Sam.\nAI:  Hello Sam! It's nice to meet you. How can I help you today?\nHuman: What is my name?\nAI:  Your name is Sam.\nHuman: What was the first thing I said?\nAI:  The first thing you said was \"Hi there! My name is Sam.\""}
    ```

2.  **`ConversationBufferWindowMemory`:**
    *   Similar to `ConversationBufferMemory` but keeps only the last `k` interactions.
    *   Useful for preventing the conversation history from growing too large and exceeding token limits.

    ```python
    from langchain.memory import ConversationBufferWindowMemory

    # memory_window = ConversationBufferWindowMemory(k=2, memory_key="history")
    # ... rest of the setup is similar to ConversationBufferMemory ...
    # If used in the chain above, it would only remember the last 2 human/AI message pairs.
    ```

3.  **`ConversationSummaryMemory`:**
    *   Instead of storing all messages, it creates a summary of the conversation as it progresses.
    *   The summary is passed as context to the LLM.
    *   Requires an LLM to generate the summaries.

    ```python
    from langchain.memory import ConversationSummaryMemory

    # summary_memory = ConversationSummaryMemory(llm=llm, memory_key="history") # llm is needed for summarization
    # ...
    # When this memory is used, the {history} variable in the prompt will contain a summary.
    ```

4.  **`ConversationSummaryBufferMemory`:**
    *   A combination of buffer and summary. It keeps a buffer of recent messages and also compiles older messages into a summary.
    *   Balances immediate context with long-term context while managing token limits.
    *   `max_token_limit` parameter controls when to summarize.

    ```python
    from langchain.memory import ConversationSummaryBufferMemory

    # summary_buffer_memory = ConversationSummaryBufferMemory(
    #     llm=llm,
    #     max_token_limit=100, # Example: Summarize when buffer exceeds 100 tokens
    #     memory_key="history"
    # )
    # ...
    ```

5.  **`ConversationKGMemory` (Knowledge Graph Memory):**
    *   Extracts entities and their relationships from the conversation and stores them in a knowledge graph.
    *   The knowledge graph can then be used to inform the LLM.
    *   More complex but can provide structured memory.

6.  **VectorStore-backed Memory (e.g., `VectorStoreRetrieverMemory`):**
    *   Stores memories (embeddings of conversation snippets) in a VectorStore.
    *   Retrieves relevant past interactions based on semantic similarity to the current input.
    *   Useful for recalling specific information from long conversations.

### Using Memory with Chat Models

When using memory with Chat Models (which expect a list of `ChatMessage` objects), you typically set `return_messages=True` in the memory component. This ensures the memory provides the history as a list of `HumanMessage` and `AIMessage` objects.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain # LLMChain can also be used with ChatModels

# Initialize Chat Model
try:
    chat_llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0) # Assuming API key

    # Prompt for chat models, using MessagesPlaceholder for history
    chat_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template("You are a helpful chatbot having a conversation."),
        MessagesPlaceholder(variable_name="chat_history"), # Where the memory will inject messages
        HumanMessagePromptTemplate.from_template("{user_input}")
    ])

    # Memory that returns messages
    # For chat models, memory_key often matches the MessagesPlaceholder variable_name
    chat_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    chat_conv_chain = LLMChain(
        llm=chat_llm,
        prompt=chat_prompt,
        memory=chat_memory,
        verbose=True
    )
    print("\n--- ConversationBufferMemory with Chat Model (return_messages=True) ---")
    chat_res1 = chat_conv_chain.invoke({"user_input": "Hey AI, my favorite color is blue."})
    print(f"AI: {chat_res1['text']}")

    chat_res2 = chat_conv_chain.invoke({"user_input": "What's my favorite color?"})
    print(f"AI: {chat_res2['text']}")

    print("\nFinal Chat Memory State (as messages):")
    print(chat_memory.load_memory_variables({})['chat_history'])

except Exception as e:
    print(f"Error in Chat Model Memory example: {e}")

```
*Output (will vary slightly):*
```
--- ConversationBufferMemory with Chat Model (return_messages=True) ---

> Entering new LLMChain chain...
Prompt after formatting:
System: You are a helpful chatbot having a conversation.
Human: Hey AI, my favorite color is blue.
> Finished chain.
AI: That's great to know! Blue is a very popular color. How can I help you today?

> Entering new LLMChain chain...
Prompt after formatting:
System: You are a helpful chatbot having a conversation.
Human: Hey AI, my favorite color is blue.
AI: That's great to know! Blue is a very popular color. How can I help you today?
Human: What's my favorite color?
> Finished chain.
AI: Your favorite color is blue.

Final Chat Memory State (as messages):
[HumanMessage(content='Hey AI, my favorite color is blue.'), AIMessage(content="That's great to know! Blue is a very popular color. How can I help you today?"), HumanMessage(content="What's my favorite color?"), AIMessage(content='Your favorite color is blue.')]
```

**Choosing the Right Memory:**

*   For simple chatbots: `ConversationBufferMemory` or `ConversationBufferWindowMemory`.
*   For long conversations where token limits are a concern: `ConversationSummaryMemory` or `ConversationSummaryBufferMemory`.
*   For recalling specific facts from the past: VectorStore-backed memory.
*   For applications needing structured understanding of conversation history: `ConversationKGMemory`.

Memory is a powerful tool for building more intelligent and engaging LLM applications by giving them the ability to remember and learn from past interactions.
