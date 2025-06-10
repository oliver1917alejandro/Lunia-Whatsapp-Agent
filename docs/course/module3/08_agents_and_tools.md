# 3.8 Agents and Tools

While Chains allow for pre-defined sequences of calls, **Agents** use an LLM as a "reasoning engine" to determine which actions to take and in what order. These actions often involve using **Tools**, which are functions that an agent can call to interact with the external world (e.g., perform a search, run code, look up data in a database).

Agents enable LLMs to go beyond just generating text and actually perform tasks and interact with their environment.

### Core Concepts:

1.  **Agent:** The LLM acting as the decision-maker. It takes user input and previous steps, and decides what to do next. This decision could be:
    *   Use a specific Tool with certain input.
    *   Respond directly to the user.
2.  **Tools:** Functions that perform specific tasks. Agents are given a list of available tools.
    *   LangChain provides many pre-built tools (e.g., `DuckDuckGoSearchRun`, `PythonREPLTool`, `WikipediaQueryRun`, `ArxivQueryRun`).
    *   You can easily create custom tools by defining a Python function and using the `@tool` decorator or by creating a class that inherits from `BaseTool`.
3.  **Agent Executor:** The runtime environment for an agent. It takes the agent and a set of tools, and orchestrates the execution loop:
    *   Passes input to the agent.
    *   Receives an "action" (tool to use and its input) or a "finish" (final response) from the agent.
    *   If it's an action, the executor calls the specified tool with the input.
    *   The tool's output (an "observation") is passed back to the agent.
    *   This loop continues until the agent decides to finish or a limit is reached.
4.  **Agent Types (ReAct, Self-ask, OpenAI Functions Agent, etc.):** Different strategies for how the agent makes decisions and uses tools.
    *   **ReAct (Reasoning and Acting):** A common pattern where the LLM generates a "Thought" (its reasoning), an "Action" (tool to use), and an "Observation" (result from the tool), iterating until it can answer.
    *   **OpenAI Functions Agent:** Leverages OpenAI's function calling capability. The LLM itself can indicate which function (tool) to call and with what arguments. This is often the most reliable for OpenAI models.

### Tools

A tool is defined by:
*   `name` (string): A unique name for the tool, used by the agent to identify it.
*   `description` (string): A clear description of what the tool does, what its inputs are, and what its outputs are. This is crucial as the agent uses this description to decide when to use the tool.
*   `func` (callable) or `_run` method: The actual function that gets executed.
*   Optionally, `args_schema` (Pydantic model): Defines the expected input arguments for the tool, allowing for structured input.

**Example: Creating a simple custom tool**

```python
from langchain.tools import tool

@tool
def get_word_length(word: str) -> int:
    """Returns the length of a word."""
    return len(word)

print(f"Tool Name: {get_word_length.name}")
print(f"Tool Description: {get_word_length.description}")
print(f"Tool Args Schema: {get_word_length.args_schema}") # Pydantic model for arguments
print(f"Running tool with 'hello': {get_word_length.run('hello')}")
```
*Output:*
```
Tool Name: get_word_length
Tool Description: get_word_length(word: str) -> int - Returns the length of a word.
Tool Args Schema: <class 'pydantic.v1.main.get_word_lengthSchema'>
Running tool with 'hello': 5
```

### Example: Using an Agent with Tools (OpenAI Functions Agent)

This example uses the OpenAI Functions agent, which is generally recommended for OpenAI models that support function calling (like "gpt-3.5-turbo", "gpt-4").

```python
# Required: pip install langchain-openai langchainhub duckduckgo-search
import os
# os.environ["OPENAI_API_KEY"] = "your_actual_api_key" # Make sure this is set

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_community.tools import DuckDuckGoSearchRun # A pre-built tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage # For manual history if needed
# langchainhub is used to pull pre-defined prompts easily
from langchain import hub


# 1. Initialize the LLM (Chat Model that supports function calling)
try:
    llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0) # 1106 models are good for function calling

    # 2. Define the tools the agent can use
    search_tool = DuckDuckGoSearchRun()
    tools = [search_tool, get_word_length] # Using our custom tool and a pre-built one

    # 3. Create the Agent
    # We need a prompt that includes:
    # - System message (optional but good for persona)
    # - Placeholders for chat history and agent scratchpad (intermediate steps)
    # - User input
    # `hub.pull` fetches a recommended prompt template for OpenAI functions agents.
    prompt = hub.pull("hwchase17/openai-functions-agent")

    # `prompt` object from hub.pull is already a ChatPromptTemplate
    # print("\nPulled Prompt Structure:")
    # for msg_template in prompt.input_ μόdules[0].messages: # Accessing messages from the first (and only) input module
    #     print(msg_template)


    # Create the OpenAI Functions Agent
    # This binds the LLM to the tools and the prompt
    agent = create_openai_functions_agent(llm, tools, prompt)

    # 4. Create the Agent Executor
    # verbose=True shows the agent's thoughts and actions
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    print("\n--- Running Agent Executor ---")
    # Example 1: Using the search tool
    query1 = "What was the score of the last Super Bowl?"
    response1 = agent_executor.invoke({"input": query1})
    print(f"\nFinal Answer for '{query1}': {response1['output']}")

    # Example 2: Using the custom get_word_length tool
    query2 = "How many letters are in the word 'onomatopoeia'?"
    response2 = agent_executor.invoke({"input": query2})
    print(f"\nFinal Answer for '{query2}': {response2['output']}")

    # Example 3: A question that might not need a tool
    query3 = "Hello, how are you today?"
    response3 = agent_executor.invoke({"input": query3})
    print(f"\nFinal Answer for '{query3}': {response3['output']}")

except Exception as e:
    print(f"Error running agent executor: {e}")
    print("Ensure OpenAI API key is set, required packages are installed, and model supports function calling.")

```

*Output (will vary, especially search results and LLM thoughts):*
```
--- Running Agent Executor ---

> Entering new AgentExecutor chain...
Invoking: `duckduckgo_search` with `{'query': 'Super Bowl LVIII score'}`
[ ... search tool might print its own output if it has verbose logging ... ]
Score of Super Bowl LVIII: Kansas City Chiefs 25, San Francisco 49ers 22. The game was played on February 11, 2024.
Final Answer for 'What was the score of the last Super Bowl?': The Kansas City Chiefs defeated the San Francisco 49ers 25-22 in Super Bowl LVIII on February 11, 2024.

> Finished chain.

Final Answer for 'What was the score of the last Super Bowl?': The Kansas City Chiefs defeated the San Francisco 49ers 25-22 in Super Bowl LVIII on February 11, 2024.

> Entering new AgentExecutor chain...
Invoking: `get_word_length` with `{'word': 'onomatopoeia'}`
12The word 'onomatopoeia' has 12 letters.

> Finished chain.

Final Answer for 'How many letters are in the word 'onomatopoeia'?:': The word 'onomatopoeia' has 12 letters.

> Entering new AgentExecutor chain...
I am doing well, thank you for asking! How can I help you today?

> Finished chain.

Final Answer for 'Hello, how are you today?': I am doing well, thank you for asking! How can I help you today?
```

**Explanation of the Agent's Process (Simplified for ReAct-like flow):**

1.  **Input:** The user's query (e.g., "What's the weather in London?").
2.  **Agent (LLM) Thought:** "I need to find the current weather. I should use a weather search tool."
3.  **Agent Action:** Call `weather_tool` with input "London".
4.  **Tool Execution:** The `weather_tool` function runs, queries a weather API, and gets the result (e.g., "15°C, cloudy").
5.  **Observation:** The result "15°C, cloudy" is passed back to the agent.
6.  **Agent (LLM) Thought:** "I have the weather. I can now answer the user."
7.  **Agent Finish:** Respond to the user: "The weather in London is 15°C and cloudy."

### Key Considerations for Agents:

*   **Prompt Engineering:** The prompt given to the agent is critical. It needs to clearly instruct the agent on how to reason, when to use tools, and how to format its thoughts and actions. Using `hub.pull` for standard agent types is often a good starting point.
*   **Tool Descriptions:** The agent relies heavily on tool descriptions to decide which tool is appropriate for a task. Descriptions should be clear, concise, and accurately reflect the tool's functionality and expected input.
*   **Choosing an Agent Type:**
    *   `OpenAI Functions Agent`: Best for OpenAI models that support function calling.
    *   `ReAct Agent` (e.g., `create_react_agent`): A more general-purpose agent that works with a wider range of LLMs by having the LLM output explicit "Thought:" and "Action:" text.
    *   Other types like `SelfAskWithSearch` are specialized for particular tasks.
*   **Error Handling:** Implement robust error handling within your tools.
*   **Cost and Latency:** Agents can make multiple LLM calls and tool calls, which can increase cost and latency.
*   **Safety and Security:** Be cautious when giving agents tools that can interact with sensitive systems or execute arbitrary code (like a Python REPL).

Agents and Tools represent a significant step towards creating truly interactive and capable AI systems. They allow LLMs to break free from the confines of text generation and actively engage with data and environments to solve complex problems.
