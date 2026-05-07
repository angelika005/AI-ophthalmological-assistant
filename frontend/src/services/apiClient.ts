/**
 * API Client с автоматическим обновлением токенов и retry логикой
 * 
 * Функционал:
 * - Перехватывает 401 ошибки
 * - Автоматически обновляет access token через refresh token
 * - Повторняет исходный запрос с новым токеном
 * - Детектирует проблемы с refresh token (требует нового login)
 */

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  skipRetry?: boolean;  // Флаг чтобы избежать бесконечного цикла retry
}

class ApiClient {
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (token: string) => void;
    reject: (error: Error) => void;
  }> = [];

  /**
   * Процессирует очередь неудавшихся запросов
   */
  private processQueue(error: Error | null, token: string | null = null) {
    this.failedQueue.forEach(prom => {
      if (error) {
        prom.reject(error);
      } else if (token) {
        prom.resolve(token);
      }
    });

    this.failedQueue = [];
  }

  /**
   * Обновляет access token через refresh token
   */
  private async refreshAccessToken(): Promise<string> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/token/refresh`, {
        method: 'POST',
        credentials: 'include', // Отправляет refresh_token cookie
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // Если refresh failed, нужно перенаправить на login
        if (response.status === 401) {
          this.handleAuthError();
        }
        throw new Error('Failed to refresh token');
      }

      const data = await response.json();
      
      // Access token установлен в cookie автоматически
      // Но сохраним его для последующего использования если нужно
      localStorage.setItem('access_token_time', Date.now().toString());
      
      return data.access_token;
    } catch (error) {
      this.handleAuthError();
      throw error;
    }
  }

  /**
   * Обработка ошибок аутентификации
   */
  private handleAuthError() {
    // Очищаем user из localStorage
    localStorage.removeItem('user');
    localStorage.removeItem('access_token_time');
    
    // Перенаправляем на login (dispatch event)
    window.dispatchEvent(new CustomEvent('auth-error', {
      detail: { message: 'Session expired, please login again' }
    }));
  }

  /**
   * Основной fetch метод с перехватом и retry
   */
  async request(
    url: string,
    options: RequestOptions = {}
  ): Promise<Response> {
    // Не добавляем skipRetry флаг в реальный запрос
    const { skipRetry, ...fetchOptions } = options;

    try {
      let response = await fetch(`${API_BASE_URL}${url}`, {
        ...fetchOptions,
        credentials: 'include', // Всегда отправляем cookies
      });

      // Если получили 401 и это не retry
      if (response.status === 401 && !skipRetry) {
        // Если уже идет refresh, добавляем запрос в очередь
        if (this.isRefreshing) {
          return new Promise((resolve, reject) => {
            this.failedQueue.push({
              resolve: (token: string) => {
                // Повторяем запрос с новым токеном
                resolve(this.request(url, { ...options, skipRetry: true }));
              },
              reject,
            });
          });
        }

        // Начинаем refresh процесс
        this.isRefreshing = true;

        try {
          await this.refreshAccessToken();
          this.processQueue(null);
          
          // Повторяем исходный запрос
          return fetch(`${API_BASE_URL}${url}`, {
            ...fetchOptions,
            credentials: 'include',
          });
        } catch (error) {
          this.processQueue(error as Error);
          throw error;
        } finally {
          this.isRefreshing = false;
        }
      }

      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * GET запрос
   */
  async get(url: string, options?: RequestOptions): Promise<Response> {
    return this.request(url, {
      ...options,
      method: 'GET',
    });
  }

  /**
   * POST запрос
   */
  async post(
    url: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<Response> {
    return this.request(url, {
      ...options,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * PUT запрос
   */
  async put(
    url: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<Response> {
    return this.request(url, {
      ...options,
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * PATCH запрос
   */
  async patch(
    url: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<Response> {
    return this.request(url, {
      ...options,
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * POST запрос с формой (для файлов)
   */
  async postFormData(
    url: string,
    formData: FormData,
    options?: RequestOptions
  ): Promise<Response> {
    return this.request(url, {
      ...options,
      method: 'POST',
      // НЕ устанавливаем Content-Type, браузер установит правильно с boundary
      headers: {
        ...(options?.headers || {}),
      },
      body: formData,
    });
  }

  /**
   * DELETE запрос
   */
  async delete(url: string, options?: RequestOptions): Promise<Response> {
    return this.request(url, {
      ...options,
      method: 'DELETE',
    });
  }
}

// Экспортируем singleton экземпляр
export const apiClient = new ApiClient();
