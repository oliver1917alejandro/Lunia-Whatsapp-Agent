# 3.6 Indexes: Document Loaders, Splitters, VectorStores, and Retrievers

One of the most powerful capabilities of LangChain is its ability to connect LLMs to external data sources. This allows LLMs to:
*   Answer questions about specific documents (e.g., your company's internal knowledge base).
*   Incorporate information that is more recent than their training data.
*   Reduce "hallucinations" by grounding responses in provided text.

The "Indexes" component in LangChain refers to the tools and processes for structuring and retrieving documents so that LLMs can effectively work with them. Key parts of this process include:

1.  **Document Loaders:** Load documents from various sources.
2.  **Text Splitters:** Break large documents into smaller, manageable chunks.
3.  **VectorStores (and Embeddings):** Store document chunks as numerical vectors (embeddings) to enable efficient similarity search.
4.  **Retrievers:** Fetch relevant document chunks based on a user's query.

### 1. Document Loaders

Document loaders are responsible for fetching data from a source and returning it as a list of `Document` objects. A `Document` object in LangChain contains page content (text) and metadata.

LangChain supports a wide variety of document loaders:
*   Text files (`TextLoader`)
*   CSV files (`CSVLoader`)
*   HTML files/Web pages (`UnstructuredHTMLLoader`, `WebBaseLoader`)
*   PDFs (`PyPDFLoader`, `UnstructuredPDFLoader`)
*   JSON (`JSONLoader`)
*   Markdown (`UnstructuredMarkdownLoader`)
*   Databases (e.g., `SQLDatabaseLoader`)
*   Cloud storage (S3, GCS, Azure Blob Storage)
*   Collaboration tools (Notion, Google Drive, Confluence)
*   And many more (see `langchain_community.document_loaders`)

**Example: Loading a text file**

```python
from langchain_community.document_loaders import TextLoader
import os

# Create a dummy text file for demonstration
dummy_file_path = "example_document.txt"
with open(dummy_file_path, "w", encoding="utf-8") as f:
    f.write("This is the first sentence of our example document.\n")
    f.write("LangChain helps connect LLMs to external data.\n")
    f.write("This document talks about document loaders, text splitters, and vector stores.\n")
    f.write("The final sentence is here to make the document a bit longer.")

# Initialize the loader
loader = TextLoader(dummy_file_path)

# Load the documents
try:
    documents = loader.load()
    print(f"Loaded {len(documents)} document(s).")
    for doc in documents:
        print(f"\nContent (first 50 chars): {doc.page_content[:50]}...")
        print(f"Metadata: {doc.metadata}")
except Exception as e:
    print(f"Error loading document: {e}")
finally:
    # Clean up the dummy file
    if os.path.exists(dummy_file_path):
        os.remove(dummy_file_path)

```
*Output:*
```
Loaded 1 document(s).

Content (first 50 chars): This is the first sentence of our example document....
Metadata: {'source': 'example_document.txt'}
```

### 2. Text Splitters

LLMs have a context window limit, meaning they can only process a certain amount of text at once. Therefore, large documents need to be split into smaller chunks before being fed to an LLM or stored in a VectorStore.

Text splitters take a list of `Document` objects and split their `page_content` into smaller pieces, ideally trying to keep semantically related pieces of text together.

Common text splitters:
*   **`RecursiveCharacterTextSplitter` (Recommended):** Splits text recursively based on a list of characters (e.g., `\n\n`, `\n`, ` `, `""`). It tries to keep paragraphs, then sentences, then words together.
*   **`CharacterTextSplitter`:** Splits based on a single character.
*   **`TokenTextSplitter`:** Splits based on token count (requires a tokenizer like `tiktoken` for OpenAI models).
*   Splitters for specific content types (e.g., `MarkdownTextSplitter`, `PythonCodeTextSplitter`).

Key parameters for splitters:
*   `chunk_size`: The maximum size of a chunk.
*   `chunk_overlap`: The number of characters/tokens to overlap between chunks. This helps maintain context between chunks.

**Example: Using `RecursiveCharacterTextSplitter`**

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Assume 'documents' is a list of Document objects (e.g., from a loader)
# For this example, let's create a single large document string
large_text_content = """LangChain is a framework for developing applications powered by language models.
It enables applications that are:
Data-aware: connect a language model to other sources of data.
Agentic: allow a language model to interact with its environment.
LangChain provides modules for models, prompts, memory, indexes, chains, and agents.
Working with long documents often requires splitting them into smaller, manageable chunks.
This ensures that the text fits within the LLM's context window.
Overlap between chunks can help maintain context.
RecursiveCharacterTextSplitter is a common choice.
It tries to split on paragraph breaks, then line breaks, then spaces.
"""
doc_for_splitting = [type('Document', (), {'page_content': large_text_content, 'metadata': {'source': 'manual_text'}})]


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,  # Max characters per chunk
    chunk_overlap=20 # Characters to overlap between chunks
)

split_documents = text_splitter.split_documents(doc_for_splitting)

print(f"\nOriginal document count: {len(doc_for_splitting)}")
print(f"Number of chunks after splitting: {len(split_documents)}")
for i, chunk_doc in enumerate(split_documents):
    print(f"\nChunk {i+1} (first 50 chars): {chunk_doc.page_content[:50]}...")
    print(f"Chunk {i+1} Metadata: {chunk_doc.metadata}") # Metadata is preserved
```
*Output:*
```
Original document count: 1
Number of chunks after splitting: 5

Chunk 1 (first 50 chars): LangChain is a framework for developing application...
Chunk 1 Metadata: {'source': 'manual_text'}

Chunk 2 (first 50 chars): It enables applications that are:
Data-aware: conn...
Chunk 2 Metadata: {'source': 'manual_text'}

Chunk 3 (first 50 chars): modules for models, prompts, memory, indexes, chai...
Chunk 3 Metadata: {'source': 'manual_text'}

Chunk 4 (first 50 chars): the LLM's context window.
Overlap between chunks...
Chunk 4 Metadata: {'source': 'manual_text'}

Chunk 5 (first 50 chars): RecursiveCharacterTextSplitter is a common choice....
Chunk 5 Metadata: {'source': 'manual_text'}
```

### 3. VectorStores and Embeddings

Once documents are split into chunks, we need an efficient way to find the most relevant chunks for a given query. This is where **embeddings** and **VectorStores** come in.

*   **Embeddings:** An embedding is a numerical representation (a vector) of a piece of text. Texts with similar meanings will have embeddings that are close together in the vector space.
    *   LangChain provides interfaces for various embedding models (e.g., `OpenAIEmbeddings`, `HuggingFaceEmbeddings`).
*   **VectorStores:** These are databases designed to store these text embeddings and perform very fast similarity searches (vector searches). Given a query embedding, a vector store can quickly find the text chunks whose embeddings are most similar.

Common VectorStores:
*   `FAISS` (Facebook AI Similarity Search): Runs locally, good for quick experimentation.
*   `Chroma`: Open-source, runs locally or can be self-hosted.
*   `Pinecone`, `Weaviate`: Managed cloud vector databases, good for production.
*   And many others.

**Example: Using `OpenAIEmbeddings` and `FAISS`**

```python
# Required: pip install langchain-openai faiss-cpu tiktoken
# faiss-gpu if you have a compatible GPU and CUDA setup

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS # Using FAISS for local example

# Assume 'split_documents' are available from the previous step.
# If not, let's quickly create some for this example:
if 'split_documents' not in locals() or not split_documents:
     quick_texts = ["LangChain is great.", "Embeddings are numerical representations.", "FAISS is a vector store."]
     split_documents = [type('Document', (), {'page_content': t, 'metadata':{'source':'quick'}}) for t in quick_texts]


# Initialize an embedding model
try:
    # Ensure OPENAI_API_KEY is set in environment variables
    embeddings_model = OpenAIEmbeddings() # Defaults to "text-embedding-ada-002"

    # Create embeddings for the document chunks and store them in FAISS
    # This step sends your document chunks to the OpenAI API to get embeddings
    print("\nCreating FAISS VectorStore (may take a moment for embeddings)...")
    vector_store = FAISS.from_documents(split_documents, embeddings_model)
    print("FAISS VectorStore created.")

    # Now the vector_store is ready for similarity searches
    query = "What are embeddings?"
    # 'similarity_search' finds documents similar to the query string
    # 'similarity_search_by_vector' finds documents similar to a query vector
    relevant_docs = vector_store.similarity_search(query, k=2) # Get top 2 relevant docs

    print(f"\nMost relevant documents for query '{query}':")
    for i, doc in enumerate(relevant_docs):
        print(f"Doc {i+1}: {doc.page_content}")
        print(f"Metadata: {doc.metadata}\n")

except Exception as e:
    print(f"\nError during VectorStore creation or search: {e}")
    print("Ensure OpenAI API key is set and 'faiss-cpu' is installed.")

```
*Output (will vary slightly based on actual split_documents content):*
```
Creating FAISS VectorStore (may take a moment for embeddings)...
FAISS VectorStore created.

Most relevant documents for query 'What are embeddings?':
Doc 1: Embeddings are numerical representations.
Metadata: {'source': 'quick'}

Doc 2: LangChain is great.
Metadata: {'source': 'quick'}
```

### 4. Retrievers

A **Retriever** is an interface that returns documents given an unstructured query. It's more general than a VectorStore. While a VectorStore *can be* the backbone of a retriever, other retrieval methods exist.

The most common type of retriever is a `VectorStoreRetriever`, which uses a vector store to find relevant documents.

**Example: Using a `VectorStoreRetriever`**

```python
# Assume 'vector_store' is available from the previous step.
if 'vector_store' in locals() and vector_store:
    # Create a retriever from the vector store
    retriever = vector_store.as_retriever(search_kwargs={"k": 1}) # Get top 1 relevant doc

    query_for_retriever = "Tell me about LangChain"
    try:
        retrieved_docs = retriever.invoke(query_for_retriever) # Use invoke for modern LangChain
        print(f"\nDocuments retrieved for query '{query_for_retriever}':")
        for doc in retrieved_docs:
            print(f"Content: {doc.page_content}")
            print(f"Metadata: {doc.metadata}\n")
    except Exception as e:
        print(f"Error during retrieval: {e}")
else:
    print("\nSkipping retriever example as vector_store was not created.")
```
*Output (will vary):*
```
Documents retrieved for query 'Tell me about LangChain':
Content: LangChain is great.
Metadata: {'source': 'quick'}
```

**Putting It All Together (Conceptual Flow for Question Answering):**

1.  **Load:** Use `DocumentLoader` to load raw documents.
2.  **Split:** Use `TextSplitter` to break them into chunks.
3.  **Store:** Use an `EmbeddingModel` and `VectorStore` to create and store embeddings of these chunks.
4.  **Retrieve:** When a user asks a question, use a `Retriever` (backed by the `VectorStore`) to find the most relevant chunks of text.
5.  **Generate:** Pass the user's question and the content of the retrieved chunks to an LLM (usually via a chain like `RetrievalQA`) to generate an answer.

This indexing pipeline is fundamental for building LLM applications that can reason about specific, external data. LangChain's modular components make each step configurable and extensible.
