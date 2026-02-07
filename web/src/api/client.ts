import axios from 'axios'
import type { AxiosError } from 'axios'

const ENV_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const ENV_API_KEY = import.meta.env.VITE_API_KEY ?? ''

export const API_KEY_STORAGE = 'easm_api_key'
export const API_BASE_URL_STORAGE = 'easm_api_base_url'

export const apiClient = axios.create({
  baseURL: ENV_BASE_URL,
  timeout: 15000,
})

apiClient.interceptors.request.use((config) => {
  const runtimeBaseUrl = localStorage.getItem(API_BASE_URL_STORAGE)
  const runtimeApiKey = localStorage.getItem(API_KEY_STORAGE)

  if (runtimeBaseUrl && runtimeBaseUrl.trim()) {
    config.baseURL = runtimeBaseUrl.trim()
  }

  const apiKey = runtimeApiKey?.trim() || ENV_API_KEY
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey
  }

  return config
})

function extractDetailMessage(detail: unknown): string | null {
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === 'string') {
          return item
        }
        if (item && typeof item === 'object' && 'msg' in item) {
          const msg = item.msg
          return typeof msg === 'string' ? msg : ''
        }
        return ''
      })
      .filter(Boolean)
    if (messages.length) {
      return messages.join('; ')
    }
  }

  if (detail && typeof detail === 'object' && 'msg' in detail) {
    const msg = detail.msg
    if (typeof msg === 'string' && msg.trim()) {
      return msg
    }
  }

  return null
}

export function getErrorMessage(error: unknown): string {
  const axiosError = error as AxiosError<{ detail?: unknown; message?: string }>
  if (axios.isAxiosError(error) && axiosError.response?.data) {
    const { detail, message } = axiosError.response.data
    const detailMessage = extractDetailMessage(detail)
    if (detailMessage) {
      return detailMessage
    }
    if (typeof message === 'string' && message.trim()) {
      return message
    }
  }

  if (typeof axiosError?.message === 'string' && axiosError.message.trim()) {
    return axiosError.message
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return '请求失败，请稍后重试'
}

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => Promise.reject(new Error(getErrorMessage(error))),
)
