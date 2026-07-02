import { useState } from 'react'
import { ProviderType } from '../../types/provider'

interface ProviderFormProps {
  onSubmit: (data: {
    name: string
    type: string
    api_key: string
    base_url?: string | null
    is_active: boolean
    default_model?: string
    timeout: number
    priority: number
    max_retries: number
    organization_id?: string
    custom_headers?: Record<string, string>
  }) => void
  onCancel: () => void
  initialData?: {
    name?: string
    type?: string
    api_key?: string
    base_url?: string | null
    is_active?: boolean
    default_model?: string
    timeout?: number
    priority?: number
    max_retries?: number
    organization_id?: string
    custom_headers?: Record<string, string>
  }
}

function ProviderForm({ onSubmit, onCancel, initialData }: ProviderFormProps) {
  const [name, setName] = useState(initialData?.name || '')
  const [type, setType] = useState<ProviderType>((initialData?.type || 'openrouter') as ProviderType)
  const [apiKey, setApiKey] = useState(initialData?.api_key || '')
  const [baseUrl, setBaseUrl] = useState(initialData?.base_url || '')
  const [isActive, setIsActive] = useState(initialData?.is_active ?? true)
  const [defaultModel, setDefaultModel] = useState(initialData?.default_model || '')
  const [timeout, setTimeout] = useState(initialData?.timeout ?? 60)
  const [priority, setPriority] = useState(initialData?.priority ?? 0)
  const [maxRetries, setMaxRetries] = useState(initialData?.max_retries ?? 3)
  const [orgId, setOrgId] = useState(initialData?.organization_id || '')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      name,
      type,
      api_key: apiKey,
      base_url: baseUrl || null,
      is_active: isActive,
      default_model: defaultModel || undefined,
      timeout,
      priority,
      max_retries: maxRetries,
      organization_id: orgId || undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 bg-white rounded-lg shadow p-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
        <select
          value={type}
          onChange={(e) => setType(e.target.value as ProviderType)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="openrouter">OpenRouter</option>
          <option value="groq">Groq</option>
          <option value="ollama">Ollama</option>
          <option value="gemini">Gemini</option>
          <option value="lmstudio">LM Studio</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Enter API key"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Base URL (Optional)</label>
        <input
          type="text"
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="https://api.example.com"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Default Model</label>
          <input
            type="text"
            value={defaultModel}
            onChange={(e) => setDefaultModel(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="gpt-4o"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Timeout (s)</label>
          <input
            type="number"
            value={timeout}
            onChange={(e) => setTimeout(Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            min={1}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
          <input
            type="number"
            value={priority}
            onChange={(e) => setPriority(Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Max Retries</label>
          <input
            type="number"
            value={maxRetries}
            onChange={(e) => setMaxRetries(Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            min={0}
            max={10}
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Organization ID (Optional)</label>
        <input
          type="text"
          value={orgId}
          onChange={(e) => setOrgId(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="org-..."
        />
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          id="is_active"
          checked={isActive}
          onChange={(e) => setIsActive(e.target.checked)}
          className="mr-2"
        />
        <label htmlFor="is_active" className="text-sm text-gray-700">Active</label>
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          className="px-4 py-2 bg-primary-500 text-white rounded hover:bg-primary-600"
        >
          {initialData ? 'Update' : 'Create'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

export default ProviderForm
