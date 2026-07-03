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
      <div className="fixed inset-0 bg-black/30" onClick={onClose} />
      <div className="relative w-full max-w-2xl bg-white dark:bg-gray-800 shadow-2xl flex flex-col h-full border-l border-gray-200 dark:border-gray-700 animate-slide-in-right">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold">Edit Agent</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-4 space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Name *</label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleChange}
                className="w-full border rounded p-2 bg-transparent"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Description</label>
              <input
                type="text"
                name="description"
                value={formData.description || ''}
                onChange={handleChange}
                className="w-full border rounded p-2 bg-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Icon</label>
              <input
                type="text"
                name="icon"
                placeholder="e.g. bot, code, brain"
                value={formData.icon || ''}
                onChange={handleChange}
                className="w-full border rounded p-2 bg-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Color</label>
              <select
                name="color"
                value={formData.color || 'blue'}
                onChange={handleChange}
                className="w-full border rounded p-2 bg-transparent"
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
              <label className="block text-sm font-medium mb-1">Provider</label>
              <select
                name="provider_id"
                value={formData.provider_id || ''}
                onChange={handleChange}
                className="w-full border rounded p-2 bg-transparent"
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
              <label className="block text-sm font-medium mb-1">Model</label>
              <input
                type="text"
                name="preferred_model_id"
                value={formData.preferred_model_id || ''}
                onChange={handleChange}
                className="w-full border rounded p-2 bg-transparent"
                placeholder="e.g. claude-3-sonnet"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Temperature</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="2"
                name="temperature"
                value={formData.temperature}
                onChange={handleChange}
                className="w-full border rounded p-2 bg-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Top P</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                name="top_p"
                value={formData.top_p}
                onChange={handleChange}
                className="w-full border rounded p-2 bg-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Max Tokens</label>
              <input
                type="number"
                name="max_tokens"
                value={formData.max_tokens || ''}
                onChange={handleChange}
                className="w-full border rounded p-2 bg-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Presence Penalty</label>
              <input
                type="number"
                step="0.1"
                min="-2"
                max="2"
                name="presence_penalty"
                value={formData.presence_penalty}
                onChange={handleChange}
                className="w-full border rounded p-2 bg-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Frequency Penalty</label>
              <input
                type="number"
                step="0.1"
                min="-2"
                max="2"
                name="frequency_penalty"
                value={formData.frequency_penalty}
                onChange={handleChange}
                className="w-full border rounded p-2 bg-transparent"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">System Prompt</label>
              <textarea
                name="prompt_template"
                rows={4}
                value={formData.prompt_template || ''}
                onChange={handleChange}
                className="w-full border rounded p-2 bg-transparent"
                placeholder="You are a helpful assistant..."
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Capabilities (comma separated)</label>
              <input
                type="text"
                name="capabilities"
                value={formData.capabilities || ''}
                onChange={handleChange}
                className="w-full border rounded p-2 bg-transparent"
              />
            </div>

            <div className="col-span-2 flex gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="streaming"
                  checked={formData.streaming}
                  onChange={handleChange}
                />
                <span className="text-sm font-medium">Streaming</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="memory_enabled"
                  checked={formData.memory_enabled}
                  onChange={handleChange}
                />
                <span className="text-sm font-medium">Memory Enabled</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="enabled"
                  checked={formData.enabled}
                  onChange={handleChange}
                />
                <span className="text-sm font-medium">Enabled</span>
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
