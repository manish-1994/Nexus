import { create } from 'zustand'

interface ModelState {
    selectedModelId: number | null
    selectModel: (id: number | null) => void
}

export const useModelStore = create<ModelState>((set) => ({
    selectedModelId: null,
    selectModel: (id) => {
        set({ selectedModelId: id })
    },
}))
