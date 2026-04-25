from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings

STRICT_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an HR assistant that answers questions about company policies.
Answer ONLY using the context provided below.
If the answer cannot be found in the context, respond with exactly:
"I don't have information about that in the policy document."
Do not use any outside knowledge. Do not make up information.

Context:
{context}""",
    ),
    ("human", "{question}"),
])


def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=settings.gemini_api_key,
        temperature=0,
    )


def format_docs(docs: list) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


async def generate_answer(question: str, context_docs: list) -> str:
    chain = STRICT_PROMPT | get_llm() | StrOutputParser()
    return await chain.ainvoke({
        "context": format_docs(context_docs),
        "question": question,
    })
