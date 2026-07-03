import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import { Model } from '../../types/provider'

interface ModelSelectorProps {
  models: Model[]
  selectedModelId: number | null
  onModelSelect: (modelId: number) => void
  isLoading: boolean
  providerId?: number | null
}

export function ModelSelector({
  models,
  selectedModelId,
  onModelSelect,
  isLoading,
}: ModelSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const selectedModel = useMemo(
    () => models.find(m => m.id === selectedModelId) || null,
    [models, selectedModelId]
  )

  const filteredModels = useMemo(() => {
    const q = searchQuery.toLowerCase().trim()
    if (!q) return models
    return models.filter(model =>
      model.name.toLowerCase().includes(q) ||
      (model.display_name && model.display_name.toLowerCase().includes(q))
    )
  }, [models, searchQuery])

  // Reset active index when filtered results change
  useEffect(() => {
    setActiveIndex(-1)
  }, [filteredModels])

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = useCallback((model: Model) => {
    onModelSelect(model.id)
    setIsOpen(false)
    setSearchQuery('')
    setActiveIndex(-1)
  }, [onModelSelect])

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        e.preventDefault()
        setIsOpen(true)
        return
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setActiveIndex(prev => prev < filteredModels.length - 1 ? prev + 1 : prev)
        break
      case 'ArrowUp':
        e.preventDefault()
        setActiveIndex(prev => (prev > 0 ? prev - 1 : -1))
        break
      case 'Enter':
        e.preventDefault()
        if (activeIndex >= 0 && activeIndex < filteredModels.length) {
          handleSelect(filteredModels[activeIndex])
        }
        break
      case 'Escape':
        e.preventDefault()
        setIsOpen(false)
        setActiveIndex(-1)
        break
    }
  }, [isOpen, filteredModels, activeIndex, handleSelect])
  return (
    <div ref={containerRef}>
      <label className="block text-[10px] font-bold text-text-muted uppercase tracking-widest mb-1.5 font-label">Model</label>
      {isLoading ? (
        <div className="space-y-2">
          <div className="h-9 bg-white/5 border border-white/5 rounded-xl animate-pulse" />
          <div className="h-4 w-24 bg-white/5 rounded animate-pulse" />
        </div>
      ) : (
        <div className="relative">
          <input
            ref={inputRef}
            type="text"
            placeholder="Search models..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              if (!isOpen) setIsOpen(true)
            }}
            onFocus={() => setIsOpen(true)}
            onKeyDown={handleKeyDown}
            className="w-full bg-elevated/40 text-text placeholder-text-muted/40 caret-accent selection:bg-accent/30 border border-white/10 rounded-xl px-3 py-2.5 text-xs font-heading tracking-wider focus:outline-none focus:ring-1 focus:ring-accent/30 focus:border-accent-light/50 transition-all"
          />
          {isOpen && (
            <div className="absolute z-50 w-full mt-1 bg-surface border border-white/10 rounded-xl shadow-glass max-h-60 overflow-y-auto p-1 text-xs">
              {filteredModels.length === 0 ? (
                <div className="px-3 py-4 text-text-muted text-center">
                  <div className="font-bold uppercase tracking-widest text-[10px]">No models found</div>
                  <div className="text-[9px] mt-1 tracking-wide">Adjust queries or check active connections.</div>
                </div>
              ) : (
                filteredModels.map((model, index) => (
                  <div
                    key={model.id}
                    onClick={() => handleSelect(model)}
                    className={`px-3 py-2 rounded-lg cursor-pointer transition-all hover:bg-accent/15 hover:text-accent-light text-text ${
                      index === activeIndex ? 'bg-accent/25 text-accent-light font-bold' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-bold tracking-wide uppercase text-[10px]">{model.display_name || model.name}</div>
                        <div className="text-[9px] text-text-muted tracking-wide mt-0.5">{model.name}</div>
                      </div>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {model.supports_streaming !== false && (
                          <span className="text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-success/15 border border-success/30 text-success">Streaming</span>
                        )}
                        {model.max_tokens && (
                          <span className="text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-text-muted">{model.max_tokens} ctx</span>
                        )}
                        {model.supports_vision && (
                          <span className="text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-secondary/15 border border-secondary/30 text-secondary-light">Vision</span>
                        )}
                        {model.supports_reasoning && (
                          <span className="text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-warning/15 border border-warning/30 text-warning">Reasoning</span>
                        )}
                        {model.is_deprecated && (
                          <span className="text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-danger/15 border border-danger/30 text-danger">Deprecated</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
      {selectedModel && !isLoading && (
        <div className="mt-1 flex items-center gap-2 text-xs text-gray-600">
          <span className="font-medium">{selectedModel.display_name || selectedModel.name}</span>
          {selectedModel.supports_streaming !== false && (
            <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">Streaming</span>
          )}
          {selectedModel.max_tokens && (
            <span className="px-1.5 py-0.5 rounded bg-gray-50 text-gray-600 border border-gray-200">{selectedModel.max_tokens} ctx</span>
          )}
          {selectedModel.supports_vision && (
            <span className="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200">Vision</span>
          )}
          {selectedModel.supports_reasoning && (
            <span className="px-1.5 py-0.5 rounded bg-orange-50 text-orange-700 border border-orange-200">Reasoning</span>
          )}
          {selectedModel.is_deprecated && (
            <span className="px-1.5 py-0.5 rounded bg-red-50 text-red-700 border border-red-200">Deprecated</span>
          )}
        </div>
      )}
    </div>
  )
}
