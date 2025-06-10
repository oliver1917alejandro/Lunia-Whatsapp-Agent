# 6.2 LangChain Exercises

These exercises will help you practice the LangChain concepts from Module 3. You'll need to have LangChain and an LLM provider library (like `openai`) installed. **Remember to set your API keys (e.g., `OPENAI_API_KEY` as an environment variable).**

**Important Note:** Running LLMs can incur costs depending on the provider and model used. Be mindful of this, especially with complex chains or agents. Start with simpler, cheaper models if possible for testing.

**Exercise 1: Basic LLM Interaction**

1.  Import `OpenAI` (or another LLM like `HuggingFaceHub`) from `langchain.llms`.
2.  Initialize an LLM instance. Set `temperature=0.7`.
3.  Create a simple prompt string, e.g., "What are the top 3 benefits of learning Python?"
4.  Use the `llm.predict()` method to get a response to your prompt.
5.  Print the prompt and the response.

**Exercise 2: Using Prompt Templates**

1.  Import `PromptTemplate` from `langchain.prompts`.
2.  Create a template string: "Generate a short story (2-3 paragraphs) about a brave knight who encounters a {creature} in a {location}."
    *   This template has two input variables: `creature` and `location`.
3.  Create a `PromptTemplate` object from this string.
4.  Format the prompt template with `creature="dragon"` and `location="dark forest"`. Print the formatted prompt.
5.  Format it again with `creature="talking squirrel"` and `location="bustling city"`. Print this too.

**Exercise 3: Simple `LLMChain`**

1.  Import `OpenAI` (or your chosen LLM), `PromptTemplate`, and `LLMChain`.
2.  Initialize your LLM.
3.  Create a `PromptTemplate` for a task, e.g., "Translate the following English text to French: '{english_text}'".
4.  Create an `LLMChain` using your LLM and the prompt template.
5.  Run the chain with an example English text, e.g., `chain.run(english_text="Hello, world!")`.
6.  Print the result.
7.  Try another input, e.g., `chain.run(english_text="LangChain is fun to learn.")`.

**Exercise 4: `LLMChain` with a Chat Model**

1.  Import `ChatOpenAI` (or another chat model), `ChatPromptTemplate`, `SystemMessagePromptTemplate`, `HumanMessagePromptTemplate`, and `LLMChain`.
2.  Initialize `ChatOpenAI` with `temperature=0.5`.
3.  Create a system message template: "You are an assistant that explains programming concepts to beginners."
4.  Create a human message template: "Explain the concept of '{concept}' in simple terms."
5.  Create a `ChatPromptTemplate` from these messages.
6.  Create an `LLMChain` using the chat model and the chat prompt template.
7.  Run the chain with `concept="Object-Oriented Programming"`. Print the result.
8.  Run it again with `concept="APIs"`.

**Exercise 5: Basic Memory (Conceptual - for `LLMChain`)**

1.  Import `OpenAI`, `LLMChain`, `PromptTemplate`, and `ConversationBufferMemory`.
2.  Initialize your LLM.
3.  Create a `PromptTemplate` that includes a placeholder for history and the human input:
    ```
    You are a helpful conversational AI.
    Previous conversation:
    {history}
    Human: {human_input}
    AI:
    ```
    *   Input variables: `history`, `human_input`.
4.  Initialize `ConversationBufferMemory` with `memory_key="history"` and `input_key="human_input"`.
5.  Create an `LLMChain` with the LLM, prompt, and memory. Set `verbose=True` to see the full prompt.
6.  Interact with the chain multiple times:
    *   `chain.predict(human_input="Hi, my name is Alex.")`
    *   `chain.predict(human_input="What is my name?")`
    *   `chain.predict(human_input="What is the capital of France?")`
    *   Observe how the `history` is populated and sent to the LLM.

**Exercise 6: Simple Document Loading and Splitting (No LLM needed for this part)**

1.  Import `TextLoader` from `langchain.document_loaders` and `RecursiveCharacterTextSplitter` from `langchain.text_splitter`.
2.  Create a dummy text file named `my_sample_doc.txt` with a few paragraphs of text (at least 15-20 lines).
3.  Use `TextLoader` to load the document.
4.  Initialize `RecursiveCharacterTextSplitter` with `chunk_size=150` and `chunk_overlap=30`.
5.  Split the loaded document(s) using `splitter.split_documents()`.
6.  Print the number of chunks created and print the content of the first 2-3 chunks.
7.  Remember to `import os` and `os.remove("my_sample_doc.txt")` at the end if you want to clean up.
