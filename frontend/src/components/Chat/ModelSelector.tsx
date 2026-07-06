import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Model } from '../../types/provider'
import { springs } from '../common/Motion'

interface ModelSelectorProps {
  models: Model[]
  selectedModelId: number | null
  onModelSelect: (modelId: number) => void
  isLoading: boolean
  providerId?: number | null
}

interface DropdownPosition {
  top: number
  left: number
  width: number
  direction: 'down' | 'up'
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
  const [dropdownPos, setDropdownPos] = useState<DropdownPosition | null>(null)
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

  // Compute dropdown position relative to viewport when open
  useEffect(() => {
    if (!isOpen || !inputRef.current) {
      // Don't clear dropdownPos immediately — let AnimatePresence play exit animation.
      // The portal condition (isOpen && dropdownPos) will become false when isOpen=false,
      // but dropdownPos stays intact so the portal renders during the exit transition.
      return
    }

    const computePosition = () => {
      const rect = inputRef.current!.getBoundingClientRect()
      const dropdownHeight = 400 // max-height
      const gap = 8 // mt-xs equivalent
      const spaceBelow = window.innerHeight - rect.bottom - gap
      const spaceAbove = rect.top - gap

      // Flip upward if insufficient space below AND more space above
      const direction: 'down' | 'up' =
        spaceBelow < dropdownHeight && spaceAbove > spaceBelow ? 'up' : 'down'

      const top = direction === 'down'
        ? rect.bottom + gap + window.scrollY
        : rect.top - dropdownHeight - gap + window.scrollY

      setDropdownPos({
        top,
        left: rect.left + window.scrollX,
        width: rect.width,
        direction,
      })
    }

    computePosition()

    // Recompute on scroll/resize
    window.addEventListener('scroll', computePosition, { capture: true })
    window.addEventListener('resize', computePosition)
    return () => {
      window.removeEventListener('scroll', computePosition, { capture: true })
      window.removeEventListener('resize', computePosition)
    }
  }, [isOpen])

  // Close on click outside (checks both container and portal dropdown)
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
      <label className="block text-[10px] font-bold text-text-muted uppercase tracking-widest mb-xs font-label">Model</label>
      {isLoading ? (
        <div className="space-y-sm">
          <div className="h-9 bg-white/5 border border-white/5 rounded-input animate-pulse" />
          <div className="h-4 w-24 bg-white/5 rounded-input animate-pulse" />
        </div>
      ) : (
        <div className="relative">
          <input
            ref={inputRef}
            type="text"
            placeholder="Search models..."
            aria-label="Search models"
            aria-expanded={isOpen}
            aria-haspopup="listbox"
            role="combobox"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              if (!isOpen) setIsOpen(true)
            }}
            onFocus={() => setIsOpen(true)}
            onKeyDown={handleKeyDown}
            className="w-full bg-surface/40 text-text placeholder-text-muted/70 caret-accent selection:bg-accent/30 border border-white/10 rounded-input px-md py-sm text-xs font-heading tracking-wider focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent/50 transition-all"
          />
        </div>
      )}
      {selectedModel && !isLoading && (
        <div className="mt-xs flex items-center gap-sm text-xs text-text-muted">
          <span className="font-medium">{selectedModel.display_name || selectedModel.name}</span>
          {selectedModel.supports_streaming !== false && (
            <span className="badge-success text-[8px]">Streaming</span>
          )}
          {selectedModel.max_tokens && (
            <span className="badge-neutral text-[8px]">{selectedModel.max_tokens} ctx</span>
          )}
          {selectedModel.supports_vision && (
            <span className="badge-secondary text-[8px]">Vision</span>
          )}
          {selectedModel.supports_reasoning && (
            <span className="badge-warning text-[8px]">Reasoning</span>
          )}
          {selectedModel.is_deprecated && (
            <span className="badge-danger text-[8px]">Deprecated</span>
          )}
        </div>
      )}

      {/* Portal dropdown — rendered to document.body to escape all overflow:hidden parents.
      The portal mounts when dropdownPos is set (by the position effect).
      AnimatePresence wraps the dropdown content, which is conditioned on isOpen
      so that setting isOpen=false triggers the exit animation. */}
      {dropdownPos &&
      createPortal(
      <AnimatePresence onExitComplete={() => setDropdownPos(null)}>
      {isOpen && (
      <motion.div
      key="model-dropdown"
      initial={{ opacity: 0, y: dropdownPos.direction === 'down' ? -8 : 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: dropdownPos.direction === 'down' ? -8 : 8 }}
      transition={springs.smooth}
      style={{
      position: 'absolute',
      top: dropdownPos.top,
      left: dropdownPos.left,
      width: dropdownPos.width,
      zIndex: 9999,
      }}
      role="listbox"
      className="glass-elevated rounded-panel shadow-glow max-h-[400px] overflow-y-auto p-xs text-xs"
      >
              {filteredModels.length === 0 ? (
                <div className="px-md py-md text-text-muted text-center">
                  <div className="font-bold uppercase tracking-widest text-[10px]">No models found</div>
                  <div className="text-[9px] mt-xs tracking-wide">Adjust queries or check active connections.</div>
                </div>
              ) : (
                filteredModels.map((model, index) => (
                  <div
                    key={model.id}
                    role="option"
                    tabIndex={0}
                    aria-selected={index === activeIndex}
                    onClick={() => handleSelect(model)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        handleSelect(model)
                      }
                    }}
                    className={`px-md py-sm rounded-button cursor-pointer transition-all hover:bg-accent/15 hover:text-accent-light text-text focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none ${
                      index === activeIndex ? 'bg-accent/25 text-accent-light font-bold' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-bold tracking-wide uppercase text-[10px]">{model.display_name || model.name}</div>
                        <div className="text-[9px] text-text-muted tracking-wide mt-xs">{model.name}</div>
                      </div>
                      <div className="flex items-center gap-xs flex-wrap">
                        {model.supports_streaming !== false && (
                          <span className="text-[8px] font-bold uppercase tracking-wider px-xs py-xs rounded-button bg-success/15 border border-success/30 text-success">Streaming</span>
                        )}
                        {model.max_tokens && (
                          <span className="text-[8px] font-bold uppercase tracking-wider px-xs py-xs rounded-button bg-white/5 border border-white/10 text-text-muted">{model.max_tokens} ctx</span>
                        )}
                        {model.supports_vision && (
                          <span className="text-[8px] font-bold uppercase tracking-wider px-xs py-xs rounded-button bg-secondary/15 border border-secondary/30 text-secondary-light">Vision</span>
                        )}
                        {model.supports_reasoning && (
                          <span className="text-[8px] font-bold uppercase tracking-wider px-xs py-xs rounded-button bg-warning/15 border border-warning/30 text-warning">Reasoning</span>
                        )}
                        {model.is_deprecated && (
                          <span className="text-[8px] font-bold uppercase tracking-wider px-xs py-xs rounded-button bg-danger/15 border border-danger/30 text-danger">Deprecated</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
              </motion.div>
              )}
              </AnimatePresence>,
          document.body
        )}
    </div>
  )
}
