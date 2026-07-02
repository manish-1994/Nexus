# NEXUS V3 - API Reference

## Base URL

```
/api/v1
```

## Authentication

Currently, no authentication is implemented. All endpoints are publicly accessible.

## Endpoints

### Health

#### `GET /health`

Returns the health status of the API.

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "version": "0.2.0",
  "timestamp": "2026-07-01T14:00:00.000Z"
}
```

---

### Providers

#### `GET /providers`

List all configured AI providers.

**Response**: `200 OK`

```json
[
  {
    "id": 1,
    "name": "OpenRouter",
    "type": "openrouter",
    "base_url": "https://openrouter.ai/api/v1",
    "health_status": "active",
    "last_checked": "2026-07-01T14:00:00.000Z",
    "created_at": "2026-07-01T12:00:00.000Z",
    "updated_at": "2026-07-01T14:00:00.000Z"
  }
]
```

#### `POST /providers`

Create a new AI provider.

**Request Body**:

```json
{
  "name": "OpenRouter",
  "type": "openrouter",
  "base_url": "https://openrouter.ai/api/v1",
  "api_key": "sk-..."
}
```

**Response**: `201 Created`

```json
{
  "id": 1,
  "name": "OpenRouter",
  "type": "openrouter",
  "base_url": "https://openrouter.ai/api/v1",
  "health_status": "inactive",
  "last_checked": null,
  "created_at": "2026-07-01T12:00:00.000Z",
  "updated_at": "2026-07-01T12:00:00.000Z"
}
```

#### `GET /providers/{provider_id}`

Get a specific provider by ID.

**Response**: `200 OK`

```json
{
  "id": 1,
  "name": "OpenRouter",
  "type": "openrouter",
  "base_url": "https://openrouter.ai/api/v1",
  "health_status": "active",
  "last_checked": "2026-07-01T14:00:00.000Z",
  "created_at": "2026-07-01T12:00:00.000Z",
  "updated_at": "2026-07-01T14:00:00.000Z"
}
```

#### `PUT /providers/{provider_id}`

Update an existing provider.

**Request Body**:

```json
{
  "name": "OpenRouter Updated",
  "base_url": "https://openrouter.ai/api/v1",
  "api_key": "new-key"
}
```

**Response**: `200 OK`

```json
{
  "id": 1,
  "name": "OpenRouter Updated",
  "type": "openrouter",
  "base_url": "https://openrouter.ai/api/v1",
  "health_status": "active",
  "last_checked": "2026-07-01T14:00:00.000Z",
  "created_at": "2026-07-01T12:00:00.000Z",
  "updated_at": "2026-07-01T14:30:00.000Z"
}
```

#### `DELETE /providers/{provider_id}`

Delete a provider.

**Response**: `204 No Content`

#### `POST /providers/{provider_id}/test`

Test the connection to a provider.

**Response**: `200 OK`

```json
{
  "status": "active",
  "provider": "OpenRouter",
  "message": "Connection successful"
}
```

#### `POST /providers/{provider_id}/models`

Discover and fetch models from a provider.

**Response**: `200 OK`

```json
[
  {
    "id": 1,
    "name": "gpt-4",
    "provider_id": 1,
    "context_length": 8192,
    "pricing": {
      "input": 0.03,
      "output": 0.06
    },
    "created_at": "2026-07-01T12:00:00.000Z",
    "updated_at": "2026-07-01T12:00:00.000Z"
  }
]
```

#### `GET /providers/{provider_id}/models`

List all models for a specific provider.

**Response**: `200 OK`

```json
[
  {
    "id": 1,
    "name": "gpt-4",
    "provider_id": 1,
    "context_length": 8192,
    "pricing": {
      "input": 0.03,
      "output": 0.06
    },
    "created_at": "2026-07-01T12:00:00.000Z",
    "updated_at": "2026-07-01T12:00:00.000Z"
  }
]
```

#### `DELETE /providers/{provider_id}/models/{model_id}`

Delete a specific model from a provider.

**Response**: `204 No Content`

---

### AI Runtime

#### `POST /api/v1/ai-runtime/chat`

Send a chat message through the AI Runtime Gateway.

**Request Body**:

```json
{
  "messages": [{"role": "user", "content": "Hello"}],
  "provider_id": 1,
  "model": "gpt-3.5-turbo",
  "stream": true
}
```

**Response (Streaming)**: `text/event-stream`

```json
data: {"content": "Hello"}
data: {"content": "! I"}
data: {"content": " am"}
data: {"content": " an"}
data: {"content": " AI"}
data: {"content": " assistant"}
```

**Response (Non-streaming)**: `200 OK`

```json
{
  "content": "Hello! I am an AI assistant",
  "provider": "openai_compatible",
  "model": "gpt-3.5-turbo",
  "tokens_used": 15
}
```

#### `GET /api/v1/ai-runtime/providers/{provider_id}/capabilities`

Get detected capabilities for a provider.

**Response**:

```json
{
  "capabilities": {
    "streaming": true,
    "vision": false,
    "embeddings": false,
    "tools": true,
    "images": false,
    "audio": false,
    "reasoning": false
  }
}
```

#### `GET /api/v1/ai-runtime/usage`

Get usage statistics.

**Response**:

```json
{
  "total_requests": 150,
  "total_tokens": 45000,
  "total_cost": 2.35,
  "by_provider": {
    "openai_compatible": {
      "requests": 100,
      "tokens": 30000,
      "cost": 1.50
    }
  }
}
```

---

### Chat

#### `POST /chat`

Send a message and get AI response with optional streaming.

**Request Body**:

```json
{
  "conversation_id": 1,
  "content": "Hello, how are you?",
  "provider_id": 1,
  "model": "gpt-3.5-turbo",
  "stream": true
}
```

**Response (Streaming)**: `text/event-stream`

```
data: {"content": "Hello"}

data: {"content": "! I"}

data: {"content": " am"}

data: {"content": " doing"}

data: {"content": " well"}
```

**Response (Non-streaming)**: `200 OK`

```json
{
  "conversation_id": 1,
  "message": {
    "id": 1,
    "role": "assistant",
    "content": "Hello! I am doing well, thank you for asking.",
    "provider": "openrouter",
    "model": "gpt-3.5-turbo",
    "tokens_used": 15,
    "created_at": "2026-07-01T16:00:00"
  }
}
```

---

## Data Models

### Provider

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique identifier |
| name | string | Provider name |
| type | enum | Provider type (openrouter, groq, ollama, gemini, lmstudio) |
| base_url | string | Base URL for API calls |
| api_key | string | Encrypted API key |
| health_status | enum | Health status (active, inactive, error, checking) |
| last_checked | datetime | Last health check timestamp |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

### Model

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique identifier |
| name | string | Model name |
| provider_id | integer | Foreign key to Provider |
| context_length | integer | Maximum context length |
| pricing | object | Input/output pricing information |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

---

## Error Responses

All endpoints may return the following error responses:

### `400 Bad Request`

```json
{
  "detail": "Invalid request parameters"
}
```

### `404 Not Found`

```json
{
  "detail": "Provider not found"
}
```

### `422 Unprocessable Entity`

```json
{
  "detail": [
    {
      "loc": ["body", "api_key"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### `500 Internal Server Error`

```json
{
  "detail": "Internal server error"
}
```

---

## Provider Types

| Type | Description | Base URL |
|------|-------------|----------|
| openrouter | OpenRouter API | https://openrouter.ai/api/v1 |
| groq | Groq API | https://api.groq.com/openai/v1 |
| ollama | Ollama (local) | http://localhost:11434 |
| gemini | Google Gemini | https://generativelanguage.googleapis.com/v1beta |
| lmstudio | LM Studio (local) | http://localhost:1234 |

---

## Rate Limiting

Currently, no rate limiting is implemented. This will be added in future phases.

## Versioning

API versioning is implemented via URL prefix (`/api/v1`). Future versions will use `/api/v2`, etc.
