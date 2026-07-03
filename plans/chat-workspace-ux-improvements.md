# NEXUS V3 - Chat Workspace UX & Performance Improvements

## Implementation Plan

---

## Current State Analysis

### Existing Architecture
- **Frontend**: React 18 + TypeScript + Vite + Zustand + React Query
- **Backend**: FastAPI + SQLAlchemy 2.0 + PostgreSQL
- **State Management**: Zustand for chat state, React Query for server state
- **Streaming**: Native Fetch API with SSE parser
- **Error Handling**: ProviderErrorParser with auto-switch logic

### What's Already Implemented
✅ Thinking placeholder with animated dots
✅ Optimistic user message insertion
✅ Error state with Retry/Cancel buttons
✅ Auto-switch provider on credit/quota errors
✅ Global toast notification system
✅ Basic conversation sidebar (title only)
✅ Message input with Enter to send, Shift+Enter for new line

### What's Missing
❌ Enhanced conversation sidebar (preview, provider, model, timestamp)
❌ Search and sort conversations
❌ Skeleton loaders for loading states
❌ Auto-scroll to latest message
❌ Persistent conversation state (restore after refresh)
❌ Keyboard shortcuts (Ctrl+K, Esc)
❌ Conversation state persistence
❌ React Query caching optimization
❌ Performance optimizations

---

## Implementation Plan

## Phase 1: Enhanced Conversation Sidebar

### 1.1 Backend - Add Conversation Metadata

**Files to Modify:**
- `backend/models/conversation.py` - Add `last_message_preview`, `provider_name`, `model_name` fields
- `backend/schemas/chat.py` - Add fields to `ConversationResponse`
- `backend/services/conversation_service.py` - Add method to get conversations with metadata
- `backend/api/conversations.py` - Update list endpoint to include metadata

**Changes:**
```python
# Add to Conversation model
last_message_preview = Column(String(200), nullable=True)
provider_name = Column(String(50), nullable=True)
model_name = Column(String(100), nullable=True)

# Add to ConversationService
def get_all_with_metadata(self, user_id: Optional[str] = None) -> List[Dict]:
    """Get conversations with last message preview and provider/model info."""
    pass
```

### 1.2 Frontend - Enhanced ConversationSidebar

**Files to Modify:**
- `frontend/src/components/Chat/ConversationSidebar.tsx` - Complete rewrite
- `frontend/src/types/chat.ts` - Add `ConversationSidebarItem` interface

**New Features:**
- Conversation title with truncation
- Last message preview (first 50 chars)
- Provider icon and model name
- Last updated time (relative: "2m ago", "1h ago", etc.)
- Search input with debounce
- Sort dropdown (Newest, Oldest)
- Loading skeleton state
- Empty state with illustration

**UI Layout:**
```
┌─────────────────────────────┐
│ 🔍 Search conversations...  │
│ Sort: [Newest ▼]           │
├─────────────────────────────┤
│ + New Chat                  │
├─────────────────────────────┤
│ 💬 Project Alpha           │
│    "How do I implement..."  │
│    GPT-4 • 2m ago          │
├─────────────────────────────┤
│ 💬 API Design              │
│    "Let's design the API..."│
│    Claude • 1h ago         │
└─────────────────────────────┘
```

---

## Phase 2: Performance & Caching

### 2.1 React Query Optimization

**Files to Modify:**
- `frontend/src/pages/ChatPage.tsx` - Add React Query hooks
- `frontend/src/stores/chatStore.ts` - Remove manual fetching, use React Query

**Strategy:**
```typescript
// Use React Query for all server state
const { data: conversations = [], isLoading: conversationsLoading } = useQuery({
  queryKey: ['conversations'],
  queryFn: chatApi.getConversations,
  staleTime: 1000 * 60 * 5, // 5 minutes
});

const { data: messages = [] } = useQuery({
  queryKey: ['messages', conversationId],
  queryFn: () => chatApi.getMessages(conversationId),
  enabled: !!conversationId,
  staleTime: 1000 * 60 * 2, // 2 minutes
});
```

**Benefits:**
- Automatic caching
- Background refetching
- Optimistic updates
- Deduplication
- Cache invalidation on mutations

### 2.2 Optimistic Updates

**Files to Modify:**
- `frontend/src/stores/chatStore.ts` - Add optimistic update helpers
- `frontend/src/pages/ChatPage.tsx` - Use `useMutation` with optimistic updates

**Strategy:**
```typescript
const sendMessageMutation = useMutation({
  mutationFn: (data) => chatApi.sendMessage(data),
  onMutate: async (newMessage) => {
    // Cancel any outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['messages'] });
    
    // Snapshot the previous value
    const previousMessages = queryClient.getQueryData(['messages', conversationId]);
    
    // Optimistically update to the new value
    queryClient.setQueryData(['messages', conversationId], (old) => [
      ...old,
      userMessage,
      thinkingPlaceholder
    ]);
    
    return { previousMessages };
  },
  onError: (err, newMessage, context) => {
    // Rollback on error
    queryClient.setQueryData(['messages', conversationId], context.previousMessages);
  },
  onSettled: () => {
    // Always refetch after error or success
    queryClient.invalidateQueries({ queryKey: ['messages'] });
  },
});
```

---

## Phase 3: Auto-Scroll & UX Improvements

### 3.1 Auto-Scroll Implementation

**Files to Modify:**
- `frontend/src/components/Chat/MessageList.tsx` - Add auto-scroll logic

**Strategy:**
```typescript
const messagesEndRef = useRef<HTMLDivElement>(null);
const prevMessagesLengthRef = useRef(messages.length);

useEffect(() => {
  const shouldScroll = 
    messages.length > prevMessagesLengthRef.current ||
    isStreaming;
  
  if (shouldScroll && messagesEndRef.current) {
    messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
  }
  
  prevMessagesLengthRef.current = messages.length;
}, [messages, isStreaming]);
```

**Scroll Triggers:**
- Opening conversation
- Receiving stream chunk
- Sending new message
- User manually scrolls to bottom (pause auto-scroll)

### 3.2 Skeleton Loaders

**Files to Create:**
- `frontend/src/components/Chat/SkeletonLoader.tsx`

**Components:**
- `ConversationSkeleton` - 5 skeleton items
- `MessageSkeleton` - 3-5 skeleton bubbles
- `MessageBubbleSkeleton` - Individual bubble with pulse animation

**Usage:**
```tsx
{isLoading ? (
  <MessageSkeleton count={5} />
) : (
  <MessageList messages={messages} />
)}
```

---

## Phase 4: Conversation State Persistence

### 4.1 Persist Selected Conversation

**Files to Modify:**
- `frontend/src/stores/chatStore.ts` - Add `currentConversationId` to state
- `frontend/src/pages/ChatPage.tsx` - Restore on mount

**Strategy:**
```typescript
// In chatStore
interface ChatState {
  currentConversationId: number | null;
  // ... other fields
}

// On conversation select
setCurrentConversationId(conversation.id);
localStorage.setItem('currentConversationId', String(conversation.id));

// On app load
const savedId = localStorage.getItem('currentConversationId');
if (savedId) {
  const conversation = await chatApi.getConversation(Number(savedId));
  setCurrentConversation(conversation);
  fetchMessages(conversation.id);
}
```

### 4.2 Persist Provider/Model Selection

**Files to Modify:**
- `frontend/src/stores/providerStore.ts` - Already has selectedProviderId
- `frontend/src/stores/modelStore.ts` - Already has selectedModel
- Add localStorage persistence to both stores

---

## Phase 5: Keyboard Shortcuts

### 5.1 Global Keyboard Handler

**Files to Modify:**
- `frontend/src/pages/ChatPage.tsx` - Add keyboard shortcut useEffect

**Shortcuts:**
- `Ctrl+K` or `Cmd+K` - Focus search conversations
- `Esc` - Cancel streaming / Clear search
- `Ctrl+N` or `Cmd+N` - New conversation
- `Ctrl+/` - Show keyboard shortcuts help

**Implementation:**
```typescript
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    // Ctrl+K: Focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      searchInputRef.current?.focus();
    }
    
    // Esc: Cancel streaming or clear search
    if (e.key === 'Escape') {
      if (isStreaming) {
        cancelStreaming();
      } else {
        searchInputRef.current?.blur();
        setSearchQuery('');
      }
    }
  };
  
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [isStreaming, cancelStreaming]);
```

---

## Phase 6: Error Recovery & UX Polish

### 6.1 Improved Error States

**Files to Modify:**
- `frontend/src/components/Chat/MessageList.tsx` - Add error boundary
- `frontend/src/pages/ChatPage.tsx` - Add error recovery UI

**Features:**
- Retry button for failed messages
- Clear error state button
- "Start new conversation" when conversation is empty
- Network error detection with retry

### 6.2 Loading States

**Files to Modify:**
- `frontend/src/components/Chat/ConversationSidebar.tsx` - Add skeleton loader
- `frontend/src/components/Chat/MessageList.tsx` - Add skeleton loader
- `frontend/src/components/Chat/MessageInput.tsx` - Disable during streaming

**States:**
- `isLoading` - Initial load (skeleton)
- `isStreaming` - Streaming in progress (thinking animation)
- `isError` - Error state (retry button)

---

## Phase 7: Backend Optimizations

### 7.1 Conversation History Performance

**Files to Modify:**
- `backend/services/conversation_service.py` - Add indexes
- `backend/repositories/conversation_repository.py` - Optimize queries

**Optimizations:**
```python
# Add database indexes
class Conversation(BaseModel):
    __table_args__ = (
        Index('idx_conversation_user_id', 'user_id'),
        Index('idx_conversation_updated_at', 'updated_at'),
        Index('idx_conversation_title', 'title'),
    )

# Optimize query with eager loading
def get_all_with_metadata(self, user_id: Optional[str] = None):
    return (
        self.db.query(Conversation)
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
```

### 7.2 Message Ordering

**Files to Modify:**
- `backend/repositories/message_repository.py` - Ensure proper ordering

**Changes:**
```python
def find_by_conversation_id(self, conversation_id: int, skip: int = 0, limit: int = 100):
    return (
        self.db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())  # Oldest first
        .offset(skip)
        .limit(limit)
        .all()
    )
```

---

## Implementation Order

### Step 1: Backend Foundation (Day 1)
1. Add conversation metadata fields
2. Update schemas
3. Add optimized queries
4. Add database indexes

### Step 2: Frontend Core (Day 2-3)
1. Implement React Query hooks
2. Migrate from Zustand to React Query for server state
3. Add optimistic updates
4. Implement auto-scroll

### Step 3: UI Enhancements (Day 4-5)
1. Enhanced conversation sidebar
2. Skeleton loaders
3. Search and sort
4. Keyboard shortcuts

### Step 4: State Persistence (Day 6)
1. Persist selected conversation
2. Persist provider/model selection
3. Restore state on app load

### Step 5: Polish & Testing (Day 7)
1. Error recovery improvements
2. Loading state refinements
3. End-to-end testing
4. Documentation updates

---

## Files to Modify

### Backend
1. `backend/models/conversation.py` - Add metadata fields
2. `backend/schemas/chat.py` - Add fields to schemas
3. `backend/services/conversation_service.py` - Add optimized queries
4. `backend/repositories/conversation_repository.py` - Add indexes
5. `backend/api/conversations.py` - Update endpoints

### Frontend
1. `frontend/src/types/chat.ts` - Add new interfaces
2. `frontend/src/stores/chatStore.ts` - Migrate to React Query
3. `frontend/src/stores/providerStore.ts` - Add localStorage persistence
4. `frontend/src/stores/modelStore.ts` - Add localStorage persistence
5. `frontend/src/pages/ChatPage.tsx` - Add React Query hooks, keyboard shortcuts
6. `frontend/src/components/Chat/ConversationSidebar.tsx` - Complete rewrite
7. `frontend/src/components/Chat/MessageList.tsx` - Add auto-scroll, skeleton
8. `frontend/src/components/Chat/MessageInput.tsx` - Minor improvements
9. `frontend/src/components/Chat/SkeletonLoader.tsx` - New component

### Documentation
1. `docs/reports/IMPLEMENTATION_REPORT.md` - Update with new features
2. `docs/testing/TEST_RESULTS.md` - Add verification results
3. `docs/reports/STATUS.md` - Update project status
4. `docs/reports/CHANGELOG.md` - Add changelog entries

---

## Acceptance Criteria

### Performance
- ✅ Conversation list loads in < 500ms
- ✅ Messages load in < 300ms
- ✅ Streaming starts in < 1s
- ✅ No unnecessary API calls (caching works)
- ✅ Smooth scrolling (60fps)

### UX
- ✅ User message appears instantly
- ✅ Thinking placeholder appears immediately
- ✅ Auto-scroll to latest message
- ✅ Search conversations with debounce
- ✅ Sort conversations (newest/oldest)
- ✅ Keyboard shortcuts work
- ✅ State persists after refresh
- ✅ Skeleton loaders during loading
- ✅ Error recovery with retry

### Functionality
- ✅ Open any previous conversation
- ✅ Continue chatting from any conversation
- ✅ No duplicate messages
- ✅ No blank loading screens
- ✅ Works with all providers
- ✅ Build passes
- ✅ Lint passes
- ✅ Type-check passes

---

## Risks & Mitigations

### Risk 1: Breaking Existing Functionality
**Mitigation:** Implement feature flags, test each feature independently, maintain backward compatibility

### Risk 2: Performance Regression
**Mitigation:** Profile before/after, use React Query devtools, monitor API calls

### Risk 3: State Management Complexity
**Mitigation:** Clear separation of concerns (server state vs client state), comprehensive testing

### Risk 4: Migration from Zustand to React Query
**Mitigation:** Gradual migration, keep Zustand for UI state only, use React Query for server state

---

## Next Steps

1. Review this plan with the team
2. Get approval to proceed
3. Start with Phase 1: Backend Foundation
4. Implement incrementally with testing at each step
5. Verify acceptance criteria before moving to next phase
