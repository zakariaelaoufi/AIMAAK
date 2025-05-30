from fastapi import FastAPI
from redis import Redis
import httpx
import json
from fastapi.params import Body
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

GEN_API_KEY = os.environ.get("GEN_API_KEY")

REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT")

# Initialize model
aitest = ChatGoogleGenerativeAI(
    google_api_key=GEN_API_KEY,
    temperature=0.4,
    model="gemini-2.0-flash"
)

# Define prompt
prompt_message = """
You are AIMaak, a cutting-edge AI chatbot designed to understand and respond fluently in Moroccan Darija, as well as Arabic, French, and English. Your main mission is to assist users with customer service–related questions in the Moroccan context, offering clear, practical, and culturally aware answers.

You must always respond in Moroccan Darija, regardless of the input language, to maintain consistency and user familiarity.

When you are unsure about an answer or lack the necessary information, simply reply with:
"Ma 3reftch." (I don't know)

Stay helpful, respectful, and local.
history: {history}

input: {query}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", (
        """You are AIMaak, a cutting-edge AI chatbot designed to understand and respond fluently in Moroccan Darija, 
        as well as Arabic, French, and English. Your main mission is to assist users with customer service–related 
        questions in the Moroccan context, offering clear, practical, and culturally aware answers.

        You must always respond in Moroccan Darija, regardless of the input language, to maintain consistency and user familiarity.
        
        When you are unsure about an answer or lack the necessary information, simply reply with:
        "Ma 3reftch." (I don't know)
        
        Stay helpful, respectful, and local.
        """
    )),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])

chat_prompt = ChatPromptTemplate.from_template(prompt_message)

# Create FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def start_event():
    app.state.redis = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        username="default",
        password=REDIS_PASSWORD,
    )
    app.state.http_client = httpx.AsyncClient()

@app.on_event("shutdown")
async def shutdown_event():
    app.state.redis.close()
    await app.state.http_client.aclose()

@app.get("/api-v1/prompt")
async def get_chatbot_history():
    raw_history = app.state.redis.get("chatbot_history")
    if raw_history:
        history = json.loads(raw_history)
    else:
        history = []
    return {"history": history[-10:]}

@app.post("/api-v1/prompt")
async def post_chatbot_response(query: dict = Body(...)):
    message = query["message"]

    # Load history
    raw_history = app.state.redis.get("chatbot_history")
    if raw_history:
        history = [HumanMessage(**msg) if msg["type"] == "human" else AIMessage(**msg) for msg in json.loads(raw_history)]
    else:
        history = []

    # Generate response
    chain = prompt | aitest
    res = chain.invoke({"input": message, "chat_history": history[-10:]}).content

    # Update history
    history.append(HumanMessage(content=message))
    history.append(AIMessage(content=res))

    # Save updated history (serialize)
    serializable_history = [
        {"type": "human", "content": msg.content} if isinstance(msg, HumanMessage)
        else {"type": "ai", "content": msg.content}
        for msg in history
    ]
    app.state.redis.set("chatbot_history", json.dumps(serializable_history))
    del history
    return {"response": res}

@app.get("/")
def root():
    return {"message": "AIMaak Chatbot API is running"}
