from fastapi import APIRouter, status, HTTPException, Body
from .sql_service import generate_sql_query, run_query, generate_natural_language_response, get_schema
import logging

logger = logging.getLogger(__name__)


CONNECTIVITY_QUERY = "SELECT 1;"

# Initialize router
router = APIRouter(prefix="/api-v1/sql", tags=["sql"])

import re

def clean_query(query: str) -> str:
    # Supprime les blocs de balisage markdown ```sql ... ```
    return re.sub(r"```(?:sql)?\s*([\s\S]*?)\s*```", r"\1", query).strip()

# Routes
@router.post("/ask", status_code=status.HTTP_200_OK)
async def client_question_answer(payload: dict = Body(...)):
    question = payload.get("question")
    if not question:
        raise HTTPException(status_code=400, detail="Missing question.")
    sql_query = await generate_sql_query(question)
    sql_query = clean_query(sql_query)
    print("salam")
    print(sql_query)
    logger.info(sql_query)
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
    # basic sql injection protection
    query_upper = sql_query.upper()
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Query contains potentially dangerous operation: {keyword}"
            )
    query_result = await run_query(query_upper)
    response = await generate_natural_language_response(question, query_result)
    return {"response":response,
            "query": query_upper
            }


@router.get("/connectivity-test", status_code=status.HTTP_200_OK)
async def test_db():
    try:
        result = await run_query(CONNECTIVITY_QUERY)
        return {"status": "Connected", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database connection failed.")

@router.get("/schema", status_code=status.HTTP_200_OK)
async def get_schema_db():
    return get_schema()