import { useState, useEffect } from 'react'
import { agentApi } from '../../services/agentApi'
import { useProviderStore } from '../../stores/providerStore'
import { Agent, AgentUpdate } from '../../types/agent'
import { toast } from 'sonner'
import { useQueryClient } from '@tanstack/react-query'

interface AgentEditDrawerProps {
  agent: Agent
  onClose: () => void
}

export function AgentEditDrawer({ agent, onClose }: AgentEditDrawerProps) {
  const queryClient = useQueryClient()
  const providers = useProviderStore(state => state.providers)

  const [formData, setFormData] = useState<AgentUpdate>({
    name: agent.name,
    description: agent.description || '',
    icon: agent.icon || 'bot',
    color: agent.color || 'blue',
    provider_id: agent.provider_id,
    preferred_model_id: agent.preferred_model_id || undefined,
    temperature: agent.temperature,
    top_p: agent.top_p,
    max_tokens: agent.max_tokens || 4096,
    streaming: agent.streaming,
    enabled: agent.enabled,
    prompt_template: agent.prompt_template || '',
    capabilities: agent.capabilities || '',
    memory_enabled: agent.memory_enabled,
    presence_penalty: agent.presence_penalty,
    frequency_penalty: agent.frequency_penalty,
  })

  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    setFormData({
      name: agent.name,
      description: agent.description || '',
      icon: agent.icon || 'bot',
      color: agent.color || 'blue',
      provider_id: agent.provider_id,
      preferred_model_id: agent.preferred_model_id || undefined,
      temperature: agent.temperature,
      top_p: agent.top_p,
      max_tokens: agent.max_tokens || 4096,
      streaming: agent.streaming,
      enabled: agent.enabled,
      prompt_template: agent.prompt_template || '',
      capabilities: agent.capabilities || '',
      memory_enabled: agent.memory_enabled,
      presence_penalty: agent.presence_penalty,
      frequency_penalty: agent.frequency_penalty,
    })
  }, [agent])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      await agentApi.updateAgent(agent.id, formData)
      toast.success('Agent updated successfully')
      queryClient.invalidateQueries({ queryKey: ['agents'] })
      onClose()
    } catch (error) {
      console.error(error)
      toast.error('Failed to update agent')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target
    let parsedValue: string | number | boolean = value
    if (type === 'checkbox') {
      parsedValue = (e.target as HTMLInputElement).checked
    } else if (type === 'number') {
      parsedValue = Number(value)
    }
    setFormData(prev => ({ ...prev, [name]: parsedValue }))
  }

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-2xl glass-elevated shadow-elevated flex flex-col h-full border-l border-white/10 animate-slide-in-right rounded-dialog">
        <div className="flex items-center justify-between p-lg border-b border-white/5">
          <h2 className="text-xl font-bold text-text font-heading">Edit Agent</h2>
          <button onClick={onClose} className="text-text-muted hover:text-text transition-colors duration-fast focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none rounded-button p-xs">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-lg space-y-lg">
          <div className="grid grid-cols-2 gap-md">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-text mb-1">Name *</label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleChange}
                className="input-standard w-full"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-text mb-1">Description</label>
              <input
                type="text"
                name="description"
                value={formData.description || ''}
                onChange={handleChange}
                className="input-standard w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">Icon</label>
              <input
                type="text"
                name="icon"
                placeholder="e.g. bot, code, brain"
                value={formData.icon || ''}
                onChange={handleChange}
                className="input-standard w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">Color</label>
              <select
                name="color"
                value={formData.color || 'blue'}
                onChange={handleChange}
                className="input-standard w-full"
              >
                <option value="blue">Blue</option>
                <option value="green">Green</option>
                <option value="red">Red</option>
                <option value="purple">Purple</option>
                <option value="yellow">Yellow</option>
                <option value="gray">Gray</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">Provider</label>
              <select
                name="provider_id"
                value={formData.provider_id || ''}
                onChange={handleChange}
                className="input-standard w-full"
              >
                <option value="">Default Provider</option>
                {providers.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">Model</label>
              <input
                type="text"
                name="preferred_model_id"
                value={formData.preferred_model_id || ''}
                onChange={handleChange}
                className="input-standard w-full"
                placeholder="e.g. claude-3-sonnet"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">Temperature</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="2"
                name="temperature"
                value={formData.temperature}
                onChange={handleChange}
                className="input-standard w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">Top P</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                name="top_p"
                value={formData.top_p}
                onChange={handleChange}
                className="input-standard w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">Max Tokens</label>
              <input
                type="number"
                name="max_tokens"
                value={formData.max_tokens || ''}
                onChange={handleChange}
                className="input-standard w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">Presence Penalty</label>
              <input
                type="number"
                step="0.1"
                min="-2"
                max="2"
                name="presence_penalty"
                value={formData.presence_penalty}
                onChange={handleChange}
                className="input-standard w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">Frequency Penalty</label>
              <input
                type="number"
                step="0.1"
                min="-2"
                max="2"
                name="frequency_penalty"
                value={formData.frequency_penalty}
                onChange={handleChange}
                className="input-standard w-full"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-text mb-1">System Prompt</label>
              <textarea
                name="prompt_template"
                rows={4}
                value={formData.prompt_template || ''}
                onChange={handleChange}
                className="input-standard w-full resize-y"
                placeholder="You are a helpful assistant..."
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-text mb-1">Capabilities (comma separated)</label>
              <input
                type="text"
                name="capabilities"
                value={formData.capabilities || ''}
                onChange={handleChange}
                className="input-standard w-full"
              />
            </div>

            <div className="col-span-2 flex gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="streaming"
                  checked={formData.streaming}
                  onChange={handleChange}
                  className="accent-accent"
                />
                <span className="text-sm font-medium text-text">Streaming</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="memory_enabled"
                  checked={formData.memory_enabled}
                  onChange={handleChange}
                  className="accent-accent"
                />
                <span className="text-sm font-medium text-text">Memory Enabled</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="enabled"
                  checked={formData.enabled}
                  onChange={handleChange}
                  className="accent-accent"
                />
                <span className="text-sm font-medium text-text">Enabled</span>
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-sm pt-md border-t border-white/5">
            <button
              type="button"
              onClick={onClose}
              className="px-md py-sm border border-white/10 rounded-button text-text-muted hover:bg-white/5 transition-colors duration-fast focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-md py-sm bg-accent text-white rounded-button hover:bg-accent-dark disabled:opacity-50 transition-colors duration-fast focus-visible:ring-2 focus-visible:ring-accent/30 focus-visible:outline-none"
            >
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
