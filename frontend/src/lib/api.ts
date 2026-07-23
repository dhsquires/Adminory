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
