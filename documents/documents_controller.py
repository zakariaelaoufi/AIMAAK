from fastapi import APIRouter, status, HTTPException
from fastapi.params import Body
from .documents_service import get_qa_chain, get_cache_status_service
from langchain_core.prompts import ChatPromptTemplate
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api-v1/docs",
    tags=["documents"]
)

prompt = ChatPromptTemplate.from_messages([
    ("system", (
        """You are AIMaak, a cutting-edge AI chatbot designed to understand and respond fluently in Moroccan Darija, 
        as well as Arabic, French, and English. Your main mission is to assist users with customer service–related 
        questions in the Moroccan context, offering clear, practical, and culturally aware answers.

        You must always respond in Moroccan Darija, regardless of the input language, to maintain consistency and user familiarity.

        When you are unsure about an answer or lack the necessary information, simply reply with:
        "Ma 3reftch." (I don't know)

        Stay helpful, respectful, and local.

        context: {context}
        """
    )),
    ("human", "{question}"),
])


@router.post("", status_code=status.HTTP_200_OK)
async def document_chatbot_response(query: dict = Body(...)):
    question = query.get("question")
    if not question:
        return {"error": "Missing 'question' in request body"}

    qa_chain = get_qa_chain()
    if qa_chain:
        response = qa_chain.invoke({"query": question})
        answer = response.get("result", "Ma 3reftch.")
        return answer
    else:
        logger.error(f"Failed to create the chain")
        raise HTTPException(
            status_code=503,
            detail="Document chatbot is not available"
        )


@router.get("/cache/status", status_code=status.HTTP_200_OK)
async def get_cache_status():
    return get_cache_status_service()
