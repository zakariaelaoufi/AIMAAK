from fastapi import APIRouter, Body, Request, status
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import os
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(
    prefix="/api-v1/prompt",
    tags=["chat"]
)

# Model setup
GEN_API_KEY = os.environ.get("GEN_API_KEY")
aitest = ChatGoogleGenerativeAI(
    google_api_key=GEN_API_KEY,
    temperature=0.4,
    model="gemini-2.0-flash"
)

# Prompt template
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


@router.get("", status_code=status.HTTP_200_OK)
async def get_chatbot_history(request: Request):
    redis = request.app.state.redis
    raw_history = redis.get("chatbot_history")
    if raw_history:
        history = json.loads(raw_history)
    else:
        history = []
    return {"history": history[-10:]}


@router.post("", status_code=status.HTTP_200_OK)
async def post_chatbot_response(request: Request, query: dict = Body(...)):
    redis = request.app.state.redis
    message = query.get("message")

    if not message:
        return {"error": "Missing 'message' in request body"}

    # Load chat history
    raw_history = redis.get("chatbot_history")
    if raw_history:
        history = [
            HumanMessage(**msg) if msg["type"] == "human" else AIMessage(**msg)
            for msg in json.loads(raw_history)
        ]
    else:
        history = []

    # Run prompt + model
    try:
        chain = prompt | aitest
        result = chain.invoke({"input": message, "chat_history": history[-10:]})
        answer = result.content or "Ma 3reftch."
    except Exception as e:
        return {"error": f"Failed to generate response: {e}"}

    # Save updated history
    history.append(HumanMessage(content=message))
    history.append(AIMessage(content=answer))

    redis.set("chatbot_history", json.dumps([
        {"type": "human", "content": msg.content} if isinstance(msg, HumanMessage)
        else {"type": "ai", "content": msg.content}
        for msg in history
    ]))

    return {"response": answer}
