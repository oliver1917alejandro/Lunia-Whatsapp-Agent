# 3.4 Prompt Templates

Prompts are the way we instruct Large Language Models (LLMs) what to do. Crafting effective prompts is a critical skill in LLM application development. LangChain provides **Prompt Templates** to make the construction of prompts easier, more flexible, and reusable.

A Prompt Template is a pre-defined recipe for generating a prompt. It can contain:
*   Instructions for the LLM.
*   A set of input variables that will be filled in dynamically.
*   Few-shot examples (to guide the LLM's behavior).
*   The user's query or input.

### Why Use Prompt Templates?

*   **Reusability:** Define a prompt structure once and use it with different inputs.
*   **Clarity:** Separates the static parts of a prompt from the dynamic parts.
*   **Flexibility:** Easily modify the prompt structure without changing the application code that uses it.
*   **Consistency:** Ensures that all prompts sent to the LLM follow a consistent format.
*   **Integration with Chains:** Prompt templates are a fundamental part of LangChain's `LLMChain`.

### Basic PromptTemplate (for LLMs)

The `PromptTemplate` class is used for creating prompts for standard LLMs (which take a string as input).

```python
# Required: pip install langchain-openai
import os
# os.environ["OPENAI_API_KEY"] = "your_actual_api_key"

from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI

# 1. Define the template string
template_string = """
You are a helpful assistant.
Translate the following English text into {target_language}:
Text: "{text_to_translate}"
Translation:
"""

# 2. Create a PromptTemplate instance
prompt_template = PromptTemplate(
    input_variables=["target_language", "text_to_translate"], # Variables expected by the template
    template=template_string
)

# 3. Format the prompt with actual values
formatted_prompt = prompt_template.format(
    target_language="French",
    text_to_translate="Hello, how are you today?"
)

print("Formatted Prompt:")
print(formatted_prompt)

# Example of using this with an LLM (and a simple LLMChain)
# This also implicitly shows the start of a basic chain
from langchain.chains import LLMChain
try:
    llm = OpenAI(model_name="gpt-3.5-turbo-instruct", temperature=0) # Assuming API key is set
    chain = LLMChain(llm=llm, prompt=prompt_template)

    response = chain.invoke({
        "target_language": "Spanish",
        "text_to_translate": "Good morning!"
    })
    print("\nLLM Response (Spanish translation):")
    # The response from LLMChain is a dictionary, the actual text is usually in 'text' key
    print(response.get('text', 'Error: No text in response'))

    response_german = chain.invoke({
        "target_language": "German",
        "text_to_translate": "Where is the library?"
    })
    print("\nLLM Response (German translation):")
    print(response_german.get('text', 'Error: No text in response'))

except Exception as e:
    print(f"\nError running LLMChain: {e}")
    print("Ensure your OpenAI API key is correctly set and the model is available.")

```

*Output (will vary slightly for LLM responses):*
```
Formatted Prompt:

You are a helpful assistant.
Translate the following English text into French:
Text: "Hello, how are you today?"
Translation:

LLM Response (Spanish translation):
 Buenos días!

LLM Response (German translation):
 Wo ist die Bibliothek?
```

### ChatPromptTemplate (for Chat Models)

Chat models expect a list of `ChatMessage` objects as input. `ChatPromptTemplate` helps construct this list. It's typically built from a list of "message templates," where each message template can be:

*   A `SystemMessagePromptTemplate`: For system messages.
*   A `HumanMessagePromptTemplate`: For user messages.
*   An `AIMessagePromptTemplate`: For AI messages (less common to template directly, more often the output of a previous step).

```python
# Required: pip install langchain-openai
import os
# os.environ["OPENAI_API_KEY"] = "your_actual_api_key"

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

# 1. Define message templates
system_template_string = "You are a helpful AI assistant that specializes in explaining complex topics in a simple way for a {audience}."
system_message_prompt = SystemMessagePromptTemplate.from_template(system_template_string)

human_template_string = "Please explain the concept of '{concept}'."
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template_string)

# 2. Create a ChatPromptTemplate
chat_prompt_template = ChatPromptTemplate.from_messages(
    [system_message_prompt, human_message_prompt]
)

# 3. Format the chat prompt with actual values
formatted_chat_prompt = chat_prompt_template.format_prompt(
    audience="high school student",
    concept="Quantum Entanglement"
)

# The result is a ChatPromptValue, convert to messages for inspection or model input
formatted_messages = formatted_chat_prompt.to_messages()

print("Formatted Chat Messages:")
for msg in formatted_messages:
    print(f"Type: {msg.type}, Content: {msg.content}")

print("-" * 20)

# Example of using this with a Chat Model in an LLMChain
try:
    chat_model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0) # Assuming API key
    chat_chain = LLMChain(llm=chat_model, prompt=chat_prompt_template)

    response = chat_chain.invoke({
        "audience": "5-year-old child",
        "concept": "Black Holes"
    })
    print("\nChat Model Response (for a child):")
    # The response from LLMChain with a ChatModel is a dictionary,
    # the AIMessage content is usually in 'text' key
    print(response.get('text', "Error: No text in response"))

except Exception as e:
    print(f"\nError running Chat LLMChain: {e}")
    print("Ensure your OpenAI API key is correctly set and the model is available.")

```
*Output (will vary for LLM responses):*
```
Formatted Chat Messages:
Type: system, Content: You are a helpful AI assistant that specializes in explaining complex topics in a simple way for a high school student.
Type: human, Content: Please explain the concept of 'Quantum Entanglement'.
--------------------

Chat Model Response (for a child):
Imagine you have two magic toy cars that are best friends. Let's call them Car A and Car B. These cars are so special that they are "entangled," which means they always know what the other is doing, no matter how far apart they are!

If Car A is blue, you instantly know Car B is also blue, even if Car B is hiding in another room or even another house! And if you paint Car A red, Car B magically turns red at the exact same moment!

Black holes are a bit like super-duper strong vacuum cleaners in space, but way, way, way bigger and stronger than any vacuum cleaner you've ever seen! They have such strong gravity (pulling power) that nothing, not even light (like from a flashlight), can escape if it gets too close.

Imagine throwing your toys up in the air. They always come back down, right? That's because Earth has gravity. A black hole's gravity is so super strong that if you could throw your toy hard enough to get near it, it would get sucked in and never come out! It's like a one-way street for everything, even stars and planets if they wander too close! They're a bit mysterious and super interesting, but luckily, they are very, very far away from us!
```

### Key Features of Prompt Templates:

*   **Input Variables:** Clearly defined using `{variable_name}` syntax.
*   **Partial Formatting:** You can pre-fill some variables in a template using `.partial()` to create a new template that expects fewer inputs.
    ```python
    french_translator_template = prompt_template.partial(target_language="French")
    formatted_french_prompt = french_translator_template.format(text_to_translate="This is great!")
    print("\nPartially Formatted Prompt:")
    print(formatted_french_prompt)
    # Output:
    # You are a helpful assistant.
    # Translate the following English text into French:
    # Text: "This is great!"
    # Translation:
    ```
*   **Composition:** Templates can be combined, though this is often handled more explicitly within chains.
*   **Few-Shot Examples:** For more complex tasks, you can include examples directly in the template string or use `FewShotPromptTemplate` or `FewShotChatMessagePromptTemplate` along with `ExampleSelectors` to dynamically choose relevant examples from a larger set. This helps the LLM understand the desired output format or reasoning process.

Prompt templates are a foundational building block in LangChain. They provide the structure needed to guide LLMs effectively and are essential for building robust and maintainable LLM applications. Mastering prompt engineering and templating is key to unlocking the full potential of these models.
