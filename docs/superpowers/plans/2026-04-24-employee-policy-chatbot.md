# Employee Policy Chatbot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-stack employee policy chatbot where admins upload a PDF policy document and employees ask questions answered strictly from that document using RAG + Google Gemini.

**Architecture:** Clean FastAPI backend with modular routers (auth, chat, documents, users), SQLAlchemy async + Supabase PostgreSQL for users, LangChain PGVector on Supabase for embeddings, JWT role-based auth. React + TypeScript frontend with AuthContext, React Router, and role-based pages.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy asyncio, asyncpg, psycopg3, LangChain, langchain-google-genai, langchain-postgres (PGVector), Google Gemini 1.5 Flash + text-embedding-004, React 18, TypeScript, Vite, Tailwind CSS, React Router v6, Axios, jwt-decode.

---

## File Map

### Backend (complete rewrite of `backend/`)
```
backend/
  app/
    __init__.py
    main.py                      # FastAPI app factory, CORS, routers, lifespan
    config.py                    # Pydantic BaseSettings — all env vars
    database.py                  # SQLAlchemy async engine, session factory, Base, create_tables()
    models.py                    # User + PolicyDocument SQLAlchemy models
    auth/
      __init__.py
      router.py                  # POST /auth/register, /auth/login, GET /auth/me
      service.py                 # hash_password, verify_password, create_access_token, decode_token, register_user, authenticate_user
      schemas.py                 # RegisterRequest, LoginRequest, TokenResponse, UserResponse
      dependencies.py            # get_current_user(), require_admin() FastAPI deps
    chat/
      __init__.py
      router.py                  # POST /chat/
      service.py                 # get_rag_response(question) -> dict
      schemas.py                 # ChatRequest, ChatResponse, Source
    documents/
      __init__.py
      router.py                  # POST /documents/upload, GET /documents/status, DELETE /documents/
      service.py                 # process_pdf(), get_document_status(), delete_document()
      schemas.py                 # UploadResponse, DocumentStatus
    users/
      __init__.py
      router.py                  # GET /users/, DELETE /users/{user_id}
      service.py                 # list_users(), delete_user()
      schemas.py                 # UserItem, UserListResponse
    rag/
      __init__.py
      embeddings.py              # get_embeddings() — cached GoogleGenerativeAIEmbeddings
      vector_store.py            # get_vector_store(), upsert_chunks(), similarity_search(), delete_all_chunks()
      chain.py                   # get_llm(), STRICT_PROMPT, generate_answer()
  tests/
    __init__.py
    conftest.py                  # pytest fixtures: test app, async client, mock db
    test_auth.py                 # register, login, me, duplicate email, wrong password
    test_documents.py            # upload, status, delete — admin auth required
    test_chat.py                 # chat endpoint — mocked RAG
    test_users.py                # list users, delete user — admin only
  requirements.txt
  .env
  .env.example
```

### Frontend (complete rewrite of `frontend/src/`)
```
frontend/
  src/
    api/
      client.ts                  # Axios instance, JWT request interceptor, 401 response interceptor
      auth.ts                    # register(), login(), getMe() — typed wrappers
      chat.ts                    # sendMessage()
      documents.ts               # uploadDocument(), getDocumentStatus(), deleteDocument()
      users.ts                   # listUsers(), deleteUser()
    context/
      AuthContext.tsx             # JWT localStorage, decoded user state, login/logout
    components/
      Layout.tsx                  # Top nav with role-aware links and logout
      ProtectedRoute.tsx          # Redirect unauthenticated or wrong-role users
      ChatMessage.tsx             # Message bubble + expandable sources accordion
      DocumentUpload.tsx          # Drag-and-drop PDF upload with progress + status display
      UserTable.tsx               # Admin table: list users, delete per row
    pages/
      LoginPage.tsx
      RegisterPage.tsx
      ChatPage.tsx
      AdminPage.tsx               # Two tabs: Upload Policy + Manage Users
    App.tsx                       # BrowserRouter + Routes
    main.tsx
    index.css                     # Tailwind directives
  package.json                    # Add react-router-dom, jwt-decode
  .env
  .env.example
  .env.production.example
```

---

## Task 1: Clean Up & Create Backend Skeleton

**Files:**
- Delete: all files inside `backend/` except `venv/`
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py` (and all sub-package `__init__.py` files)

- [ ] **Step 1: Remove old backend source files**

```bash
cd /path/to/rag-chatbot
rm -rf backend/app backend/main.py backend/config.py backend/rag_chain.py backend/vector_store.py backend/embeddings.py backend/llm_provider.py backend/document_loader.py backend/chroma_db
```

- [ ] **Step 2: Create directory structure**

```bash
mkdir -p backend/app/auth backend/app/chat backend/app/documents backend/app/users backend/app/rag backend/tests
touch backend/app/__init__.py
touch backend/app/auth/__init__.py
touch backend/app/chat/__init__.py
touch backend/app/documents/__init__.py
touch backend/app/users/__init__.py
touch backend/app/rag/__init__.py
touch backend/tests/__init__.py
```

- [ ] **Step 3: Write `backend/requirements.txt`**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
psycopg[binary]==3.1.19
pydantic-settings==2.2.1
pydantic[email]==2.7.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
pypdf==4.2.0
langchain==0.2.1
langchain-google-genai==1.0.6
langchain-postgres==0.0.9
langchain-core==0.2.1
pytest==8.2.2
pytest-asyncio==0.23.7
httpx==0.27.0
python-dotenv==1.0.1
```

- [ ] **Step 4: Write `backend/.env.example`**

```
# Get from: https://aistudio.google.com → Get API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Get from: Supabase dashboard → Settings → Database → Connection string → URI (Transaction mode)
# Format: postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
DATABASE_URL=postgresql://postgres.xxxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=your_random_64_char_hex_secret_here

JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
FRONTEND_URL=http://localhost:5173
ENVIRONMENT=development
```

- [ ] **Step 5: Install dependencies in venv**

```bash
cd backend
source venv/bin/activate   # or: venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Expected: all packages install without errors.

- [ ] **Step 6: Commit**

```bash
git init   # if not already a git repo
git add backend/requirements.txt backend/.env.example backend/app/ backend/tests/
git commit -m "feat: initialize backend module structure"
```

---

## Task 2: Supabase Setup

**Goal:** Create Supabase project, enable pgvector extension, get DATABASE_URL.

- [ ] **Step 1: Create Supabase project**

1. Go to https://supabase.com → Sign up (free) → New project
2. Choose a name (e.g., `policy-chatbot`), set a strong database password, pick the closest region
3. Wait ~2 minutes for project to provision

- [ ] **Step 2: Enable pgvector extension**

In Supabase dashboard → SQL Editor → paste and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Expected output: `Success. No rows returned`

- [ ] **Step 3: Get DATABASE_URL**

Supabase dashboard → Settings → Database → Connection string → **Transaction mode** tab → copy the URI.

It looks like:
```
postgresql://postgres.abcdefgh:YourPassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

- [ ] **Step 4: Create `backend/.env` from example**

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and fill in:
# GEMINI_API_KEY — from aistudio.google.com
# DATABASE_URL — from step 3 above
# JWT_SECRET_KEY — run: python -c "import secrets; print(secrets.token_hex(32))"
```

- [ ] **Step 5: Get Gemini API Key**

1. Go to https://aistudio.google.com
2. Click "Get API key" → Create API key in new project
3. Copy the key → paste into `backend/.env` as `GEMINI_API_KEY`

---

## Task 3: Config, Database, Models

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`

- [ ] **Step 1: Write `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    frontend_url: str = "http://localhost:5173"
    environment: str = "development"

    @property
    def async_database_url(self) -> str:
        return self.database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace(
            "postgresql://", "postgresql+psycopg://"
        )

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 2: Write `backend/app/database.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.async_database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 3: Write `backend/app/models.py`**

```python
import enum
from datetime import datetime

from sqlalchemy import String, Enum as SAEnum, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    employee = "employee"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.employee, nullable=False)


class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
```

- [ ] **Step 4: Verify config loads without error**

```bash
cd backend
source venv/bin/activate
python -c "from app.config import settings; print(settings.environment)"
```

Expected: `development`

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/app/database.py backend/app/models.py
git commit -m "feat: add config, database engine, and SQLAlchemy models"
```

---

## Task 4: Auth Service + Tests

**Files:**
- Create: `backend/app/auth/schemas.py`
- Create: `backend/app/auth/service.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Write `backend/app/auth/schemas.py`**

```python
from pydantic import BaseModel, EmailStr

from app.models import UserRole


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.employee


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Write `backend/app/auth/service.py`**

```python
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, email: str, role: UserRole, name: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "name": name,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


async def register_user(
    db: AsyncSession, name: str, email: str, password: str, role: UserRole
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return user
```

- [ ] **Step 3: Write `backend/tests/conftest.py`**

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.database import Base, get_db
from app.models import User, UserRole
from app.auth.service import hash_password


TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest_asyncio.fixture(scope="session")
async def engine():
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db):
    from app.main import app
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db):
    user = User(
        name="Admin User",
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        role=UserRole.admin,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def employee_user(db):
    user = User(
        name="Employee User",
        email="employee@example.com",
        hashed_password=hash_password("emppass123"),
        role=UserRole.employee,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```

> Note: add `aiosqlite` to requirements.txt for the test SQLite driver:
> ```
> aiosqlite==0.20.0
> ```
> Run `pip install aiosqlite` in the venv.

- [ ] **Step 4: Write `backend/tests/test_auth.py`**

```python
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_employee(client: AsyncClient):
    res = await client.post("/auth/register", json={
        "name": "John Doe",
        "email": "john@example.com",
        "password": "secret123",
        "role": "employee",
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"name": "Jane", "email": "jane@example.com", "password": "pass", "role": "employee"}
    await client.post("/auth/register", json=payload)
    res = await client.post("/auth/register", json=payload)
    assert res.status_code == 409
    assert res.json()["detail"] == "Email already registered"


async def test_login_success(client: AsyncClient, employee_user):
    res = await client.post("/auth/login", json={
        "email": "employee@example.com",
        "password": "emppass123",
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


async def test_login_wrong_password(client: AsyncClient, employee_user):
    res = await client.post("/auth/login", json={
        "email": "employee@example.com",
        "password": "wrongpassword",
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


async def test_me_returns_user(client: AsyncClient, admin_user):
    login_res = await client.post("/auth/login", json={
        "email": "admin@example.com",
        "password": "adminpass123",
    })
    token = login_res.json()["access_token"]
    res = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "admin@example.com"
    assert data["role"] == "admin"


async def test_me_no_token(client: AsyncClient):
    res = await client.get("/auth/me")
    assert res.status_code == 403
```

- [ ] **Step 5: Write `backend/app/auth/dependencies.py`** (needed for tests to run)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserRole
from app.auth.service import decode_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    user_id = int(payload.get("sub"))
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user
```

- [ ] **Step 6: Write `backend/app/auth/router.py`** (needed for tests to run)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.auth.dependencies import get_current_user
from app.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.auth.service import register_user, authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, body.name, body.email, body.password, body.role)
    token = create_access_token(user.id, user.email, user.role, user.name)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.email, body.password)
    token = create_access_token(user.id, user.email, user.role, user.name)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
```

- [ ] **Step 7: Write minimal `backend/app/main.py`** (needed for tests to run)

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.auth.router import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(title="Employee Policy Chatbot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 8: Write `backend/pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 9: Run auth tests**

```bash
cd backend
source venv/bin/activate
pytest tests/test_auth.py -v
```

Expected output:
```
tests/test_auth.py::test_register_employee PASSED
tests/test_auth.py::test_register_duplicate_email PASSED
tests/test_auth.py::test_login_success PASSED
tests/test_auth.py::test_login_wrong_password PASSED
tests/test_auth.py::test_me_returns_user PASSED
tests/test_auth.py::test_me_no_token PASSED
6 passed
```

- [ ] **Step 10: Commit**

```bash
git add backend/app/auth/ backend/tests/ backend/pytest.ini
git commit -m "feat: auth service, router, and passing tests"
```

---

## Task 5: RAG — Embeddings, Vector Store, Chain

**Files:**
- Create: `backend/app/rag/embeddings.py`
- Create: `backend/app/rag/vector_store.py`
- Create: `backend/app/rag/chain.py`

- [ ] **Step 1: Write `backend/app/rag/embeddings.py`**

```python
from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=settings.gemini_api_key,
    )
```

- [ ] **Step 2: Write `backend/app/rag/vector_store.py`**

```python
from langchain_core.documents import Document
from langchain_postgres import PGVector

from app.config import settings
from app.rag.embeddings import get_embeddings

COLLECTION_NAME = "policy_chunks"


def get_vector_store() -> PGVector:
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=COLLECTION_NAME,
        connection=settings.sync_database_url,
        use_jsonb=True,
    )


def upsert_chunks(chunks: list[Document]) -> int:
    store = get_vector_store()
    store.delete_collection()
    store.create_collection()
    store.add_documents(chunks)
    return len(chunks)


def similarity_search(query: str, k: int = 4) -> list[Document]:
    store = get_vector_store()
    return store.similarity_search(query, k=k)


def delete_all_chunks() -> None:
    store = get_vector_store()
    store.delete_collection()
```

- [ ] **Step 3: Write `backend/app/rag/chain.py`**

```python
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
        model="gemini-1.5-flash",
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
```

- [ ] **Step 4: Smoke-test embeddings against Gemini API**

```bash
cd backend
source venv/bin/activate
python -c "
from app.rag.embeddings import get_embeddings
emb = get_embeddings()
result = emb.embed_query('hello world')
print(f'Embedding length: {len(result)}')
"
```

Expected: `Embedding length: 768`

- [ ] **Step 5: Commit**

```bash
git add backend/app/rag/
git commit -m "feat: RAG embeddings, vector store, and Gemini chain"
```

---

## Task 6: Documents Service + Router + Tests

**Files:**
- Create: `backend/app/documents/schemas.py`
- Create: `backend/app/documents/service.py`
- Create: `backend/app/documents/router.py`
- Create: `backend/tests/test_documents.py`

- [ ] **Step 1: Write `backend/app/documents/schemas.py`**

```python
from datetime import datetime

from pydantic import BaseModel


class UploadResponse(BaseModel):
    success: bool
    message: str
    chunks_created: int


class DocumentStatus(BaseModel):
    has_document: bool
    filename: str | None = None
    chunk_count: int | None = None
    uploaded_at: datetime | None = None
```

- [ ] **Step 2: Write `backend/app/documents/service.py`**

```python
import os
import tempfile

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pypdf import PdfReader
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PolicyDocument
from app.rag.vector_store import delete_all_chunks, upsert_chunks

TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
)


async def process_pdf(file_bytes: bytes, filename: str, db: AsyncSession) -> int:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        reader = PdfReader(tmp_path)
        full_text = "\n\n".join(
            page.extract_text() or "" for page in reader.pages
        ).strip()
    finally:
        os.unlink(tmp_path)

    if not full_text:
        raise ValueError("PDF appears to be empty or unreadable")

    raw_doc = Document(page_content=full_text, metadata={"source": filename})
    chunks = TEXT_SPLITTER.split_documents([raw_doc])
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    chunk_count = upsert_chunks(chunks)

    await db.execute(delete(PolicyDocument))
    db.add(PolicyDocument(filename=filename, chunk_count=chunk_count))
    await db.commit()

    return chunk_count


async def get_document_status(db: AsyncSession) -> dict:
    result = await db.execute(
        select(PolicyDocument).order_by(PolicyDocument.uploaded_at.desc()).limit(1)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        return {"has_document": False}
    return {
        "has_document": True,
        "filename": doc.filename,
        "chunk_count": doc.chunk_count,
        "uploaded_at": doc.uploaded_at,
    }


async def delete_document(db: AsyncSession) -> None:
    delete_all_chunks()
    await db.execute(delete(PolicyDocument))
    await db.commit()
```

- [ ] **Step 3: Write `backend/app/documents/router.py`**

```python
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database import get_db
from app.documents.schemas import DocumentStatus, UploadResponse
from app.documents.service import delete_document, get_document_status, process_pdf
from app.models import User

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    file_bytes = await file.read()
    chunk_count = await process_pdf(file_bytes, file.filename, db)
    return UploadResponse(
        success=True,
        message="Document processed successfully",
        chunks_created=chunk_count,
    )


@router.get("/status", response_model=DocumentStatus)
async def document_status(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    status = await get_document_status(db)
    return DocumentStatus(**status)


@router.delete("/")
async def delete_all_documents(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await delete_document(db)
    return {"success": True, "message": "Document deleted successfully"}
```

- [ ] **Step 4: Write `backend/tests/test_documents.py`**

```python
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _get_admin_token(client: AsyncClient) -> str:
    res = await client.post("/auth/login", json={
        "email": "admin@example.com",
        "password": "adminpass123",
    })
    return res.json()["access_token"]


async def _get_employee_token(client: AsyncClient) -> str:
    res = await client.post("/auth/login", json={
        "email": "employee@example.com",
        "password": "emppass123",
    })
    return res.json()["access_token"]


async def test_upload_requires_admin(client: AsyncClient, employee_user):
    token = await _get_employee_token(client)
    res = await client.post(
        "/documents/upload",
        files={"file": ("policy.pdf", b"fake", "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


async def test_upload_rejects_non_pdf(client: AsyncClient, admin_user):
    token = await _get_admin_token(client)
    res = await client.post(
        "/documents/upload",
        files={"file": ("policy.txt", b"some text", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "PDF" in res.json()["detail"]


async def test_status_no_document(client: AsyncClient, admin_user):
    with patch("app.documents.service.upsert_chunks", return_value=0):
        token = await _get_admin_token(client)
        res = await client.get(
            "/documents/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["has_document"] is False


async def test_upload_success(client: AsyncClient, admin_user):
    with patch("app.documents.service.upsert_chunks", return_value=5), \
         patch("app.documents.service.PdfReader") as mock_reader:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Employee leave policy. Employees get 20 days."
        mock_reader.return_value.pages = [mock_page]

        token = await _get_admin_token(client)
        fake_pdf = BytesIO(b"%PDF-1.4 fake content")
        res = await client.post(
            "/documents/upload",
            files={"file": ("policy.pdf", fake_pdf, "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert res.json()["chunks_created"] == 5
```

- [ ] **Step 5: Add documents router to `backend/app/main.py`**

```python
# Add to existing imports:
from app.documents.router import router as documents_router

# Add after existing app.include_router(auth_router):
app.include_router(documents_router)
```

- [ ] **Step 6: Run documents tests**

```bash
cd backend
pytest tests/test_documents.py -v
```

Expected: 4 tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/app/documents/ backend/tests/test_documents.py backend/app/main.py
git commit -m "feat: documents upload, status, delete with tests"
```

---

## Task 7: Chat Service + Router + Tests

**Files:**
- Create: `backend/app/chat/schemas.py`
- Create: `backend/app/chat/service.py`
- Create: `backend/app/chat/router.py`
- Create: `backend/tests/test_chat.py`

- [ ] **Step 1: Write `backend/app/chat/schemas.py`**

```python
from pydantic import BaseModel


class Source(BaseModel):
    text: str
    chunk_index: int


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
```

- [ ] **Step 2: Write `backend/app/chat/service.py`**

```python
from langchain_core.documents import Document

from app.chat.schemas import Source
from app.rag.chain import generate_answer
from app.rag.vector_store import similarity_search

NO_INFO_RESPONSE = "I don't have information about that in the policy document."


async def get_rag_response(question: str) -> dict:
    docs: list[Document] = similarity_search(question, k=4)

    if not docs:
        return {"answer": NO_INFO_RESPONSE, "sources": []}

    answer = await generate_answer(question, docs)
    sources = [
        Source(
            text=doc.page_content[:300],
            chunk_index=doc.metadata.get("chunk_index", 0),
        )
        for doc in docs
    ]
    return {"answer": answer, "sources": sources}
```

- [ ] **Step 3: Write `backend/app/chat/router.py`**

```python
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.chat.schemas import ChatRequest, ChatResponse
from app.chat.service import get_rag_response
from app.models import User

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    _: User = Depends(get_current_user),
):
    result = await get_rag_response(body.question)
    return ChatResponse(**result)
```

- [ ] **Step 4: Write `backend/tests/test_chat.py`**

```python
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from langchain_core.documents import Document

pytestmark = pytest.mark.asyncio


async def _get_token(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post("/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


async def test_chat_requires_auth(client: AsyncClient):
    res = await client.post("/chat/", json={"question": "What is the leave policy?"})
    assert res.status_code == 403


async def test_chat_returns_answer(client: AsyncClient, employee_user):
    mock_docs = [
        Document(
            page_content="Employees receive 20 days of annual leave.",
            metadata={"chunk_index": 0},
        )
    ]
    with patch("app.chat.service.similarity_search", return_value=mock_docs), \
         patch("app.chat.service.generate_answer", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "Employees receive 20 days of annual leave per year."

        token = await _get_token(client, "employee@example.com", "emppass123")
        res = await client.post(
            "/chat/",
            json={"question": "How many leave days do employees get?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "answer" in data
        assert "sources" in data
        assert len(data["sources"]) == 1
        assert data["sources"][0]["chunk_index"] == 0


async def test_chat_no_docs_returns_fallback(client: AsyncClient, employee_user):
    with patch("app.chat.service.similarity_search", return_value=[]):
        token = await _get_token(client, "employee@example.com", "emppass123")
        res = await client.post(
            "/chat/",
            json={"question": "What is the overtime policy?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert "don't have information" in res.json()["answer"]
```

- [ ] **Step 5: Add chat router to `backend/app/main.py`**

```python
# Add to imports:
from app.chat.router import router as chat_router

# Add include:
app.include_router(chat_router)
```

- [ ] **Step 6: Run chat tests**

```bash
cd backend
pytest tests/test_chat.py -v
```

Expected: 3 tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/app/chat/ backend/tests/test_chat.py backend/app/main.py
git commit -m "feat: chat RAG endpoint with tests"
```

---

## Task 8: Users Service + Router + Tests

**Files:**
- Create: `backend/app/users/schemas.py`
- Create: `backend/app/users/service.py`
- Create: `backend/app/users/router.py`
- Create: `backend/tests/test_users.py`

- [ ] **Step 1: Write `backend/app/users/schemas.py`**

```python
from pydantic import BaseModel

from app.models import UserRole


class UserItem(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: list[UserItem]
    total: int
```

- [ ] **Step 2: Write `backend/app/users/service.py`**

```python
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.id))
    return list(result.scalars().all())


async def delete_user(db: AsyncSession, user_id: int) -> None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
```

- [ ] **Step 3: Write `backend/app/users/router.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import User
from app.users.schemas import UserItem, UserListResponse
from app.users.service import delete_user, list_users

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=UserListResponse)
async def get_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    users = await list_users(db)
    return UserListResponse(users=users, total=len(users))


@router.delete("/{user_id}")
async def remove_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await delete_user(db, user_id)
    return {"success": True, "message": "User deleted"}
```

- [ ] **Step 4: Write `backend/tests/test_users.py`**

```python
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _get_admin_token(client: AsyncClient) -> str:
    res = await client.post("/auth/login", json={
        "email": "admin@example.com", "password": "adminpass123"
    })
    return res.json()["access_token"]


async def _get_employee_token(client: AsyncClient) -> str:
    res = await client.post("/auth/login", json={
        "email": "employee@example.com", "password": "emppass123"
    })
    return res.json()["access_token"]


async def test_list_users_admin_only(client: AsyncClient, employee_user):
    token = await _get_employee_token(client)
    res = await client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


async def test_list_users_returns_all(client: AsyncClient, admin_user, employee_user):
    token = await _get_admin_token(client)
    res = await client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    emails = [u["email"] for u in data["users"]]
    assert "admin@example.com" in emails
    assert "employee@example.com" in emails


async def test_delete_user_not_found(client: AsyncClient, admin_user):
    token = await _get_admin_token(client)
    res = await client.delete("/users/99999", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404
```

- [ ] **Step 5: Update `backend/app/main.py`** to include all routers

Replace entire `backend/app/main.py` with the final version:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.chat.router import router as chat_router
from app.config import settings
from app.database import create_tables
from app.documents.router import router as documents_router
from app.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(title="Employee Policy Chatbot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(users_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Run all backend tests**

```bash
cd backend
pytest -v
```

Expected: all tests pass. Fix any failures before continuing.

- [ ] **Step 7: Run backend server manually to verify**

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/health — expect `{"status": "ok"}`
Visit http://localhost:8000/docs — expect Swagger UI with all endpoints.

- [ ] **Step 8: Commit**

```bash
git add backend/app/users/ backend/tests/test_users.py backend/app/main.py
git commit -m "feat: users management, finalized main.py, all tests passing"
```

---

## Task 9: Frontend Setup

**Files:**
- Modify: `frontend/package.json` — add react-router-dom, jwt-decode
- Create: `frontend/.env`
- Create: `frontend/.env.example`

- [ ] **Step 1: Update `frontend/package.json` dependencies**

Open `frontend/package.json` and update the `dependencies` section to include:

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.24.0",
    "axios": "^1.7.2",
    "jwt-decode": "^4.0.0",
    "lucide-react": "^0.395.0",
    "react-markdown": "^9.0.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.39",
    "tailwindcss": "^3.4.4",
    "typescript": "^5.5.2",
    "vite": "^5.3.1"
  }
}
```

- [ ] **Step 2: Install dependencies**

```bash
cd frontend
npm install
```

Expected: no errors, `node_modules` updated.

- [ ] **Step 3: Create `frontend/.env`**

```
VITE_API_URL=http://localhost:8000
```

- [ ] **Step 4: Create `frontend/.env.example`**

```
# Local development
VITE_API_URL=http://localhost:8000

# Production — set to your Render backend URL
# VITE_API_URL=https://your-app.onrender.com
```

- [ ] **Step 5: Delete old frontend source files**

```bash
cd frontend/src
rm -f App.tsx api.ts components/ChatMessage.tsx components/DocumentPanel.tsx
rm -rf components
```

- [ ] **Step 6: Recreate clean directory structure**

```bash
mkdir -p src/api src/context src/components src/pages
```

- [ ] **Step 7: Update `frontend/src/index.css`**

Replace entire contents with:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 8: Commit**

```bash
cd ..
git add frontend/package.json frontend/.env.example frontend/src/index.css
git commit -m "feat: frontend dependency setup and clean structure"
```

---

## Task 10: Frontend API Client Layer

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/auth.ts`
- Create: `frontend/src/api/chat.ts`
- Create: `frontend/src/api/documents.ts`
- Create: `frontend/src/api/users.ts`

- [ ] **Step 1: Write `frontend/src/api/client.ts`**

```typescript
import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default client;
```

- [ ] **Step 2: Write `frontend/src/api/auth.ts`**

```typescript
import client from './client';

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  role: 'admin' | 'employee';
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'employee';
}

export const register = (payload: RegisterPayload) =>
  client.post<TokenResponse>('/auth/register', payload);

export const login = (payload: LoginPayload) =>
  client.post<TokenResponse>('/auth/login', payload);

export const getMe = () =>
  client.get<User>('/auth/me');
```

- [ ] **Step 3: Write `frontend/src/api/chat.ts`**

```typescript
import client from './client';

export interface Source {
  text: string;
  chunk_index: number;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}

export const sendMessage = (question: string) =>
  client.post<ChatResponse>('/chat/', { question });
```

- [ ] **Step 4: Write `frontend/src/api/documents.ts`**

```typescript
import client from './client';

export interface UploadResponse {
  success: boolean;
  message: string;
  chunks_created: number;
}

export interface DocumentStatus {
  has_document: boolean;
  filename?: string;
  chunk_count?: number;
  uploaded_at?: string;
}

export const uploadDocument = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return client.post<UploadResponse>('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const getDocumentStatus = () =>
  client.get<DocumentStatus>('/documents/status');

export const deleteDocument = () =>
  client.delete('/documents/');
```

- [ ] **Step 5: Write `frontend/src/api/users.ts`**

```typescript
import client from './client';
import type { User } from './auth';

export interface UserListResponse {
  users: User[];
  total: number;
}

export const listUsers = () =>
  client.get<UserListResponse>('/users/');

export const deleteUser = (userId: number) =>
  client.delete(`/users/${userId}`);
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/
git commit -m "feat: typed API client layer with axios interceptors"
```

---

## Task 11: AuthContext + ProtectedRoute + Layout

**Files:**
- Create: `frontend/src/context/AuthContext.tsx`
- Create: `frontend/src/components/ProtectedRoute.tsx`
- Create: `frontend/src/components/Layout.tsx`

- [ ] **Step 1: Write `frontend/src/context/AuthContext.tsx`**

```typescript
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { jwtDecode } from 'jwt-decode';

export interface AuthUser {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'employee';
}

interface JWTPayload {
  sub: string;
  email: string;
  role: 'admin' | 'employee';
  name: string;
  exp: number;
}

interface AuthContextType {
  user: AuthUser | null;
  login: (token: string) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const payload = jwtDecode<JWTPayload>(token);
        if (payload.exp * 1000 > Date.now()) {
          setUser({
            id: parseInt(payload.sub),
            email: payload.email,
            role: payload.role,
            name: payload.name,
          });
        } else {
          localStorage.removeItem('access_token');
        }
      } catch {
        localStorage.removeItem('access_token');
      }
    }
    setIsLoading(false);
  }, []);

  const login = (token: string) => {
    localStorage.setItem('access_token', token);
    const payload = jwtDecode<JWTPayload>(token);
    setUser({
      id: parseInt(payload.sub),
      email: payload.email,
      role: payload.role,
      name: payload.name,
    });
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
```

- [ ] **Step 2: Write `frontend/src/components/ProtectedRoute.tsx`**

```typescript
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'employee';
}

export function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500 text-sm">Loading...</p>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  if (requiredRole === 'admin' && user.role !== 'admin') {
    return <Navigate to="/chat" replace />;
  }

  return <>{children}</>;
}
```

- [ ] **Step 3: Write `frontend/src/components/Layout.tsx`**

```typescript
import { Link, useNavigate } from 'react-router-dom';
import { LogOut, MessageSquare, Settings } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-6">
            <span className="text-lg font-bold text-[#29ABE2]">PolicyBot</span>
            <Link
              to="/chat"
              className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-[#29ABE2] transition-colors"
            >
              <MessageSquare size={15} />
              Chat
            </Link>
            {user?.role === 'admin' && (
              <Link
                to="/admin"
                className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-[#29ABE2] transition-colors"
              >
                <Settings size={15} />
                Admin
              </Link>
            )}
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">{user?.email}</span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-500 transition-colors"
            >
              <LogOut size={15} />
              Logout
            </button>
          </div>
        </div>
      </nav>
      <main>{children}</main>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/context/ frontend/src/components/ProtectedRoute.tsx frontend/src/components/Layout.tsx
git commit -m "feat: AuthContext, ProtectedRoute, Layout components"
```

---

## Task 12: Login + Register Pages

**Files:**
- Create: `frontend/src/pages/LoginPage.tsx`
- Create: `frontend/src/pages/RegisterPage.tsx`

- [ ] **Step 1: Write `frontend/src/pages/LoginPage.tsx`**

```typescript
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import { login } from '../api/auth';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { login: authLogin, user } = useAuth();
  const navigate = useNavigate();

  if (user) {
    navigate(user.role === 'admin' ? '/admin' : '/chat', { replace: true });
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const res = await login({ email, password });
      authLogin(res.data.access_token);
      const { jwtDecode } = await import('jwt-decode');
      const payload = jwtDecode<{ role: string }>(res.data.access_token);
      navigate(payload.role === 'admin' ? '/admin' : '/chat', { replace: true });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setError(msg || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-[#29ABE2] to-[#1e90c7] px-6 py-6">
            <h1 className="text-2xl font-bold text-white">PolicyBot</h1>
            <p className="text-blue-100 text-sm mt-1">Sign in to your account</p>
          </div>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                <AlertCircle size={16} className="text-red-600 flex-shrink-0" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#29ABE2] focus:border-[#29ABE2] transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#29ABE2] focus:border-[#29ABE2] transition-all"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 bg-[#29ABE2] hover:bg-[#2196cc] text-white rounded-lg text-sm font-medium transition-all duration-200 disabled:opacity-50"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
            <p className="text-center text-sm text-gray-500">
              Don&apos;t have an account?{' '}
              <Link to="/register" className="text-[#29ABE2] hover:underline font-medium">
                Register
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write `frontend/src/pages/RegisterPage.tsx`**

```typescript
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import { register } from '../api/auth';
import { useAuth } from '../context/AuthContext';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'employee' | 'admin'>('employee');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { login: authLogin } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const res = await register({ name, email, password, role });
      authLogin(res.data.access_token);
      navigate(role === 'admin' ? '/admin' : '/chat', { replace: true });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setError(msg || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden">
          <div className="bg-gradient-to-r from-[#29ABE2] to-[#1e90c7] px-6 py-6">
            <h1 className="text-2xl font-bold text-white">PolicyBot</h1>
            <p className="text-blue-100 text-sm mt-1">Create your account</p>
          </div>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                <AlertCircle size={16} className="text-red-600 flex-shrink-0" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#29ABE2] focus:border-[#29ABE2] transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#29ABE2] focus:border-[#29ABE2] transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                className="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#29ABE2] focus:border-[#29ABE2] transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as 'employee' | 'admin')}
                className="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#29ABE2] focus:border-[#29ABE2] bg-white transition-all"
              >
                <option value="employee">Employee</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 bg-[#29ABE2] hover:bg-[#2196cc] text-white rounded-lg text-sm font-medium transition-all duration-200 disabled:opacity-50"
            >
              {isLoading ? 'Creating account...' : 'Create Account'}
            </button>
            <p className="text-center text-sm text-gray-500">
              Already have an account?{' '}
              <Link to="/login" className="text-[#29ABE2] hover:underline font-medium">
                Sign In
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/LoginPage.tsx frontend/src/pages/RegisterPage.tsx
git commit -m "feat: login and register pages"
```

---

## Task 13: ChatMessage Component + ChatPage

**Files:**
- Create: `frontend/src/components/ChatMessage.tsx`
- Create: `frontend/src/pages/ChatPage.tsx`

- [ ] **Step 1: Write `frontend/src/components/ChatMessage.tsx`**

```typescript
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ChevronDown, ChevronRight, FileText, User, Bot } from 'lucide-react';
import type { Source } from '../api/chat';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

export function ChatMessage({ role, content, sources = [] }: ChatMessageProps) {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const isUser = role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-[#29ABE2]' : 'bg-gray-200'
      }`}>
        {isUser
          ? <User size={16} className="text-white" />
          : <Bot size={16} className="text-gray-600" />
        }
      </div>
      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'bg-[#29ABE2] text-white rounded-tr-sm'
            : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm shadow-sm'
        }`}>
          {isUser ? (
            <p>{content}</p>
          ) : (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          )}
        </div>
        {!isUser && sources.length > 0 && (
          <div className="w-full">
            <button
              onClick={() => setSourcesOpen(!sourcesOpen)}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-[#29ABE2] transition-colors"
            >
              {sourcesOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
              {sources.length} source{sources.length > 1 ? 's' : ''}
            </button>
            {sourcesOpen && (
              <div className="mt-2 space-y-2">
                {sources.map((source, i) => (
                  <div key={i} className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <div className="flex items-center gap-1.5 mb-1">
                      <FileText size={11} className="text-gray-400" />
                      <span className="text-xs text-gray-400 font-medium">
                        Chunk {source.chunk_index + 1}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 leading-relaxed">{source.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write `frontend/src/pages/ChatPage.tsx`**

```typescript
import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { sendMessage } from '../api/chat';
import { ChatMessage } from '../components/ChatMessage';
import { Layout } from '../components/Layout';
import type { Source } from '../api/chat';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I can answer questions about your company policy document. What would you like to know?',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const question = input.trim();
    if (!question || isLoading) return;

    setInput('');
    setError(null);
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: 'user', content: question },
    ]);
    setIsLoading(true);

    try {
      const res = await sendMessage(question);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: res.data.answer,
          sources: res.data.sources,
        },
      ]);
    } catch {
      setError('Failed to get a response. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Layout>
      <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-65px)]">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              role={msg.role}
              content={msg.content}
              sources={msg.sources}
            />
          ))}
          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                <Loader2 size={16} className="text-gray-500 animate-spin" />
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                <div className="flex gap-1 items-center h-4">
                  <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          {error && (
            <p className="text-center text-sm text-red-500">{error}</p>
          )}
          <div ref={bottomRef} />
        </div>
        <div className="border-t border-gray-200 bg-white p-4">
          <div className="flex gap-3 items-end">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about company policy..."
              rows={1}
              className="flex-1 resize-none rounded-xl border border-gray-300 py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#29ABE2] focus:border-[#29ABE2] transition-all max-h-32"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="p-3 bg-[#29ABE2] hover:bg-[#2196cc] text-white rounded-xl transition-all duration-200 disabled:opacity-40 flex-shrink-0"
            >
              <Send size={18} />
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2 text-center">
            Press Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>
    </Layout>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ChatMessage.tsx frontend/src/pages/ChatPage.tsx
git commit -m "feat: ChatMessage component and ChatPage"
```

---

## Task 14: DocumentUpload + UserTable + AdminPage

**Files:**
- Create: `frontend/src/components/DocumentUpload.tsx`
- Create: `frontend/src/components/UserTable.tsx`
- Create: `frontend/src/pages/AdminPage.tsx`

- [ ] **Step 1: Write `frontend/src/components/DocumentUpload.tsx`**

```typescript
import { useState, useCallback } from 'react';
import { Upload, FileText, Trash2, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadDocument, deleteDocument } from '../api/documents';
import type { DocumentStatus } from '../api/documents';

interface DocumentUploadProps {
  status: DocumentStatus | null;
  onStatusChange: () => void;
}

export function DocumentUpload({ status, onStatusChange }: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [uploadResult, setUploadResult] = useState<{ success: boolean; message: string } | null>(null);

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadResult({ success: false, message: 'Only PDF files are supported.' });
      return;
    }
    setIsUploading(true);
    setUploadResult(null);
    try {
      const res = await uploadDocument(file);
      setUploadResult({
        success: true,
        message: `Uploaded successfully — ${res.data.chunks_created} chunks created.`,
      });
      onStatusChange();
    } catch {
      setUploadResult({ success: false, message: 'Upload failed. Please try again.' });
    } finally {
      setIsUploading(false);
    }
  }, [onStatusChange]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleDelete = async () => {
    if (!confirm('Delete the policy document? Employees will not be able to get answers until a new document is uploaded.')) return;
    setIsDeleting(true);
    try {
      await deleteDocument();
      onStatusChange();
      setUploadResult(null);
    } catch {
      setUploadResult({ success: false, message: 'Delete failed. Please try again.' });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-4">
      {status?.has_document && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CheckCircle size={18} className="text-emerald-600 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-emerald-800">{status.filename}</p>
              <p className="text-xs text-emerald-600">{status.chunk_count} chunks indexed</p>
            </div>
          </div>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="flex items-center gap-1.5 text-sm text-red-500 hover:text-red-700 transition-colors disabled:opacity-50"
          >
            <Trash2 size={14} />
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      )}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors ${
          isDragging
            ? 'border-[#29ABE2] bg-blue-50'
            : 'border-gray-300 hover:border-[#29ABE2] bg-white'
        }`}
      >
        <Upload size={32} className="text-gray-400 mx-auto mb-3" />
        <p className="text-sm font-medium text-gray-700 mb-1">
          Drag & drop your policy PDF here
        </p>
        <p className="text-xs text-gray-400 mb-4">or click to browse</p>
        <label className="cursor-pointer">
          <span className="px-4 py-2 bg-[#29ABE2] hover:bg-[#2196cc] text-white text-sm rounded-lg transition-colors">
            {isUploading ? 'Uploading...' : 'Choose File'}
          </span>
          <input
            type="file"
            accept=".pdf"
            className="hidden"
            disabled={isUploading}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
              e.target.value = '';
            }}
          />
        </label>
      </div>
      {uploadResult && (
        <div className={`flex items-center gap-2 p-3 rounded-lg border text-sm ${
          uploadResult.success
            ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
            : 'bg-red-50 border-red-200 text-red-700'
        }`}>
          {uploadResult.success
            ? <CheckCircle size={15} className="flex-shrink-0" />
            : <AlertCircle size={15} className="flex-shrink-0" />
          }
          {uploadResult.message}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Write `frontend/src/components/UserTable.tsx`**

```typescript
import { useState } from 'react';
import { Trash2, ShieldCheck, User } from 'lucide-react';
import { deleteUser } from '../api/users';
import type { User as UserType } from '../api/auth';

interface UserTableProps {
  users: UserType[];
  onUserDeleted: () => void;
}

export function UserTable({ users, onUserDeleted }: UserTableProps) {
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const handleDelete = async (user: UserType) => {
    if (!confirm(`Delete user ${user.email}? This cannot be undone.`)) return;
    setDeletingId(user.id);
    try {
      await deleteUser(user.id);
      onUserDeleted();
    } finally {
      setDeletingId(null);
    }
  };

  if (users.length === 0) {
    return <p className="text-sm text-gray-500 text-center py-8">No users found.</p>;
  }

  return (
    <div className="overflow-hidden rounded-xl border border-gray-100">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-100">
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Name</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Email</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Role</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50 bg-white">
          {users.map((user) => (
            <tr key={user.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 font-medium text-gray-800">{user.name}</td>
              <td className="px-4 py-3 text-gray-600">{user.email}</td>
              <td className="px-4 py-3">
                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold ${
                  user.role === 'admin'
                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                    : 'bg-gray-50 text-gray-600 border border-gray-200'
                }`}>
                  {user.role === 'admin'
                    ? <ShieldCheck size={11} />
                    : <User size={11} />
                  }
                  {user.role}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <button
                  onClick={() => handleDelete(user)}
                  disabled={deletingId === user.id}
                  className="text-gray-400 hover:text-red-500 transition-colors disabled:opacity-40"
                  title="Delete user"
                >
                  <Trash2 size={15} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 3: Write `frontend/src/pages/AdminPage.tsx`**

```typescript
import { useState, useEffect, useCallback } from 'react';
import { Upload, Users, Loader2, AlertCircle } from 'lucide-react';
import { getDocumentStatus } from '../api/documents';
import { listUsers } from '../api/users';
import { DocumentUpload } from '../components/DocumentUpload';
import { UserTable } from '../components/UserTable';
import { Layout } from '../components/Layout';
import type { DocumentStatus } from '../api/documents';
import type { User } from '../api/auth';

type Tab = 'upload' | 'users';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<Tab>('upload');
  const [docStatus, setDocStatus] = useState<DocumentStatus | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [statusRes, usersRes] = await Promise.all([
        getDocumentStatus(),
        listUsers(),
      ]);
      setDocStatus(statusRes.data);
      setUsers(usersRes.data.users);
    } catch {
      setError('Failed to load data. Please refresh.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'upload', label: 'Policy Document', icon: <Upload size={15} /> },
    { id: 'users', label: `Users (${users.length})`, icon: <Users size={15} /> },
  ];

  return (
    <Layout>
      <div className="max-w-3xl mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
          <p className="text-gray-500 text-sm mt-1">Manage the policy document and user accounts</p>
        </div>
        {error && (
          <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2">
            <AlertCircle size={16} className="text-red-600 flex-shrink-0" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
        <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-xl w-fit">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-white text-[#29ABE2] shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 size={24} className="text-[#29ABE2] animate-spin" />
          </div>
        ) : (
          <>
            {activeTab === 'upload' && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <h2 className="text-base font-semibold text-gray-800 mb-4">Upload Policy Document</h2>
                <p className="text-sm text-gray-500 mb-5">
                  Upload a PDF of your company policy. Employees can ask questions about it in the chat.
                  Uploading a new document replaces the current one.
                </p>
                <DocumentUpload status={docStatus} onStatusChange={fetchData} />
              </div>
            )}
            {activeTab === 'users' && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <h2 className="text-base font-semibold text-gray-800 mb-4">User Accounts</h2>
                <UserTable users={users} onUserDeleted={fetchData} />
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/DocumentUpload.tsx frontend/src/components/UserTable.tsx frontend/src/pages/AdminPage.tsx
git commit -m "feat: DocumentUpload, UserTable, AdminPage components"
```

---

## Task 15: App.tsx + main.tsx + Wire Frontend

**Files:**
- Create: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Write `frontend/src/App.tsx`**

```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ChatPage from './pages/ChatPage';
import AdminPage from './pages/AdminPage';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute requiredRole="admin">
                <AdminPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
```

- [ ] **Step 2: Write `frontend/src/main.tsx`**

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 3: Start the frontend dev server and verify**

```bash
cd frontend
npm run dev
```

Visit http://localhost:5173 — expect redirect to `/login`.
Register a new admin account → expect redirect to `/admin`.
Register a new employee account → expect redirect to `/chat`.

- [ ] **Step 4: Run TypeScript check**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors. Fix any type errors before continuing.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/main.tsx
git commit -m "feat: wire React Router routes and app entry point"
```

---

## Task 16: Deployment Configuration

**Files:**
- Create: `render.yaml`
- Create: `vercel.json`
- Create: `frontend/.env.production.example`

- [ ] **Step 1: Write `render.yaml`** (in project root)

```yaml
services:
  - type: web
    name: policy-chatbot-backend
    runtime: python
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: DATABASE_URL
        sync: false
      - key: JWT_SECRET_KEY
        sync: false
      - key: JWT_ALGORITHM
        value: HS256
      - key: JWT_EXPIRE_HOURS
        value: "24"
      - key: FRONTEND_URL
        sync: false
      - key: ENVIRONMENT
        value: production
```

- [ ] **Step 2: Write `vercel.json`** (in project root)

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "rewrites": [{ "source": "/(.*)", "destination": "/" }]
}
```

- [ ] **Step 3: Write `frontend/.env.production.example`**

```
# Set this to your Render backend URL after deploying
VITE_API_URL=https://policy-chatbot-backend.onrender.com
```

- [ ] **Step 4: Create `frontend/vite.config.ts`** with proxy for local dev

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});
```

- [ ] **Step 5: Deploy to Render**

1. Push code to GitHub
2. Go to https://render.com → New → Web Service → connect GitHub repo
3. Set root directory: leave blank (uses `render.yaml`)
4. Set environment variables in Render dashboard:
   - `GEMINI_API_KEY` — your key from aistudio.google.com
   - `DATABASE_URL` — your Supabase transaction URL
   - `JWT_SECRET_KEY` — your secret
   - `FRONTEND_URL` — your Vercel URL (set after deploying frontend)
5. Deploy → copy the Render URL (e.g., `https://policy-chatbot-backend.onrender.com`)

- [ ] **Step 6: Deploy to Vercel**

1. Go to https://vercel.com → New Project → import GitHub repo
2. Set environment variable: `VITE_API_URL` = your Render backend URL from step 5
3. Deploy

- [ ] **Step 7: Update Render FRONTEND_URL**

In Render dashboard → Environment → update `FRONTEND_URL` to your Vercel URL → redeploy.

- [ ] **Step 8: Smoke test production**

1. Visit your Vercel URL
2. Register an admin account
3. Go to Admin → upload a PDF policy document
4. Register an employee account (open incognito window)
5. Ask a question about the policy → verify the answer is grounded in the document

- [ ] **Step 9: Final commit**

```bash
git add render.yaml vercel.json frontend/vite.config.ts frontend/.env.production.example
git commit -m "feat: deployment configuration for Render + Vercel"
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|---|---|
| Google Gemini 1.5 Flash LLM | Task 5 (rag/chain.py) |
| Google text-embedding-004 | Task 5 (rag/embeddings.py) |
| Supabase pgvector | Task 2 + Task 5 (vector_store.py) |
| JWT auth with roles | Task 4 (auth/service.py + dependencies.py) |
| User registration + login | Task 4 (auth/router.py) |
| Admin: upload policy PDF | Task 6 (documents/) |
| Admin: document status + delete | Task 6 |
| Admin: manage users | Task 8 (users/) |
| Employee: ask questions | Task 7 (chat/) |
| Strict RAG — answers only from docs | Task 5 (STRICT_PROMPT in chain.py) |
| React login + register pages | Task 12 |
| React chat interface with sources | Task 13 |
| React admin panel (two tabs) | Task 14 |
| Role-based routing (ProtectedRoute) | Task 11 |
| Axios interceptor with JWT | Task 10 |
| Vercel + Render + Supabase deploy | Task 16 |
| Env files (.env, .env.example) | Tasks 1, 9, 16 |
| Backend tests (auth, docs, chat, users) | Tasks 4, 6, 7, 8 |
