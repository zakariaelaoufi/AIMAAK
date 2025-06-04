from fastapi import status, HTTPException, Body
from typing import Optional
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GEN_API_KEY = os.getenv("GEN_API_KEY")

# Constants
DB_URI = "mysql+mysqlconnector://root:root@localhost:3306/product_management"

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


# Prompt templates
sql_query_prompt = ChatPromptTemplate.from_template("""
You are a skilled MySQL assistant. Given the table schema and a natural language question, generate a syntactically correct and efficient SQL query that accurately answers the question.

Schema:
{schema}

User Question:
{question}

SQL Query:
""")

nlp_result_explanation_prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant. Based on the user's question and the SQL query result provided, write a natural, clear, and concise response that summarizes the result in plain language.

User Question:
{question}

Query Result:
{result}

Natural Language Response:
""")


# Chains
def get_sql_query_chain():
    return sql_query_prompt | aimaak_llm | StrOutputParser()

def get_sql_query_response_chain():
    return nlp_result_explanation_prompt | aimaak_llm


# DB utility functions
async def initialize_database(uri: str) -> SQLDatabase:
    return SQLDatabase.from_uri(uri)


async def get_schema_info(database: SQLDatabase) -> str:
    return database.get_table_info()


async def initialize_db_and_schema():
    global db, schema_cache
    try:
        db = await initialize_database(DB_URI)
        if not schema_cache:
            schema_cache = await get_schema_info(db)
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