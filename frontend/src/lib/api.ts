import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios'

interface ApiMethods {
  get<T>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T>(
    url: string,
    body?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T>
  put<T>(
    url: string,
    body?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T>
  patch<T>(
    url: string,
    body?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T>
  delete<T>(url: string, config?: AxiosRequestConfig): Promise<T>
}

type ApiClient = Omit<
  AxiosInstance,
  'get' | 'post' | 'put' | 'patch' | 'delete'
> &
  ApiMethods

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
}) as ApiClient

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  }
)

// On a 401, the access token has almost certainly expired (15-min TTL).
// Transparently refresh once using the stored refresh token and replay the
// original request; if refresh fails, clear tokens and bounce to /login.
// A shared promise coalesces concurrent 401s so we refresh only once.
let refreshPromise: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  if (typeof window === 'undefined') return null
  const refresh = localStorage.getItem('refresh_token')
  if (!refresh) return null
  try {
    // Bare axios (not apiClient) to skip the unwrap + auth interceptors.
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const resp = await axios.post(`${base}/api/auth/refresh`, {
      refresh_token: refresh,
    })
    localStorage.setItem('access_token', resp.data.access_token)
    localStorage.setItem('refresh_token', resp.data.refresh_token)
    return resp.data.access_token as string
  } catch {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    return null
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined
    const status = error.response?.status
    if (
      status === 401 &&
      original &&
      !original._retry &&
      !original.url?.includes('/api/auth/')
    ) {
      original._retry = true
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null
        })
      }
      const token = await refreshPromise
      if (token) {
        original.headers = original.headers ?? {}
        original.headers.Authorization = `Bearer ${token}`
        return apiClient.request(original)
      }
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

async function data<T>(request: Promise<AxiosResponse<T>>): Promise<T> {
  const response = await request
  return response.data
}

const axiosGet = apiClient.get.bind(apiClient) as AxiosInstance['get']
const axiosPost = apiClient.post.bind(apiClient) as AxiosInstance['post']
const axiosPut = apiClient.put.bind(apiClient) as AxiosInstance['put']
const axiosPatch = apiClient.patch.bind(apiClient) as AxiosInstance['patch']
const axiosDelete = apiClient.delete.bind(apiClient) as AxiosInstance['delete']

apiClient.get = <T>(url: string, config?: AxiosRequestConfig): Promise<T> =>
  data(axiosGet<T>(url, config))

apiClient.post = <T>(
  url: string,
  body?: unknown,
  config?: AxiosRequestConfig
): Promise<T> => data(axiosPost<T>(url, body, config))

apiClient.put = <T>(
  url: string,
  body?: unknown,
  config?: AxiosRequestConfig
): Promise<T> => data(axiosPut<T>(url, body, config))

apiClient.patch = <T>(
  url: string,
  body?: unknown,
  config?: AxiosRequestConfig
): Promise<T> => data(axiosPatch<T>(url, body, config))

apiClient.delete = <T>(
  url: string,
  config?: AxiosRequestConfig
): Promise<T> => data(axiosDelete<T>(url, config))
