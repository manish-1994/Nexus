# NEXUS V3 - Chat Workspace UX & Real-Time Streaming Enhancement

## Objective
Upgrade the Chat Workspace so it behaves like ChatGPT/Claude/Cursor with production-quality UX, real-time updates, and polished animations.

## Current State Analysis

### Existing Implementation
- **MessageList**: Basic streaming support, loading skeletons, auto-scroll with user scroll detection
- **MessageInput**: Enter to send, Shift+Enter for new line, auto-grow textarea, stop streaming button
- **chatStore**: Optimistic UI (user message appended immediately), thinking placeholder with animated dots, streaming content accumulation, provider error parsing with retry
- **ChatPage**: React Query for conversations/messages, URL-based conversation persistence, sidebar with search/sort

### Gaps Identified
1. No timeout states for long-running requests
2. No explicit message status indicators (Sending/Sent/Generating/Completed/Failed)
3. No blinking cursor during streaming
4. No smooth animations for new messages
5. No accessibility attributes (ARIA labels, keyboard navigation)
6. No reduced motion support
7. Input not auto-focused on new conversation/switch/response completion
8. No toast notifications for conversation operations (create/delete/rename)

## Implementation Plan

### Phase 1: Message Status & Timeout States
**Goal**: Add visual feedback for message lifecycle and long-running requests

#### Tasks
1. **Extend Message type** with `status` field (`sending` | `sent` | `generating` | `completed` | `failed`)
2. **Update chatStore.sendMessage** to set status transitions:
   - User message: `sending` → `sent`
   - Assistant placeholder: `generating` → `completed` or `failed`
3. **Add timeout tracking** in chatStore:
   - Start timer when streaming begins
   - At 5s: Update assistant message with "Still thinking..."
   - At 15s: Update with "This model is taking longer than usual..."
4. **Update MessageBubble** to display status badge:
   - Show "Sending..." for user messages with `sending` status
   - Show "Generating..." for assistant with `generating` status
   - Show "Failed" for failed messages
   - Hide status for `completed` messages

### Phase 2: Streaming UX Improvements
**Goal**: Make streaming feel responsive and polished

#### Tasks
1. **Add blinking cursor** during streaming:
   - Append `<span className="animate-pulse">|</span>` to streaming content in MessageList
   - Remove cursor when streaming completes
2. **Improve auto-scroll behavior**:
   - Add `scrollBehavior: 'smooth'` for new messages
   - Add `scrollBehavior: 'auto'` for streaming tokens (faster)
   - Keep user pinned if within 100px of bottom during streaming
3. **Add streaming indicator** in MessageInput:
   - Show "Generating..." text with animated dots when `isStreaming`
   - Replace "Send" button text with "Generating..." during streaming

### Phase 3: Toast Notifications for Conversations
**Goal**: Provide feedback for conversation operations

#### Tasks
1. **Add toasts in ChatPage**:
   - `toast.success('Conversation created')` on new conversation
   - `toast.success('Conversation deleted')` on delete (already exists)
   - `toast.success('Conversation renamed')` on rename (already exists)
   - `toast.error('Failed to create conversation')` on error
2. **Add toasts for provider/model errors**:
   - Already partially implemented in chatStore
   - Ensure all error paths show toasts

### Phase 4: Accessibility & Keyboard Navigation
**Goal**: Make chat accessible to all users

#### Tasks
1. **Add ARIA labels**:
   - `aria-label="Send message"` on send button
   - `aria-label="Stop generating"` on stop button
   - `aria-label="New conversation"` on new chat button
   - `aria-label="Conversation list"` on sidebar
   - `aria-label="Message list"` on message container
   - `aria-live="polite"` on message list for screen readers
2. **Keyboard navigation**:
   - `Ctrl+N` or `Cmd+N` for new conversation
   - `Ctrl+/` or `Cmd+/` to focus input
   - `Escape` to cancel streaming
   - `ArrowUp`/`ArrowDown` to navigate conversations in sidebar
3. **Focus management**:
   - Auto-focus input after new conversation
   - Auto-focus input after conversation switch
   - Auto-focus input after response completes
   - Return focus to send button after error

### Phase 5: Smooth Animations
**Goal**: Add polished transitions for all state changes

#### Tasks
1. **Add CSS transitions** in `index.css`:
   - `.message-enter`: Fade in + slide up for new messages
   - `.message-exit`: Fade out for removed messages
   - `.sidebar-item-enter`: Slide in from left for sidebar items
   - `.thinking-enter`: Pulse animation for thinking indicator
2. **Animate new messages**:
   - Apply `animate-fadeInUp` class to new MessageBubble
   - Duration: 200ms ease-out
3. **Animate assistant appearance**:
   - Add subtle scale animation when thinking placeholder appears
4. **Animate conversation selection**:
   - Highlight transition: 150ms ease-in-out

### Phase 6: Performance Optimizations
**Goal**: Ensure smooth performance with large conversation histories

#### Tasks
1. **Memoize message list**:
   - Already using `memo` on MessageBubble
   - Ensure `displayMessages` memo dependencies are correct
2. **Virtualization preparation**:
   - Add comment markers for future virtualization (>500 messages)
   - Ensure current implementation can be wrapped with `react-window` later
3. **Reduce re-renders**:
   - Use `useCallback` for event handlers in ChatPage
   - Split MessageList into smaller memoized components if needed

### Phase 7: Reduced Motion Support
**Goal**: Respect user accessibility preferences

#### Tasks
1. **Add CSS media query**:
   ```css
   @media (prefers-reduced-motion: reduce) {
     * {
       animation-duration: 0.01ms !important;
       transition-duration: 0.01ms !important;
     }
   }
   ```
2. **Check preference in components**:
   - Use `window.matchMedia('(prefers-reduced-motion: reduce)').matches`
   - Disable non-essential animations when true

## Acceptance Criteria

### 1. Optimistic UI
- [ ] User message appears instantly in UI before API call
- [ ] Input clears immediately after send
- [ ] Send button disables during streaming

### 2. Assistant Placeholder
- [ ] Temporary assistant message with animated dots appears
- [ ] Shows provider icon/name and model name
- [ ] Pulse animation on placeholder

### 3. Live Streaming
- [ ] Tokens append incrementally (not replace)
- [ ] Blinking cursor appears during stream
- [ ] Cursor disappears when stream completes

### 4. Timeout States
- [ ] "Still thinking..." appears after 5 seconds
- [ ] "This model is taking longer than usual..." appears after 15 seconds

### 5. Error Handling
- [ ] Provider-specific error toasts (401, 403, 429, 500)
- [ ] Retry button appears on failed messages
- [ ] Cancel button stops streaming

### 6. Conversation Sidebar (Real-Time)
- [ ] New conversations appear instantly
- [ ] Deleted conversations disappear instantly
- [ ] Renamed conversations update instantly
- [ ] No page refresh required

### 7. Conversation History
- [ ] Entire message history loads on conversation select
- [ ] Scroll position restores to bottom

### 8. Auto Scroll
- [ ] Stays pinned to latest token during streaming
- [ ] Pauses when user scrolls up
- [ ] Resumes when user scrolls to bottom

### 9. Message Status
- [ ] Displays "Sending..." for pending user messages
- [ ] Displays "Sent" for confirmed user messages
- [ ] Displays "Generating..." for streaming assistant
- [ ] Displays "Completed" for finished assistant
- [ ] Displays "Failed" for errored messages
- [ ] Retry button on failed messages

### 10. Typing Indicator Animation
- [ ] Pure CSS animation (no GIFs)
- [ ] Three bouncing dots
- [ ] Smooth infinite loop

### 11. Smooth Animations
- [ ] New messages animate in (fade + slide)
- [ ] Assistant placeholder pulses
- [ ] Thinking bubble animates
- [ ] Streaming bubble animates
- [ ] Conversation selection animates
- [ ] Conversation creation animates
- [ ] Conversation deletion animates

### 12. Input Experience
- [ ] Input always visible at bottom
- [ ] Auto-focus after new chat
- [ ] Auto-focus after conversation switch
- [ ] Auto-focus after response completion
- [ ] Enter sends message
- [ ] Shift+Enter creates new line

### 13. Toast Notifications
- [ ] "Conversation created" on new chat
- [ ] "Conversation deleted" on delete
- [ ] "Conversation renamed" on rename
- [ ] "Provider synced" on model discovery
- [ ] "Model synced" on model refresh
- [ ] API errors show provider-specific message
- [ ] "Credits exhausted" for quota errors
- [ ] "Rate limit reached" for 429 errors
- [ ] Network status changes shown

### 14. Loading Skeletons
- [ ] Skeleton messages while loading history
- [ ] Skeleton conversations while loading sidebar
- [ ] Shimmer animation on skeletons

### 15. Performance
- [ ] No unnecessary re-renders
- [ ] Message list memoized
- [ ] Handles 500+ messages smoothly
- [ ] Virtualization ready (commented for future)

### 16. Accessibility
- [ ] Keyboard navigation works
- [ ] ARIA labels present
- [ ] Focus management correct
- [ ] Screen reader friendly
- [ ] Respects reduced motion preference

### 17. Verification
- [ ] Build passes
- [ ] Lint passes
- [ ] Type-check passes
- [ ] All 16 criteria above verified

## Files to Modify

### Frontend
1. `frontend/src/types/chat.ts` - Add `status` field to Message
2. `frontend/src/stores/chatStore.ts` - Add timeout tracking, status transitions
3. `frontend/src/components/Chat/MessageList.tsx` - Add status badge, blinking cursor, animations
4. `frontend/src/components/Chat/MessageInput.tsx` - Add streaming indicator, auto-focus
5. `frontend/src/pages/ChatPage.tsx` - Add toasts, keyboard shortcuts, focus management
6. `frontend/src/components/Chat/ConversationSidebar.tsx` - Add ARIA labels, keyboard nav
7. `frontend/src/assets/index.css` - Add animations, reduced motion support

## Implementation Order

1. **Phase 1**: Message Status & Timeout States (core UX)
2. **Phase 2**: Streaming UX Improvements (polish)
3. **Phase 3**: Toast Notifications (feedback)
4. **Phase 4**: Accessibility (compliance)
5. **Phase 5**: Smooth Animations (polish)
6. **Phase 6**: Performance (optimization)
7. **Phase 7**: Reduced Motion (accessibility)

Each phase will be implemented, tested, and verified before moving to the next.
