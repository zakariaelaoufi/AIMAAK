from fastapi import status, HTTPException, Body
from typing import Optional
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from .prompts import nlp_result_explanation_prompt, sql_query_prompt
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GEN_API_KEY = os.getenv("GEN_API_KEY")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Constants
DB_URI = os.getenv("DB_URI")


# Global variables for caching
db: Optional[SQLDatabase] = None
schema_cache: Optional[str] = None


# Get LLM instance
def get_llm():
    return ChatGoogleGenerativeAI(
        google_api_key=GEN_API_KEY,
        temperature=0.4,
        model="gemini-2.0-flash"
    )


aimaak_llm = get_llm()

# Chains
def get_sql_query_chain():
    return sql_query_prompt | aimaak_llm | StrOutputParser()

def get_sql_query_response_chain():
    return nlp_result_explanation_prompt | aimaak_llm


# DB utility functions
async def initialize_database(uri: str) -> SQLDatabase:
    return SQLDatabase.from_uri(uri, view_support=True)


async def get_schema_info(database: SQLDatabase) -> str:
    return database.get_table_info()

def get_schema():
    return schema_cache

async def initialize_db_and_schema():
    global db, schema_cache
    try:
        db = await initialize_database(DB_URI)
        # Test connection by fetching schema or running a simple query
        test_schema = await get_schema_info(db)
        if test_schema:
            logger.info("Database connection successful.")
        else:
            logger.error("Database connection failed: No schema found.")
            return False
        if not schema_cache:
            schema_cache = test_schema
            logger.info("Schema fetched and cached.")
        return True
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        return False


# Query execution and response generation
async def run_query(query: str):
    global db
    try:
        return db.run(query)
    except Exception as e:
        logger.e4("Query error:", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query execution failed.")


async def generate_sql_query(question: str) -> str:
    if not schema_cache:
        raise HTTPException(status_code=500, detail="Schema not available.")
    chain = get_sql_query_chain()
    return chain.invoke({"schema": schema_cache, "question": question})


async def generate_natural_language_response(question: str, result: str) -> str:
    chain = get_sql_query_response_chain()
    response = chain.invoke({"question": question, "result": result})
    return response.content