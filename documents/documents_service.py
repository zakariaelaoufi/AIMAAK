import os
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv
from fastapi import HTTPException
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

load_dotenv()
logger = logging.getLogger(__name__)

GEN_API_KEY = os.environ.get("GEN_API_KEY")
_qa_chain: Optional[RetrievalQA] = None


def get_llm():
    return ChatGoogleGenerativeAI(
        google_api_key=GEN_API_KEY,
        temperature=0.4,
        model="gemini-2.0-flash"
    )


def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=GEN_API_KEY
    )


async def create_vector_db(filepath: str, vector_store_path: str) -> Optional[FAISS]:
    try:
        loader = PyPDFLoader(file_path=filepath)
        documents = loader.load_and_split()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
        chunks = text_splitter.split_documents(documents)

        embeddings = get_embeddings()
        vector_store = FAISS.from_documents(chunks, embeddings)
        vector_store.save_local(vector_store_path)

        logger.info(f"Vector store created and saved to {vector_store_path}")
        return vector_store
    except Exception as e:
        logger.error(f"Failed to create vector DB: {e}")
        return None


async def load_vector_store(source_path: str, embeddings) -> Optional[FAISS]:
    try:
        if Path(source_path).exists():
            return FAISS.load_local(source_path, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        logger.error(f"Failed to load vector store: {e}")
    return None


async def initialize_qa_chat(filepath: str, vector_store_path: str) -> Optional[RetrievalQA]:
    global _qa_chain
    if _qa_chain is not None:
        print("hello")
        logger.info("QA chain already initialized")
        return get_qa_chain()

    try:
        logger.info(f"Initializing QA chain with file: {filepath}")
        if not Path(filepath).exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        embeddings = get_embeddings()

        if Path(vector_store_path).exists():
            logger.info(f"Loading existing vector store from: {vector_store_path}")
            vector_store = await load_vector_store(vector_store_path, embeddings)
        else:
            logger.info(f"Creating new vector store at: {vector_store_path}")
            vector_store = await create_vector_db(filepath, vector_store_path)

        if not vector_store:
            raise RuntimeError("Vector store is not available.")

        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 2}
        )

        _qa_chain = RetrievalQA.from_chain_type(
            llm=get_llm(),
            retriever=retriever,
            return_source_documents=True
        )

        logger.info("QA chatbot initialized")
        return _qa_chain

    except Exception as e:
        logger.error(f"Failed to initialize QA chat: {e}")
        qa_chain = None
        raise HTTPException(status_code=500, detail=f"Failed to initialize chatbot: {str(e)}")


def get_qa_chain() -> Optional[RetrievalQA]:
    return _qa_chain


def get_cache_status_service() -> dict:
    return {
        "qa_chain_cached": _qa_chain is not None,
        "vector_store_exists": Path("./vector_store").exists()
    }
