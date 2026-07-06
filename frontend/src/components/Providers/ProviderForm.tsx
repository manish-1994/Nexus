import { useState, useEffect } from 'react'
import { ProviderType, Model } from '../../types/provider'
import { providersApi } from '../../api/providers'
import SearchableSelect from '../common/SearchableSelect'

interface ProviderFormProps {
  onSubmit: (data: {
    name: string
    type: ProviderType
    api_key?: string
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
    id?: number
    name?: string
    type?: ProviderType
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

// Provider types that don't require API key
const LOCAL_TYPES: ProviderType[] = ['ollama', 'lmstudio']

// Provider types that typically need base_url
const CUSTOM_URL_TYPES: ProviderType[] = [
  'openai_compatible',
  'ollama',
  'lmstudio',
  'custom',
]

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
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverErrors, setServerErrors] = useState<string[]>([])

  const [models, setModels] = useState<Model[]>([])
  const [modelsLoading, setModelsLoading] = useState(false)
  const [discoveryError, setDiscoveryError] = useState<string | null>(null)
  const [discoveredAt, setDiscoveredAt] = useState<string | null>(null)

  const requiresApiKey = !LOCAL_TYPES.includes(type)
  const showsBaseUrl = CUSTOM_URL_TYPES.includes(type)

  const canDiscoverModels = showsBaseUrl && baseUrl && (requiresApiKey ? apiKey : true)

  useEffect(() => {
    const fetchModels = async () => {
      if (!initialData?.id) return
      try {
        setModelsLoading(true)
        setDiscoveryError(null)
        const data = await providersApi.listModels(initialData.id)
        setModels(data)
        if (data.length > 0) {
          setDiscoveredAt(new Date().toISOString())
        }
      } catch {
        setDiscoveryError('Failed to load existing models')
      } finally {
        setModelsLoading(false)
      }
    }
    fetchModels()
  }, [initialData?.id, type, baseUrl])

  const handleDiscoverModels = async () => {
    if (!initialData?.id) return
    try {
      setModelsLoading(true)
      setDiscoveryError(null)
      const data = await providersApi.discoverModels(initialData.id)
      setModels(data)
      setDiscoveredAt(new Date().toISOString())
      if (data.length === 0) {
        setDiscoveryError('No models found. Check your Base URL and API key.')
      }
    } catch {
      setDiscoveryError('Model discovery failed. Please check your configuration and try again.')
    } finally {
      setModelsLoading(false)
    }
  }

  const validate = async (): Promise<boolean> => {
    const newErrors: Record<string, string> = {}
    const newServerErrors: string[] = []

    if (!name.trim()) {
      newErrors.name = 'Provider name is required'
    } else if (name.length > 255) {
      newErrors.name = 'Name must be 255 characters or less'
    }

    if (showsBaseUrl && baseUrl) {
      const urlPattern = /^https?:\/\/.+/i
      if (!urlPattern.test(baseUrl)) {
        newErrors.base_url = 'URL must start with http:// or https://'
      }
    }

    if (requiresApiKey && !apiKey.trim()) {
      newErrors.api_key = 'API key is required for this provider type'
    }

    setErrors(newErrors)

    if (Object.keys(newErrors).length === 0) {
      try {
        const result = await providersApi.validate({
          name: name.trim(),
          type,
          base_url: baseUrl || undefined,
          api_key: apiKey || undefined,
        })
        if (!result.valid) {
          newServerErrors.push(...result.errors)
        }
      } catch {
        newServerErrors.push('Validation service unavailable')
      }
    }

    setServerErrors(newServerErrors)
    return Object.keys(newErrors).length === 0 && newServerErrors.length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    onSubmit({
      name: name.trim(),
      type,
      api_key: apiKey || undefined,
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
    <form onSubmit={handleSubmit} className="space-y-4 glass-surface rounded-card p-lg">
      {/* Name */}
      <div>
        <label className="block text-sm font-medium text-text mb-1">
          Provider Name <span className="text-danger">*</span>
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={`input-standard w-full ${
            errors.name ? 'border-danger focus:ring-danger/30' : ''
          }`}
          placeholder="My Provider"
        />
        {errors.name && <p className="text-danger text-xs mt-1">{errors.name}</p>}
      </div>

      {/* Type */}
      <div>
        <label className="block text-sm font-medium text-text mb-1">
          Provider Type <span className="text-danger">*</span>
        </label>
        <select
          value={type}
          onChange={(e) => setType(e.target.value as ProviderType)}
          className="input-standard w-full"
        >
          <option value="openai_compatible">OpenAI Compatible</option>
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
          <option value="gemini">Gemini</option>
          <option value="groq">Groq</option>
          <option value="openrouter">OpenRouter</option>
          <option value="ollama">Ollama</option>
          <option value="lmstudio">LM Studio</option>
          <option value="nvidia_nim">NVIDIA NIM</option>
          <option value="azure_openai">Azure OpenAI</option>
          <option value="mistral">Mistral</option>
          <option value="together_ai">Together AI</option>
          <option value="deepseek">DeepSeek</option>
          <option value="cohere">Cohere</option>
          <option value="xai">xAI</option>
          <option value="perplexity">Perplexity</option>
          <option value="custom">Custom</option>
        </select>
      </div>

      {/* API Key */}
      {requiresApiKey && (
        <div>
          <label className="block text-sm font-medium text-text mb-1">
            API Key <span className="text-danger">*</span>
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className={`input-standard w-full ${
              errors.api_key ? 'border-danger focus:ring-danger/30' : ''
            }`}
            placeholder="sk-..."
          />
          {errors.api_key && <p className="text-danger text-xs mt-1">{errors.api_key}</p>}
        </div>
      )}

      {/* Base URL */}
      {showsBaseUrl && (
        <div>
          <label className="block text-sm font-medium text-text mb-1">
            Base URL {type === 'openai_compatible' && <span className="text-danger">*</span>}
          </label>
          <input
            type="text"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            className={`input-standard w-full ${
              errors.base_url ? 'border-danger focus:ring-danger/30' : ''
            }`}
            placeholder="http://localhost:11434 or https://api.example.com"
          />
          {errors.base_url && <p className="text-danger text-xs mt-1">{errors.base_url}</p>}
          {type === 'openai_compatible' && (
            <p className="text-text-muted text-xs mt-1">
              Models will be auto-discovered from /models endpoint
            </p>
          )}
        </div>
      )}
      
      {/* Model Discovery */}
      {showsBaseUrl && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-text">Models</label>
            {initialData?.id && (
              <button
                type="button"
                onClick={handleDiscoverModels}
                disabled={!canDiscoverModels || modelsLoading}
                className="text-sm px-3 py-1 bg-accent text-white rounded-button hover:bg-accent-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-fast focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
              >
                {modelsLoading ? 'Discovering...' : discoveredAt ? 'Refresh Models' : 'Discover Models'}
              </button>
            )}
          </div>
      
          {discoveryError && (
            <div className="p-2 bg-warning/10 border border-warning/30 rounded-button">
              <p className="text-sm text-warning">{discoveryError}</p>
            </div>
          )}
      
          {discoveredAt && !discoveryError && (
            <p className="text-xs text-text-muted">
              Last discovered: {new Date(discoveredAt).toLocaleString()}
            </p>
          )}
      
          {models.length > 0 && (
            <div className="text-sm text-text-muted">
              {models.length} model{models.length !== 1 ? 's' : ''} discovered
            </div>
          )}
        </div>
      )}
      
      {/* Default Model */}
      {showsBaseUrl ? (
        <div>
          <label className="block text-sm font-medium text-text mb-1">Default Model</label>
          <SearchableSelect
            options={models.map((model) => ({
              value: model.name,
              label: model.display_name || model.name,
            }))}
            value={defaultModel}
            onChange={setDefaultModel}
            placeholder={modelsLoading ? 'Discovering models...' : 'Select a model...'}
            disabled={modelsLoading}
          />
          {models.length === 0 && !modelsLoading && (
            <p className="text-text-muted text-xs mt-1">
              Click Discover Models to load available models
            </p>
          )}
        </div>
      ) : (
        <div>
          <label className="block text-sm font-medium text-text mb-1">Default Model</label>
          <input
            type="text"
            value={defaultModel}
            onChange={(e) => setDefaultModel(e.target.value)}
            className="input-standard w-full"
            placeholder="gpt-4o"
          />
        </div>
      )}

      {/* Timeout & Priority */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-text mb-1">Timeout (s)</label>
          <input
            type="number"
            value={timeout}
            onChange={(e) => setTimeout(Number(e.target.value))}
            className="input-standard w-full"
            min={1}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-text mb-1">Priority</label>
          <input
            type="number"
            value={priority}
            onChange={(e) => setPriority(Number(e.target.value))}
            className="input-standard w-full"
          />
        </div>
      </div>

      {/* Max Retries & Org ID */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-text mb-1">Max Retries</label>
          <input
            type="number"
            value={maxRetries}
            onChange={(e) => setMaxRetries(Number(e.target.value))}
            className="input-standard w-full"
            min={0}
            max={10}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-text mb-1">Organization ID</label>
          <input
            type="text"
            value={orgId}
            onChange={(e) => setOrgId(e.target.value)}
            className="input-standard w-full"
            placeholder="org-..."
          />
        </div>
      </div>

      {/* Active Checkbox */}
      <div className="flex items-center">
        <input
          type="checkbox"
          id="is_active"
          checked={isActive}
          onChange={(e) => setIsActive(e.target.checked)}
          className="mr-2 accent-accent"
        />
        <label htmlFor="is_active" className="text-sm text-text">
          Active
        </label>
      </div>

      {/* Server Errors */}
      {serverErrors.length > 0 && (
        <div className="p-3 bg-danger/10 border border-danger/30 rounded-button">
          {serverErrors.map((error, index) => (
            <p key={index} className="text-sm text-danger">{error}</p>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          type="submit"
          className="px-4 py-2 bg-accent text-white rounded-button hover:bg-accent-dark transition-colors duration-fast focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
        >
          {initialData ? 'Update' : 'Create'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-white/5 text-text-muted rounded-button hover:bg-white/10 transition-colors duration-fast focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

export default ProviderForm