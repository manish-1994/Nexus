import axios from 'axios'
import { showError, getHttpErrorMessage } from '../utils/toast'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// Response interceptor - show toast for HTTP errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = getHttpErrorMessage(error)
    const status = error?.response?.status

    if (status) {
      switch (status) {
        case 400:
          showError('Bad Request', { description: message })
          break
        case 401:
          showError('Authentication Error', { description: 'Invalid or expired credentials.' })
          break
        case 403:
          showError('Access Denied', { description: message })
          break
        case 404:
          showError('Not Found', { description: message })
          break
        case 429:
          showError('Rate Limited', { description: 'Too many requests. Please try again later.' })
          break
        case 500:
          showError('Server Error', { description: 'Internal server error. Please try again.' })
          break
        case 502:
          showError('Bad Gateway', { description: 'Unable to reach the backend.' })
          break
        case 503:
          showError('Service Unavailable', { description: 'Service temporarily unavailable.' })
          break
        case 504:
          showError('Gateway Timeout', { description: 'Request timed out. Please try again.' })
          break
        default:
          showError('Request Failed', { description: message })
      }
    } else {
      showError('Network Error', { description: 'Unable to reach the backend.' })
    }
    
    return Promise.reject(error)
  }
)
