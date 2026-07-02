import { toast } from 'sonner'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastOptions {
  description?: string
  duration?: number
}

const TOAST_DURATION = 4000

export function showToast(type: ToastType, message: string, options?: ToastOptions) {
  const duration = options?.duration ?? TOAST_DURATION

  switch (type) {
    case 'success':
      return toast.success(message, {
        description: options?.description,
        duration,
      })
    case 'error':
      return toast.error(message, {
        description: options?.description,
        duration,
      })
    case 'warning':
      return toast.warning(message, {
        description: options?.description,
        duration,
      })
    case 'info':
      return toast.info(message, {
        description: options?.description,
        duration,
      })
    default:
      return toast(message, {
        description: options?.description,
        duration,
      })
  }
}

export function showSuccess(message: string, options?: ToastOptions) {
  return showToast('success', message, options)
}

export function showError(message: string, options?: ToastOptions) {
  return showToast('error', message, options)
}

export function showWarning(message: string, options?: ToastOptions) {
  return showToast('warning', message, options)
}

export function showInfo(message: string, options?: ToastOptions) {
  return showToast('info', message, options)
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  if (typeof error === 'string') return error
  if (error && typeof error === 'object' && 'detail' in error) {
    const detail = (error as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0 && typeof detail[0] === 'object' && 'msg' in detail[0]) {
      return (detail[0] as { msg: string }).msg
    }
  }
  if (error && typeof error === 'object' && 'message' in error) {
    return String((error as { message: unknown }).message)
  }
  return 'An unexpected error occurred'
}

export function getHttpErrorMessage(error: unknown): string {
  if (error && typeof error === 'object') {
    const err = error as {
      response?: { status?: number; data?: { detail?: unknown } }
      message?: string
    }
    if (err.response?.data?.detail) {
      const detail = err.response.data.detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail) && detail.length > 0 && typeof detail[0] === 'object' && 'msg' in detail[0]) {
        return (detail[0] as { msg: string }).msg
      }
    }
    if (err.message) return err.message
  }
  return getErrorMessage(error)
}
