# 3.5 Chains: Basic Usage

Chains are at the core of LangChain's philosophy of composability. A chain is a sequence of calls to components, which can include models (LLMs or Chat Models), prompt templates, other chains, or custom Python functions. They allow you to combine multiple steps to create more complex applications.

The most fundamental type of chain is the **`LLMChain`**.

### `LLMChain`: The Core Chain

An `LLMChain` is the simplest and most common type of chain. It consists of:
1.  A **Model** (either an LLM or a Chat Model).
2.  A **PromptTemplate** (or `ChatPromptTemplate`).

The `LLMChain` takes user input, formats it using the `PromptTemplate`, and then passes the formatted prompt to the Model to get a response.

**How it works:**
1.  Input variables are received.
2.  The `PromptTemplate` uses these variables to generate a prompt.
3.  The `Model` takes this prompt and returns an output string (for LLMs) or an AIMessage (for Chat Models).
4.  The `LLMChain` returns a dictionary containing the model's output and potentially other information.

```python
# Required: pip install langchain-openai
import os
# os.environ["OPENAI_API_KEY"] = "your_actual_api_key"

from langchain_openai import OpenAI, ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain # The primary chain class

# --- Example 1: LLMChain with an LLM ---
print("--- LLMChain with LLM ---")
llm = OpenAI(model_name="gpt-3.5-turbo-instruct", temperature=0.7) # Make sure API key is set

# Define a prompt template
prompt_llm = PromptTemplate(
    input_variables=["product_name", "feature"],
    template="Generate a short, catchy marketing slogan for a product called '{product_name}' that highlights its '{feature}' feature."
)

# Create the LLMChain
llm_chain = LLMChain(llm=llm, prompt=prompt_llm)

# Input for the chain
input_data_llm = {"product_name": "QuickCharge Battery", "feature": "ultra-fast charging"}

try:
    # Invoke the chain (using .invoke() is the modern way)
    response_llm = llm_chain.invoke(input_data_llm)
    print(f"Input: {input_data_llm}")
    # The response is a dictionary. The actual LLM output is typically in the 'text' key.
    print(f"Slogan: {response_llm.get('text', 'Error: No text key in response').strip()}")
except Exception as e:
    print(f"Error invoking LLMChain (LLM): {e}")
    print("Ensure your OpenAI API key is set and valid.")


print("\n--- LLMChain with Chat Model ---")
# --- Example 2: LLMChain with a Chat Model ---
chat_model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7) # Make sure API key is set

# Define a chat prompt template
system_message = SystemMessagePromptTemplate.from_template(
    "You are a witty assistant who creates taglines. Be concise and clever."
)
human_message = HumanMessagePromptTemplate.from_template(
    "Create a tagline for a company that sells {product_category} called '{company_name}'."
)
chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])

# Create the LLMChain with the chat model and chat prompt
chat_chain = LLMChain(llm=chat_model, prompt=chat_prompt)

# Input for the chain
input_data_chat = {"product_category": "artisanal coffee beans", "company_name": "AromaPeak"}

try:
    # Invoke the chain
    response_chat = chat_chain.invoke(input_data_chat)
    print(f"Input: {input_data_chat}")
    # For chat models, the output is also in the 'text' key of the response dictionary
    print(f"Tagline: {response_chat.get('text', 'Error: No text key in response').strip()}")
except Exception as e:
    print(f"Error invoking LLMChain (Chat Model): {e}")
    print("Ensure your OpenAI API key is set and valid.")

```

*Output (will vary due to model generation):*
```
--- LLMChain with LLM ---
Input: {'product_name': 'QuickCharge Battery', 'feature': 'ultra-fast charging'}
Slogan: QuickCharge Battery: Power Up Your Life in a Flash!

--- LLMChain with Chat Model ---
Input: {'product_category': 'artisanal coffee beans', 'company_name': 'AromaPeak'}
Tagline: AromaPeak: Elevating your daily grind.
```

### Key Aspects of `LLMChain`:

*   **Input Keys:** Defined by the `input_variables` in the `PromptTemplate`. When you call `chain.invoke(inputs)`, the `inputs` dictionary must contain these keys.
*   **Output Keys:** By default, the main output from the model is stored in a key named `text` in the result dictionary.
    *   You can change the output key by specifying `output_key="your_key_name"` when creating the `LLMChain`. This is useful when chaining multiple `LLMChain`s together, as the output of one chain can be the input to another.

```python
# Example: Custom output key
custom_output_chain = LLMChain(llm=llm, prompt=prompt_llm, output_key="slogan_text")
try:
    response_custom = custom_output_chain.invoke(input_data_llm)
    print("\n--- LLMChain with Custom Output Key ---")
    print(f"Slogan from 'slogan_text' key: {response_custom.get('slogan_text', 'Error: Key not found').strip()}")
except Exception as e:
    print(f"\nError with custom output key: {e}")
```
*Output (will vary):*
```
--- LLMChain with Custom Output Key ---
Slogan from 'slogan_text' key: QuickCharge Battery: Power Up Your Life in an Instant!
```

### Beyond `LLMChain`: Sequential Chains

While `LLMChain` is fundamental, LangChain offers more complex chain types. One common pattern is to run a sequence of chains, where the output of one chain becomes the input to the next.

*   **`SimpleSequentialChain`**: The simplest way to chain calls. It runs a sequence of chains or callables, and each step takes a single string as input and returns a single string as output. The output of one step is directly fed as the input to the next.
*   **`SequentialChain`**: More flexible than `SimpleSequentialChain`. It allows for multiple inputs and outputs between chained elements. You explicitly define how outputs from one chain map to inputs of the next.

**Example of `SimpleSequentialChain` (Conceptual - requires multiple chains defined):**

```python
from langchain.chains import SimpleSequentialChain

# Assume chain_one and chain_two are already defined LLMChains
# where chain_one's output key is 'text' (default)
# and chain_two's prompt template expects an input variable that matches chain_one's output.

# Chain 1: Generate a company name based on a product
prompt_company = PromptTemplate.from_template("Suggest a creative company name for a business that makes {product_type}.")
chain_one = LLMChain(llm=llm, prompt=prompt_company, output_key="company_name_output") # output key is company_name_output

# Chain 2: Write a tagline for a given company name
prompt_tagline = PromptTemplate.from_template("Write a short, catchy tagline for a company named '{company_name_output}'.")
chain_two = LLMChain(llm=llm, prompt=prompt_tagline, output_key="tagline_output") # output key is tagline_output

# Create the SimpleSequentialChain (make sure input/output keys align or use SequentialChain for mapping)
# For SimpleSequentialChain, the output of chain_one ('company_name_output') must be the input variable for chain_two's prompt.
# This setup is a bit problematic for SimpleSequentialChain as it expects the variable name to be the same.
# A SequentialChain would be better here for explicit mapping.

# Let's adjust chain_one's output_key to match chain_two's expected input for SimpleSequentialChain to work easily.
# Or, more simply, ensure chain_two's prompt uses 'text' if chain_one has default output.
# For this example, let's assume a slightly different setup for simplicity with SimpleSequentialChain:

# Chain 1: Takes a topic, outputs a related concept
prompt1 = PromptTemplate.from_template("What is a key concept related to {topic}?")
chain1 = LLMChain(llm=llm, prompt=prompt1) # output key is 'text'

# Chain 2: Takes the concept (as 'text' from chain1), explains it
prompt2 = PromptTemplate.from_template("Explain the concept of {text} in one sentence.")
chain2 = LLMChain(llm=llm, prompt=prompt2) # input variable 'text' matches output of chain1

# SimpleSequentialChain - output of chain1 ('text') becomes input for chain2
simple_seq_chain = SimpleSequentialChain(chains=[chain1, chain2], verbose=True)

try:
    print("\n--- SimpleSequentialChain Example ---")
    result_seq = simple_seq_chain.invoke("artificial intelligence")
    print(f"Final Explanation: {result_seq.get('output', 'Error in SimpleSequentialChain output')}")
    # For SimpleSequentialChain, the final output is in the 'output' key by default
except Exception as e:
    print(f"Error in SimpleSequentialChain: {e}")

```
*Output (will vary):*
```
--- SimpleSequentialChain Example ---

> Entering new SimpleSequentialChain chain...
Machine learning is a key concept related to artificial intelligence.
Machine learning is a type of artificial intelligence that allows computer systems to learn from data and improve their performance on a specific task without being explicitly programmed.

> Finished chain.
Final Explanation: Machine learning is a type of artificial intelligence that enables computer systems to learn from data and make decisions or predictions without being explicitly programmed.
```

Chains are what allow you to build sophisticated logic flows. While `LLMChain` handles the interaction with the model, other chain types (like `SequentialChain`, `RouterChain`, and specialized chains like `RetrievalQA`) orchestrate how data and calls are routed and processed through multiple steps. We'll explore more advanced chains later.
