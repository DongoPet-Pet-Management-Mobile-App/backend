
import os
import ast

from dotenv import load_dotenv
from fastapi import APIRouter
from typing import Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from app.models import ChatRequest, ChatResponse
from app.core.prompt import Prompt

router = APIRouter(prefix="/chat", tags=["chats"])

load_dotenv()

# Read from dotenv
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
PINECONE_KEY = os.getenv("PINECONE_KEY", "")
PINECONE_ENV = os.getenv("PINECONE_ENV", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "")

openai_llm = ChatOpenAI(
    model=OPENAI_MODEL_NAME,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=OPENAI_API_KEY,
)

def generate_openai_response(system_prompt: str, user_message: str) -> str:

    messages = [
        (
            "system",
            system_prompt
        ),
        (
            "user",
            user_message
        ),
    ]

    return openai_llm.invoke(messages).content


@router.post("/get_text_response", response_model=ChatResponse)
async def chat_with_openai(request: ChatRequest) -> ChatResponse:
    """
    Endpoint to generate a response using OpenAI gpt-4o model
    """
    system_prompt = Prompt.Chat_Assistant_System_Prompt
    user_input = request.message

    ai_response = generate_openai_response(system_prompt, user_input)
    print("AI result: ", ai_response)
    message = ai_response

    return ChatResponse(message=message)

@router.post("/get_text_response_rag", response_model=ChatResponse)
async def chat_with_rag(
    request: ChatRequest,
    context_prefix: Optional[str] = "",
    max_tokens: Optional[int] = 1000,
    temperature: Optional[float] = 0.7
) -> ChatResponse:
    """
    Endpoint to generate a response using RAG (Retrieval Augmented Generation)
    """
    try:
        # Initialize OpenAI
        chat = ChatOpenAI(
            model=OPENAI_MODEL_NAME,
            temperature=0.9,
            max_tokens=1000,
            api_key=OPENAI_API_KEY,
        )

        # Initialize Pinecone and vector store
        pc = Pinecone(api_key=PINECONE_KEY)
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectorstore = PineconeVectorStore(
            pinecone_api_key=PINECONE_KEY,
            index_name=PINECONE_INDEX,
            embedding=embeddings,
            namespace=PINECONE_NAMESPACE
        )
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": 4}  # Retrieve top 3 most relevant documents
        )

        # Get relevant documents
        retrieved_docs = retriever.invoke(request.message)
        retrieved_context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        # Create RAG prompt
        rag_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                    You are a Gig Platform assistant that provides accurate information based on the given context.
                    {context_prefix}

                    Make the response for drivers and provide some advice and guide using these answers.

                    Use the following retrieved information to answer the question:
                    {retrieved_context}

                    Create precise and structured questions about the user’s questions and requests. Your answers should be consistent, conversational, and clearly emphasize the answer you are providing to the user.
                    Response should be short less than 1~2 sentences. only return detail response if user require.
                    All of response should related about gig-worker.
                """
            ),
            (
                "user", "{query}")
        ])

        # Generate response
        chain = rag_prompt | chat | StrOutputParser()
        
        response = chain.invoke({
            "query": request.message,
            "context_prefix": context_prefix,
            "retrieved_context": retrieved_context
        })

        return ChatResponse(message=response)

    except Exception as e:
        return ChatResponse(message=f"Error: {str(e)}")

