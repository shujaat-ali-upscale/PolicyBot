from pydantic import BaseModel


class Source(BaseModel):
    text: str
    chunk_index: int


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
