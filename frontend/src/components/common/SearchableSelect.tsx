import { useState, useRef, useEffect } from 'react'

interface SearchableSelectProps {
  options: { value: string; label: string }[]
  value?: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
  loading?: boolean
  error?: string
  className?: string
}

export default function SearchableSelect({
  options,
  value,
  onChange,
  placeholder = 'Select an option...',
  disabled = false,
  loading = false,
  error,
  className = '',
}: SearchableSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const selectedOption = options.find((opt) => opt.value === value)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setSearch('')
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  const filteredOptions = options.filter((opt) =>
    opt.label.toLowerCase().includes(search.toLowerCase())
  )

  const handleSelect = (optionValue: string) => {
    onChange(optionValue)
    setIsOpen(false)
    setSearch('')
  }

  const handleInputClick = () => {
    if (!disabled && !loading) {
      setIsOpen(!isOpen)
    }
  }

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div
        role="combobox"
        tabIndex={disabled || loading ? -1 : 0}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        className={`
          flex items-center justify-between
          px-3 py-2 border rounded-input
          bg-elevated/60 backdrop-blur-md
          border-white/10 hover:border-accent-light/30
          cursor-pointer transition-all focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none
          ${disabled || loading ? 'opacity-50 cursor-not-allowed' : ''}
          ${error ? 'border-danger' : ''}
        `}
        onClick={handleInputClick}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            handleInputClick()
          }
        }}
      >
        <span className={selectedOption ? 'text-text font-medium' : 'text-text-muted/60'}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <svg
          className={`w-4 h-4 text-text-muted transition-transform ${isOpen ? 'rotate-180 text-accent-light' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-surface border border-white/10 rounded-panel shadow-glow overflow-hidden">
          <div className="p-2 border-b border-white/5 bg-elevated/20">
            <input
              ref={inputRef}
              type="text"
              aria-label="Search options"
              className="w-full px-3 py-1.5 border border-white/10 rounded-input bg-elevated/40 text-text placeholder-text-muted/70 outline-none focus:ring-1 focus:ring-accent/30 focus:border-accent-light/50 caret-accent selection:bg-accent/30 text-xs font-heading tracking-wider"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onClick={(e) => e.stopPropagation()}
            />
          </div>
          <div className="max-h-60 overflow-y-auto p-1 text-xs">
            {loading ? (
              <div className="px-3 py-2 text-text-muted">Loading...</div>
            ) : filteredOptions.length === 0 ? (
              <div className="px-3 py-2 text-text-muted">No options found</div>
            ) : (
              filteredOptions.map((option) => (
                <div
                  key={option.value}
                  role="option"
                  aria-selected={value === option.value}
                  tabIndex={0}
                  className={`
                    px-3 py-2 rounded-button cursor-pointer transition-all focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none
                    hover:bg-accent/15 hover:text-accent-light
                    ${value === option.value ? 'bg-accent/25 text-accent-light font-bold' : 'text-text'}
                  `}
                  onClick={() => handleSelect(option.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      handleSelect(option.value)
                    }
                  }}
                >
                  {option.label}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {error && <p className="mt-1 text-xs text-danger">{error}</p>}
    </div>
  )
}