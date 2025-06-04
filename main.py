from fastapi import FastAPI
from redis import Redis
import httpx
from documents.documents_service import initialize_qa_chat
from relational_db.sql_service import initialize_db_and_schema
from documents.documents_controller import router as documents_router
from general.general_chat_controller import router as general_chat_router
from relational_db.sql_controller import router as relational_db_router
import logging

logger = logging.getLogger(__name__)

FILE_PATH = "./Lara_Fashion_QA.pdf"
VECTOR_STORE_PATH = "./vector_store"

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    try:
        app.state.redis = Redis(host="localhost", port=6379, decode_responses=True)
        app.state.http_client = httpx.AsyncClient()
        success = await initialize_qa_chat(FILE_PATH, VECTOR_STORE_PATH)
        if success:
            logger.info("AIMaak Chatbot pre-initialized successfully")
        else:
            logger.error("Failed to initialize AIMaak Chatbot")
        success2 = await initialize_db_and_schema()
        if success2:
            logger.info("Database and schema initialized.")
        else:
            logger.error("Failed to initialize database and schema.")
    except Exception as e:
        print(f"Startup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    app.state.redis.close()
    await app.state.http_client.aclose()

app.include_router(general_chat_router)
app.include_router(documents_router)
app.include_router(relational_db_router)

@app.get("/")
def root():
    return {"message": "AIMaak Chatbot API is running!"}
