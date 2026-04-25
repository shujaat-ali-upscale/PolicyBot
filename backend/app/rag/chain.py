from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.config import settings

STRICT_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an HR assistant that answers questions about company policies.
Answer ONLY using the context provided below.
If the answer cannot be found in the context, respond with exactly:
"I don't have information about that in the policy document."
Do not use any outside knowledge. Do not make up information.

Format your response using proper markdown:
- Use bullet lists with "- " (hyphen + space) for items, never use ● or • characters
- Use **bold** for section headings or key terms
- Use short paragraphs — do not write one long block of text

Context:
{context}""",
    ),
    ("human", "{question}"),
])


def get_llm() -> ChatGroq:
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=settings.groq_api_key,
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
