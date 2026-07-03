import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface AgentState {
  selectedAgentId: number | null
  selectAgent: (id: number | null) => void
}

export const useAgentStore = create<AgentState>()(
  devtools(
    persist(
      (set) => ({
        selectedAgentId: null,
        selectAgent: (id) => set({ selectedAgentId: id }),
      }),
      {
        name: 'agent-storage',
      }
    )
  )
)
