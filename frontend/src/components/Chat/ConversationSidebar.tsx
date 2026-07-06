import { useState, useMemo } from 'react';
import type { Conversation } from '../../types/chat';
import { Plus, Search, Calendar, Trash2, Edit2, Inbox } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ConversationSidebarProps {
  conversations: Conversation[]
  selectedId: number | null
  onSelect: (id: number) => void
  onNewConversation: () => void
  onDelete: (id: number) => void
  onRename: (id: number, title: string) => void
  isLoading: boolean
  searchQuery?: string
  onSearchChange?: (query: string) => void
  sortBy?: 'newest' | 'oldest'
  onSortChange?: (sort: 'newest' | 'oldest') => void
}

function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'JUST NOW';
  if (diffMins < 60) return `${diffMins}M AGO`;
  if (diffHours < 24) return `${diffHours}H AGO`;
  if (diffDays < 7) return `${diffDays}D AGO`;
  return date.toLocaleDateString().toUpperCase();
}

function ConversationSidebar({
  conversations,
  selectedId,
  onSelect,
  onNewConversation,
  onDelete,
  onRename,
  isLoading,
  searchQuery = '',
  onSearchChange,
  sortBy = 'newest',
  onSortChange,
}: ConversationSidebarProps) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState('');

  const handleStartRename = (conversation: Conversation) => {
    setEditingId(conversation.id);
    setEditingTitle(conversation.title);
  };

  const handleSaveRename = (id: number) => {
    if (editingTitle.trim()) {
      onRename(id, editingTitle.trim());
    }
    setEditingId(null);
    setEditingTitle('');
  };

  const handleKeyDown = (e: React.KeyboardEvent, id: number) => {
    if (e.key === 'Enter') {
      handleSaveRename(id);
    } else if (e.key === 'Escape') {
      setEditingId(null);
      setEditingTitle('');
    }
  };

  const filteredAndSortedConversations = useMemo(() => {
    let filtered = conversations;

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = conversations.filter(
        (conv) =>
          conv.title.toLowerCase().includes(query) ||
          conv.last_message_preview?.toLowerCase().includes(query) ||
          conv.provider_name?.toLowerCase().includes(query) ||
          conv.model_name?.toLowerCase().includes(query)
      );
    }

    const sorted = [...filtered].sort((a, b) => {
      const dateA = new Date(a.updated_at).getTime();
      const dateB = new Date(b.updated_at).getTime();
      return sortBy === 'newest' ? dateB - dateA : dateA - dateB;
    });

    return sorted;
  }, [conversations, searchQuery, sortBy]);

  return (
    <div className="w-80 bg-surface/30 backdrop-blur-md border-r border-white/5 flex flex-col h-full">
      {/* Header with New Chat button */}
      <div className="p-4 border-b border-white/5">
        <button
          onClick={onNewConversation}
          disabled={isLoading}
          className="w-full bg-accent hover:bg-accent-light disabled:bg-white/5 disabled:text-text-muted/40 disabled:cursor-not-allowed text-white rounded-button py-3 text-xs font-bold tracking-widest uppercase transition-all shadow-glow-sm flex items-center justify-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>{isLoading ? 'Creating...' : 'New Sequence'}</span>
        </button>
      </div>

      {/* Search and Sort */}
      <div className="p-4 border-b border-white/5 space-y-3">
        {onSearchChange && (
          <div className="relative">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-text-muted/50" />
            <input
              type="text"
              placeholder="Query logs..."
              aria-label="Search conversations"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full bg-elevated/40 text-text placeholder-text-muted/70 text-xs font-heading tracking-wider rounded-input pl-9 pr-4 py-2.5 outline-none border border-white/10 focus:ring-1 focus:ring-accent/30 focus:border-accent-light/50 transition-all"
            />
          </div>
        )}
        {onSortChange && (
          <div className="relative">
            <Calendar className="absolute left-3 top-2.5 w-4 h-4 text-text-muted/50" />
            <select
              value={sortBy}
              onChange={(e) => onSortChange(e.target.value as 'newest' | 'oldest')}
              aria-label="Sort conversations"
              className="w-full bg-elevated/40 text-text text-xs font-heading tracking-widest uppercase rounded-input pl-9 pr-4 py-2.5 outline-none border border-white/10 focus:ring-1 focus:ring-accent/30 focus:border-accent-light/50 appearance-none transition-all"
            >
              <option value="newest" className="bg-surface">Newest First</option>
              <option value="oldest" className="bg-surface">Oldest First</option>
            </select>
          </div>
        )}
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto p-3">
        {filteredAndSortedConversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-4">
            <Inbox className="w-12 h-12 text-text-muted/30 mb-3" />
            <p className="text-xs font-bold text-text-muted tracking-widest uppercase">No Active Link</p>
            <p className="text-[10px] text-text-muted/60 mt-1 tracking-wider">
              {searchQuery ? 'Zero sequences matched query' : 'Ready to spawn conversation'}
            </p>
          </div>
        ) : (
          <ul className="space-y-2">
            <AnimatePresence initial={false}>
              {filteredAndSortedConversations.map((conversation) => {
                const isSelected = selectedId === conversation.id;
                return (
                  <motion.li
                    key={conversation.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    role="button"
                    tabIndex={0}
                    aria-label={`Conversation: ${conversation.title}`}
                    aria-current={isSelected ? 'true' : undefined}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        onSelect(conversation.id)
                      }
                    }}
                    className={`group rounded-card p-3 cursor-pointer border transition-all focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none ${
                      isSelected
                        ? 'bg-accent/15 border-accent/40 shadow-glow-sm'
                        : 'bg-white/5 border-transparent hover:bg-white/10 hover:border-white/10'
                    }`}
                  >
                    {editingId === conversation.id ? (
                      <input
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onBlur={() => handleSaveRename(conversation.id)}
                        onKeyDown={(e) => handleKeyDown(e, conversation.id)}
                        autoFocus
                        className="w-full bg-elevated/80 text-text rounded-input px-3 py-1.5 text-xs border border-accent/40 outline-none"
                      />
                    ) : (
                      <div
                        className="flex items-start justify-between"
                        onClick={() => onSelect(conversation.id)}
                        onDoubleClick={() => handleStartRename(conversation)}
                      >
                        <div className="flex-1 min-w-0">
                          {/* Title */}
                          <div className="text-xs font-bold tracking-wider text-text truncate uppercase">{conversation.title}</div>

                          {/* Last message preview */}
                          {conversation.last_message_preview && (
                            <div className="text-[10px] text-text-muted/70 truncate mt-1 leading-normal tracking-wide">
                              {conversation.last_message_preview}
                            </div>
                          )}

                          {/* Provider and Model */}
                          <div className="flex items-center space-x-1.5 mt-2 flex-wrap gap-y-1">
                            {conversation.provider_name && (
                              <span className="text-[9px] font-bold uppercase tracking-wider bg-white/5 text-text-muted px-1.5 py-0.5 rounded-button border border-white/5">
                                {conversation.provider_name}
                              </span>
                            )}
                            {conversation.model_name && (
                              <span className="text-[9px] font-bold uppercase tracking-wider bg-accent/10 text-accent-light px-1.5 py-0.5 rounded-button border border-accent/20 max-w-[80px] truncate">
                                {conversation.model_name}
                              </span>
                            )}
                            <span className="text-[9px] font-medium tracking-wider text-text-muted/55">
                              {formatRelativeTime(conversation.updated_at)}
                            </span>
                          </div>
                        </div>

                        {/* Action buttons */}
                        <div className="opacity-0 group-hover:opacity-100 flex items-center space-x-1 ml-2 flex-shrink-0 transition-opacity">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleStartRename(conversation);
                            }}
                            className="p-1 text-text-muted hover:text-accent transition-colors focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none rounded-button"
                            aria-label="Rename conversation"
                            title="Rename"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onDelete(conversation.id);
                            }}
                            className="p-1 text-text-muted hover:text-danger transition-colors focus-visible:ring-2 focus-visible:ring-danger/30 focus-visible:outline-none rounded-button"
                            aria-label="Delete conversation"
                            title="Delete"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    )}
                  </motion.li>
                );
              })}
            </AnimatePresence>
          </ul>
        )}
      </div>
    </div>
  );
}

export default ConversationSidebar;