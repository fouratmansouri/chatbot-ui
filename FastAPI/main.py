from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_community.document_loaders import JSONLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage

# Initialize embeddings
embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")

# Initialize the Chroma vector store for FAQ and Web datasets
vector_store = Chroma(
    collection_name="ihec_collection_Orca",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_ihec_db",
)

# LLM for ChatOllama
llm = ChatOllama(
    model="llama3.1:8b",
    temperature=0.2,
    max_tokens=200
)

# Define schema for user queries
class QueryRequest(BaseModel):
    question: str

# Initialize FastAPI app
app = FastAPI()

# The RAG prompt template
rag_prompt = """You are an assistant for question-answering task.

Your role is to guide and explain students.

Here is the context to use to answer the question:

{context}

Think carefully about the above context.

Now, review the user question:

{question}

Provide an answer to this question using only the above context.

Use three sentences maximum and keep the answer concise.

Answer:"""

# Define metadata extraction for JSONLoader
def metadata_func(record: dict, metadata: dict) -> dict:
    metadata["id"] = record.get("id")
    metadata["category"] = record.get("category")
    metadata["question"] = record.get("question")
    metadata["answer"] = record.get("answer")
    return metadata

# Load and split documents (e.g., FAQ data)
loader = JSONLoader(
    file_path='./FAQ.json',
    jq_schema=r'.dataset[] | . + {"content": "\(.answer) \(.question) \(.category)"}',
    content_key="content",
    metadata_func=metadata_func
)

documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", "!", "?", ",", " "]
)

split_docs = text_splitter.split_documents(documents)

# Create Chroma vector store from documents
db = Chroma.from_documents(
    documents=split_docs,
    embedding=embeddings,
    persist_directory="./chroma_langchain_ihec_db",
    collection_name="ihec_collection_Orca",
    collection_metadata={"hnsw:space": "cosine"}
)

# Define function for RAG-based response
def generate_rag_answer(query: str):
    # Perform similarity search on FAQ data
    results = db.similarity_search(query, k=2)

    # Extract relevant context
    combined_content = " ".join([doc.page_content for doc in results])

    # Format the prompt
    rag_prompt_formatted = rag_prompt.format(context=combined_content, question=query)

    # Generate answer using the LLM (ChatOllama)
    generation = llm.invoke([HumanMessage(content=rag_prompt_formatted)])
    return generation.content

# API endpoint for handling user queries
@app.post("/query/")
async def get_chatbot_response(query: QueryRequest):
    try:
        answer = generate_rag_answer(query.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the query: {str(e)}")