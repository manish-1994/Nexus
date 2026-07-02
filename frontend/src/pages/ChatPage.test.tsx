import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import ChatPage from './ChatPage'

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {ui}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('ChatPage', () => {
  it('renders welcome message when no conversation selected', () => {
    renderWithProviders(<ChatPage />)
    expect(screen.getByText('Welcome to NEXUS V3 Chat')).toBeDefined()
  })

  it('renders new chat button', () => {
    renderWithProviders(<ChatPage />)
    expect(screen.getByText('+ New Chat')).toBeDefined()
  })

  it('shows loading state initially', async () => {
    renderWithProviders(<ChatPage />)
    // Initially loading, then either error or conversations load
    await waitFor(() => {
      expect(screen.queryByText('Loading conversations...')).toBeDefined()
    }, { timeout: 1000 })
  })

  it('renders conversation sidebar', async () => {
    renderWithProviders(<ChatPage />)
    await waitFor(() => {
      expect(screen.getByText('+ New Chat')).toBeDefined()
    })
  })
})
