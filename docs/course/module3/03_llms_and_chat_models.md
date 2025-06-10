# 3.3 Models: LLMs and Chat Models

At the heart of LangChain are the **Models**, which provide the interface to Large Language Models (LLMs) and Chat Models. These are the engines that generate text, answer questions, and power the reasoning capabilities of your applications.

LangChain offers a standardized interface for a wide variety of models, making it easy to switch between them or even use multiple models in a single application.

### Two Main Types of Models:

1.  **LLMs (Large Language Models):**
    *   These models take a single string as input and return a single string as output.
    *   They are often used for simpler, one-shot tasks or when a conversational history isn't strictly necessary for the immediate task.
    *   Examples: Text generation, summarization of a single piece of text, simple question answering.

2.  **Chat Models:**
    *   These models are designed for conversational interactions.
    *   They take a list of `ChatMessage` objects as input and return an `AIMessage` object as output.
    *   `ChatMessage` objects can be of different types:
        *   `SystemMessage`: Sets the context or instructions for the AI (e.g., "You are a helpful assistant that translates English to French.").
        *   `HumanMessage`: Represents a message from the user.
        *   `AIMessage`: Represents a message from the AI. It can also contain `tool_calls` when using agents.
        *   `ToolMessage`: Represents the result of a tool call made by an agent.
    *   Chat models are generally more powerful and flexible than LLMs, especially for complex tasks and maintaining context in conversations. Many newer models are primarily accessed via a chat-like interface.

### Common Interface

Both LLMs and Chat Models in LangChain share some common methods:

*   **`invoke(input, config=None, **kwargs)` / `ainvoke(input, config=None, **kwargs)`:**
    *   The primary way to call the model.
    *   `invoke`: Synchronous call.
    *   `ainvoke`: Asynchronous call (useful for concurrent operations).
    *   `input`: The input to the model (string for LLMs, list of ChatMessages for Chat Models).
    *   `config`: Optional LangChain specific configuration (e.g., for callbacks, tags).
*   **`batch(inputs, config=None, **kwargs)` / `abatch(inputs, config=None, **kwargs)`:**
    *   Calls the model on a list of inputs. More efficient than calling `invoke` multiple times.
*   **`stream(input, config=None, **kwargs)` / `astream(input, config=None, **kwargs)`:**
    *   Streams the model's response chunk by chunk, allowing for real-time output.
*   **`bind_tools(tools, **kwargs)` (Chat Models primarily):**
    *   Allows you to provide tools (functions) that the chat model can decide to call. This is fundamental for agents.

### Example: Using an LLM (OpenAI)

First, ensure you have the necessary libraries and API keys set up. For OpenAI models, you'll need the `langchain-openai` package and an OpenAI API key set as an environment variable (`OPENAI_API_KEY`).

```python
# Required: pip install langchain-openai
import os
# Ensure your OPENAI_API_KEY is set in your environment variables
# os.environ["OPENAI_API_KEY"] = "your_actual_api_key"

from langchain_openai import OpenAI

# Initialize the LLM
# temperature controls randomness (0.0 = deterministic, 1.0 = more random)
# model_name can be specified, e.g., "gpt-3.5-turbo-instruct" for newer instruct models
llm = OpenAI(model_name="gpt-3.5-turbo-instruct", temperature=0.7)

# Input prompt string
prompt_text = "What is the capital of France?"

# Invoke the LLM
try:
    response = llm.invoke(prompt_text)
    print("LLM Response:")
    print(response)
except Exception as e:
    print(f"Error invoking LLM: {e}")
    print("Please ensure your OpenAI API key is correctly set and valid.")

print("-" * 20)

# Batch invocation
prompts = [
    "What is the capital of Germany?",
    "Translate 'hello' into Spanish."
]
try:
    batch_response = llm.batch(prompts)
    print("LLM Batch Response:")
    for res in batch_response:
        print(res)
except Exception as e:
    print(f"Error in LLM batch: {e}")

print("-" * 20)

# Streaming invocation
try:
    print("LLM Streamed Response:")
    for chunk in llm.stream("Write a short poem about a cat."):
        print(chunk, end="", flush=True)
    print() # Newline after stream
except Exception as e:
    print(f"Error in LLM stream: {e}")

```
*Output (will vary slightly due to model generation):*
```
LLM Response:

The capital of France is Paris.
--------------------
LLM Batch Response:

The capital of Germany is Berlin.

Hola
--------------------
LLM Streamed Response:
In shadows deep, with eyes so green,
A feline friend, a silent queen.
With fur as soft as morning light,
She moves with grace, a calming sight.
A gentle purr, a soothing sound,
As happy dreams on paws are found.

```

### Example: Using a Chat Model (ChatOpenAI)

```python
# Required: pip install langchain-openai
import os
# os.environ["OPENAI_API_KEY"] = "your_actual_api_key"

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Initialize the Chat Model
# model_name can be "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview", etc.
chat_model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)

# Define a list of messages
messages = [
    SystemMessage(content="You are a helpful assistant that provides concise answers."),
    HumanMessage(content="What are the main benefits of using LangChain?")
]

# Invoke the Chat Model
try:
    ai_response = chat_model.invoke(messages)
    print("Chat Model Response:")
    print(f"AI: {ai_response.content}")

    # You can continue the conversation by adding the AI's response and a new human message
    messages.append(ai_response)
    messages.append(HumanMessage(content="Can you list one more benefit?"))

    continued_response = chat_model.invoke(messages)
    print("\nChat Model Continued Response:")
    print(f"AI: {continued_response.content}")

except Exception as e:
    print(f"Error invoking Chat Model: {e}")
    print("Please ensure your OpenAI API key is correctly set and valid.")

print("-" * 20)

# Streaming with Chat Model
try:
    print("Chat Model Streamed Response:")
    messages_for_stream = [
        SystemMessage(content="You are a poet."),
        HumanMessage(content="Compose a haiku about a rainy day.")
    ]
    for chunk in chat_model.stream(messages_for_stream):
        # chunk is an AIMessageChunk, access its content
        print(chunk.content, end="", flush=True)
    print()
except Exception as e:
    print(f"Error in Chat Model stream: {e}")

```
*Output (will vary slightly):*
```
Chat Model Response:
AI: LangChain offers several benefits:
1.  **Modularity and Composability:** Easily combine components to build complex applications.
2.  **Standardized Interfaces:** Consistent way to interact with various LLMs and tools.
3.  **Rich Ecosystem:** Pre-built components for prompts, chains, memory, agents, etc.
4.  **Data-Awareness:** Connect LLMs to external data sources.
5.  **Agency:** Enable LLMs to interact with their environment.

Chat Model Continued Response:
AI: 6. **Simplified Development:** Abstracts boilerplate code, allowing for faster prototyping and deployment of LLM-powered applications.
--------------------
Chat Model Streamed Response:
Gray clouds softly weep,
Pitter-patter on the roof,
Nature's gentle song.
```

**Choosing Between LLMs and Chat Models:**

*   For new projects, **Chat Models are generally recommended** as they are often more capable, support multi-turn conversations naturally, and are the focus of most new model developments (like GPT-4, Gemini, etc.).
*   LLMs can still be useful for simpler tasks or when working with older models that only have a text-completion interface.

LangChain's model abstraction makes it straightforward to experiment with different types of models and providers, allowing you to choose the best fit for your application's needs. Remember to install the specific integration package for the model provider you intend to use (e.g., `langchain-anthropic`, `langchain-google-genai`, `langchain-community` for Hugging Face models).
