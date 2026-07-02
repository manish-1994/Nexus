# NEXUS V3 - Phase 2: Chat Module

## Overview

This document describes the implementation of Phase 2: Chat Module for NEXUS V3.

## Objectives

- Implement conversation management (create, read, update, delete)
- Enable message sending and receiving with AI providers
- Support streaming responses using Server-Sent Events (SSE)
- Persist conversations and messages in SQLite database
- Build intuitive chat interface with conversation sidebar
- Integrate with existing provider runtime for AI responses

## Completed Tasks

### 1. Backend Chat Service

- `backend/services/chat_service.py` - Core chat business logic:
  - Conversation CRUD operations
  - Message sending with provider integration
  - Streaming response generation
  - Message history management

- `backend/services/conversation_service.py` - Conversation service layer
- `backend/services/message_service.py` - Message service layer

### 2. Backend Repositories

- `backend/repositories/conversation_repository.py` - Conversation data access
- `backend/repositories/message_repository.py` - Message data access

### 3. Backend Schemas

- `backend/schemas/chat.py` - Pydantic schemas:
  - `MessageBase`, `MessageCreate`, `MessageResponse`
  - `ConversationBase`, `ConversationCreate`, `ConversationUpdate`, `ConversationResponse`
  - `ChatRequest`, `ChatResponse`

### 4. Backend API Endpoints

- `backend/api/chat.py` - Chat API endpoints:
  - `GET /conversations` - List all conversations
  - `POST /conversations` - Create new conversation
  - `GET /conversations/{id}` - Get conversation details
  - `PUT /conversations/{id}` - Update conversation title
  - `DELETE /conversations/{id}` - Delete conversation
  - `GET /conversations/{id}/messages` - Get conversation messages
  - `POST /chat` - Send message and get AI response (streaming or non-streaming)

### 5. Frontend Types

- `frontend/src/types/chat.ts` - TypeScript interfaces:
  - `Message` - Message data structure
  - `Conversation` - Conversation data structure
  - `ChatRequest` - Chat request payload

### 6. Frontend API Client

- `frontend/src/api/chat.ts` - Chat API client with methods:
  - `getConversations()` - Fetch all conversations
  - `createConversation()` - Create new conversation
  - `getConversation()` - Fetch single conversation
  - `updateConversation()` - Update conversation title
  - `deleteConversation()` - Delete conversation
  - `getMessages()` - Fetch messages for conversation
  - `sendMessage()` - Send message with streaming support

### 7. Frontend Components

- `frontend/src/pages/ChatPage.tsx` - Main chat page orchestrating all components
- `frontend/src/components/Chat/ConversationSidebar.tsx` - Conversation list with rename/delete
- `frontend/src/components/Chat/MessageList.tsx` - Message display with streaming support
- `frontend/src/components/Chat/MessageInput.tsx` - Message input with provider/model selection

### 8. Routing and Navigation

- `frontend/src/App.tsx` - Added `/chat` route
- `frontend/src/components/Layout/Sidebar.tsx` - Added Chat navigation item

## Directory Structure

```
NEXUS-V3/
├── backend/
│   ├── services/
│   │   ├── chat_service.py # Core chat business logic
│   │   ├── conversation_service.py # Conversation service
│   │   └── message_service.py # Message service
│   ├── repositories/
│   │   ├── conversation_repository.py # Conversation data access
│   │   └── message_repository.py # Message data access
│   ├── schemas/
│   │   └── chat.py # Chat Pydantic schemas
│   └── api/
│       └── chat.py # Chat API endpoints
└── frontend/
    └── src/
        ├── types/
        │   └── chat.ts # TypeScript interfaces
        ├── api/
        │   └── chat.ts # Chat API client
        ├── components/
        │   └── Chat/
        │       ├── ConversationSidebar.tsx # Conversation list
        │       ├── MessageList.tsx # Message display
        │       └── MessageInput.tsx # Message input
        └── pages/
            └── ChatPage.tsx # Main chat page
```

## Technology Stack

### Backend
- FastAPI - Web framework
- SQLAlchemy 2.0 - ORM
- Pydantic - Data validation
- StreamingResponse - SSE streaming

### Frontend
- React 18 - UI library
- TypeScript - Type safety
- Tailwind CSS - Styling
- React Query - Server state management
- Axios - HTTP client

## Key Features

### Conversation Management
- Create new conversations
- List all conversations
- Rename conversations
- Delete conversations
- Persistent storage in SQLite

### Message Handling
- Send messages to AI providers
- Receive streaming responses in real-time
- Display messages with role-based styling
- Auto-scroll during streaming
- Message history persistence

### Streaming Support
- Server-Sent Events (SSE) format
- Real-time token streaming
- Frontend ReadableStream API consumption
- Automatic stream cleanup

### Provider Integration
- Uses existing ProviderRegistry
- Supports all configured AI providers
- Provider and model selection in UI
- Error handling for provider failures

## API Endpoints

### Conversation Endpoints
- `GET /api/v1/conversations` - List all conversations
- `POST /api/v1/conversations` - Create new conversation
- `GET /api/v1/conversations/{id}` - Get conversation details
- `PUT /api/v1/conversations/{id}` - Update conversation title
- `DELETE /api/v1/conversations/{id}` - Delete conversation
- `GET /api/v1/conversations/{id}/messages` - Get conversation messages

### Chat Endpoint
- `POST /api/v1/chat` - Send message and get AI response
  - Request body: `ChatRequest` (conversation_id, content, provider_id, model, stream)
  - Response: StreamingResponse (SSE) or ChatResponse

## Database Schema

### conversations
- id (Primary Key)
- title (String)
- user_id (String, nullable)
- created_at (DateTime)
- updated_at (DateTime)

### messages
- id (Primary Key)
- conversation_id (Foreign Key)
- role (Enum: user, assistant, system)
- content (Text)
- provider (String, nullable)
- model (String, nullable)
- tokens_used (Integer, nullable)
- created_at (DateTime)
- updated_at (DateTime)

## Testing

### Backend Tests
- Conversation CRUD operations
- Message creation and retrieval
- Streaming endpoint functionality
- Provider integration

### Frontend Tests
- Chat page rendering
- Conversation sidebar interactions
- Message list display
- Message input submission
- Streaming content display

## Security Considerations

- Input validation via Pydantic schemas
- SQL injection prevention via SQLAlchemy ORM
- CORS configured for frontend-backend communication
- No authentication implemented yet (future phase)

## Performance Considerations

- Streaming reduces time-to-first-token
- React Query caches conversations and messages
- Auto-scroll optimization for long message lists
- Database queries optimized with indexes

## Future Enhancements

- User authentication and authorization
- Multi-user conversation support
- Conversation search and filtering
- Message editing and deletion
- Conversation branching
- Export conversations (JSON, Markdown)
- Message reactions and feedback
- Typing indicators
- Read receipts
