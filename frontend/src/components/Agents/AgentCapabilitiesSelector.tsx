import { useState, useRef, useEffect } from 'react'

interface AgentCapabilitiesSelectorProps {
  selected: string[]
  onChange: (capabilities: string[]) => void
  disabled?: boolean
}

const AVAILABLE_CAPABILITIES = [
  { id: 'chat', label: 'Chat', description: 'Conversational AI capabilities', icon: '💬' },
  { id: 'code', label: 'Code Generation', description: 'Generate and analyze code', icon: '💻' },
  { id: 'analysis', label: 'Analysis', description: 'Data analysis and insights', icon: '📊' },
  { id: 'writing', label: 'Writing', description: 'Content creation and editing', icon: '✍️' },
  { id: 'research', label: 'Research', description: 'Information gathering and synthesis', icon: '🔍' },
  { id: 'planning', label: 'Planning', description: 'Task planning and organization', icon: '📋' },
  { id: 'translation', label: 'Translation', description: 'Language translation', icon: '🌐' },
  { id: 'summarization', label: 'Summarization', description: 'Text summarization', icon: '📝' },
  { id: 'reasoning', label: 'Reasoning', description: 'Logical reasoning and problem solving', icon: '🧠' },
  { id: 'creative', label: 'Creative', description: 'Creative content generation', icon: '🎨' },
  { id: 'math', label: 'Mathematics', description: 'Mathematical computation', icon: '🔢' },
  { id: 'vision', label: 'Vision', description: 'Image understanding and analysis', icon: '👁️' },
  { id: 'audio', label: 'Audio', description: 'Audio processing and generation', icon: '🎵' },
  { id: 'tool_use', label: 'Tool Use', description: 'External tool integration', icon: '🔧' },
  { id: 'memory', label: 'Memory', description: 'Long-term memory and context', icon: '💾' },
]

export function AgentCapabilitiesSelector({
  selected,
  onChange,
  disabled = false,
}: AgentCapabilitiesSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const filteredCapabilities = AVAILABLE_CAPABILITIES.filter(
    cap =>
      cap.label.toLowerCase().includes(search.toLowerCase()) ||
      cap.description.toLowerCase().includes(search.toLowerCase())
  )

  const toggleCapability = (capId: string) => {
    if (disabled) return
    const newSelected = selected.includes(capId)
      ? selected.filter(id => id !== capId)
      : [...selected, capId]
    onChange(newSelected)
  }

  const removeCapability = (capId: string) => {
    if (disabled) return
    onChange(selected.filter(id => id !== capId))
  }

  const selectedCaps = AVAILABLE_CAPABILITIES.filter(cap => selected.includes(cap.id))

  return (
    <div className="relative" ref={dropdownRef}>
      <div
        className={`w-full border rounded-lg p-2 min-h-[42px] flex flex-wrap gap-1 items-center cursor-pointer bg-transparent ${
          disabled ? 'opacity-50 cursor-not-allowed' : ''
        }`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
      >
        {selectedCaps.length === 0 ? (
          <span className="text-sm text-gray-400 px-1">Select capabilities...</span>
        ) : (
          selectedCaps.map(cap => (
            <span
              key={cap.id}
              className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full border border-blue-200 dark:border-blue-800"
            >
              <span>{cap.icon}</span>
              <span>{cap.label}</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  removeCapability(cap.id)
                }}
                className="ml-0.5 hover:text-blue-900 dark:hover:text-blue-100"
                disabled={disabled}
              >
                ×
              </button>
            </span>
          ))
        )}
        <span className="ml-auto text-gray-400 text-xs">{isOpen ? '▲' : '▼'}</span>
      </div>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-64 overflow-hidden">
          <div className="p-2 border-b border-gray-200 dark:border-gray-700">
            <input
              type="text"
              placeholder="Search capabilities..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full border rounded p-1.5 text-sm bg-transparent focus:outline-none focus:ring-1 focus:ring-blue-500"
              autoFocus
            />
          </div>
          <div className="overflow-y-auto max-h-48">
            {filteredCapabilities.length === 0 ? (
              <div className="p-3 text-sm text-gray-500 text-center">No capabilities found</div>
            ) : (
              filteredCapabilities.map(cap => {
                const isSelected = selected.includes(cap.id)
                return (
                  <div
                    key={cap.id}
                    className={`flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                      isSelected ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                    }`}
                    onClick={() => toggleCapability(cap.id)}
                  >
                    <div
                      className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 ${
                        isSelected
                          ? 'bg-blue-600 border-blue-600 text-white'
                          : 'border-gray-300 dark:border-gray-600'
                      }`}
                    >
                      {isSelected && (
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                    <span className="text-lg">{cap.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">{cap.label}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 truncate">{cap.description}</div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}