from fastapi import FastAPI
from redis import Redis
import httpx
from documents.documents_service import initialize_qa_chat
from documents.documents_controller import router as doc_router
from general.general_chat_controller import router as general_chat_router

FILE_PATH = "./Lara_Fashion_QA.pdf"
VECTOR_STORE_PATH = "./vector_store"

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    try:
        app.state.redis = Redis(host="localhost", port=6379, decode_responses=True)
        app.state.http_client = httpx.AsyncClient()
        await initialize_qa_chat(FILE_PATH, VECTOR_STORE_PATH)
        print("AIMaak Chatbot pre-initialized successfully")
    except Exception as e:
        print(f"Startup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    app.state.redis.close()
    await app.state.http_client.aclose()

app.include_router(general_chat_router)
app.include_router(doc_router)

@app.get("/")
def root():
    return {"message": "AIMaak Chatbot API is running!"}