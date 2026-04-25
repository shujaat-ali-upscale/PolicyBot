# Employee Policy Chatbot — Design Spec
Date: 2026-04-24

## Overview

A RAG-powered chatbot that lets employees ask questions about company policy documents. Admins upload a combined policy PDF; employees ask questions and receive answers grounded strictly in that document. Built for learning best practices in AI/RAG development.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | Python + FastAPI |
| LLM | Google Gemini 1.5 Flash (free tier, aistudio.google.com) |
| Embeddings | Google text-embedding-004 (free tier) |
| Vector Store | Supabase pgvector (free tier) |
| User Database | Supabase PostgreSQL (free tier) |
| ORM | SQLAlchemy (async) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Deployment | Vercel (frontend) + Render (backend) + Supabase (database) |

---

## Roles

| Role | Permissions |
|---|---|
| `admin` | Upload/replace policy document, view/delete users, access chat |
| `employee` | Access chat only |

---

## Backend Structure

```
backend/
  app/
    auth/
      router.py        # POST /auth/register, /auth/login, /auth/me
      service.py       # JWT creation, bcrypt password hashing
      schemas.py       # LoginRequest, RegisterRequest, TokenResponse, UserResponse
      dependencies.py  # get_current_user(), require_admin() FastAPI dependencies
    chat/
      router.py        # POST /chat
      service.py       # Embed question → similarity search → Gemini → return answer
      schemas.py       # ChatRequest, ChatResponse
    documents/
      router.py        # POST /documents/upload, DELETE /documents, GET /documents/status
      service.py       # Parse PDF → chunk → embed → upsert to pgvector
      schemas.py       # DocumentStatus, UploadResponse
    users/
      router.py        # GET /users, DELETE /users/{id}  (admin only)
      service.py       # List users, delete user
      schemas.py       # UserListResponse
    rag/
      embeddings.py    # Google text-embedding-004 via LangChain
      vector_store.py  # PGVector connection, upsert, similarity search
      chain.py         # Strict RAG prompt template + Gemini 1.5 Flash chain
    main.py            # FastAPI app factory, CORS, router registration
    config.py          # All env vars via Pydantic BaseSettings
    database.py        # SQLAlchemy async engine, session factory, Base
    models.py          # User SQLAlchemy model
  requirements.txt
  .env
  .env.example
```

---

## Frontend Structure

```
frontend/
  src/
    api/
      client.ts        # Axios instance, JWT injector interceptor, 401 handler
      auth.ts          # login(), register(), getMe()
      chat.ts          # sendMessage()
      documents.ts     # upload(), deleteDocument(), getStatus()
      users.ts         # listUsers(), deleteUser()
    pages/
      LoginPage.tsx    # Email + password login form
      RegisterPage.tsx # Name, email, password, role selector (employee default)
      AdminPage.tsx    # Two tabs: "Upload Policy" + "Manage Users"
      ChatPage.tsx     # Full chat interface
    components/
      Layout.tsx           # Top nav, role-aware links, logout
      ProtectedRoute.tsx   # Redirects unauthenticated or wrong-role users
      ChatMessage.tsx      # Message bubble + expandable sources accordion
      DocumentUpload.tsx   # Drag-and-drop PDF uploader with chunk count feedback
      UserTable.tsx        # Admin table: list users, delete button per row
    context/
      AuthContext.tsx   # JWT in localStorage, decoded user state, login/logout
    App.tsx             # React Router v6 route definitions
    main.tsx
```

---

## Routes

| Path | Page | Access |
|---|---|---|
| `/login` | LoginPage | Public |
| `/register` | RegisterPage | Public |
| `/chat` | ChatPage | Employee + Admin |
| `/admin` | AdminPage | Admin only |
| `*` | Redirect to /login | — |

---

## Data Flow

### Registration
1. User fills register form (name, email, password, role)
2. `POST /auth/register` → validate → hash password (bcrypt) → insert into Supabase users table
3. Return JWT → store in localStorage → redirect to `/chat` or `/admin`

### Login
1. `POST /auth/login` → verify email + password → return JWT + user info
2. Frontend decodes JWT for role → redirect accordingly

### Admin Uploads Policy
1. Admin drags PDF onto `DocumentUpload` component
2. `POST /documents/upload` (multipart/form-data, admin JWT required)
3. Backend: parse PDF → split into chunks (1000 chars, 150 char overlap)
4. Embed each chunk via `text-embedding-004`
5. Delete all existing vectors from pgvector collection
6. Insert new vectors with metadata `{ source: filename, chunk_index: n }`
7. Return `{ success: true, chunks_created: 42 }`

### Employee Asks Question
1. Employee types question → `POST /chat { question }`
2. Embed question via `text-embedding-004`
3. Similarity search pgvector → top 4 most relevant chunks
4. Build strict prompt:
   ```
   You are a helpful HR assistant. Answer ONLY using the context below.
   If the answer is not in the context, say "I don't have information about that in the policy document."
   Do not use any outside knowledge.

   Context:
   {context}

   Question: {question}
   ```
5. Send to Gemini 1.5 Flash → stream response
6. Return `{ answer: string, sources: [{ text, chunk_index }] }`
7. Frontend renders markdown answer + expandable sources accordion

---

## Auth & Security

- Passwords hashed with bcrypt via passlib
- JWT tokens signed with HS256, 24hr expiry
- All endpoints except `/auth/login` and `/auth/register` require valid JWT
- `/documents/*` and `/users/*` require `admin` role
- `/chat` requires any authenticated user
- CORS restricted to `FRONTEND_URL` env var
- Input validated via Pydantic on all endpoints

---

## Environment Variables

### backend/.env
```
GEMINI_API_KEY=          # from aistudio.google.com → Get API Key
DATABASE_URL=            # Supabase → Settings → Database → Connection string (Transaction mode)
JWT_SECRET_KEY=          # any random 32+ char string (generate with: openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
FRONTEND_URL=http://localhost:5173
ENVIRONMENT=development
```

### frontend/.env
```
VITE_API_URL=http://localhost:8000
```

### frontend/.env.production
```
VITE_API_URL=https://your-render-app.onrender.com
```

---

## Deployment

| Service | Purpose | Free Tier |
|---|---|---|
| Supabase | PostgreSQL + pgvector | 500MB, always free |
| Render | FastAPI backend | 750hrs/month, sleeps after 15min inactivity |
| Vercel | React frontend | Unlimited, always free |

### Setup Order
1. Create Supabase project → enable pgvector extension → copy DATABASE_URL
2. Get Gemini API key from aistudio.google.com
3. Deploy backend to Render (set env vars in dashboard)
4. Deploy frontend to Vercel (set VITE_API_URL to Render URL)

---

## What This Teaches

- RAG pipeline: chunking → embedding → vector similarity search → LLM grounding
- JWT authentication with role-based access control
- FastAPI modular structure (routers, services, schemas, dependencies)
- Supabase pgvector as a production-grade free vector store
- React context for auth state management
- Axios interceptors for automatic token injection
- Deployment pipeline: Vercel + Render + Supabase
