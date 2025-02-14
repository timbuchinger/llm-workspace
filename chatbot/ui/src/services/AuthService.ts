import axios, {AxiosError} from 'axios';

import type { AxiosInstance } from 'axios';
import type {
  LoginResponse,
  RegisterResponse,
  LoginCredentials,
  RegisterCredentials,
  AuthError
} from '../types/auth.ts';

class AuthService {
  private api: AxiosInstance;
  private tokenKey = 'token';

  constructor(baseURL: string = 'http://localhost:8000') {
    this.api = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });


    const token = this.getToken();
  }

  private setAuthHeader(token: string): void {
    this.api.defaults.headers.common['Authorization'] = `Token ${token}`;
  }

  private removeAuthHeader(): void {
    delete this.api.defaults.headers.common['Authorization'];
  }

  public async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await this.api.post<LoginResponse>('/dj-rest-auth/login/', credentials);
      const token = response.data.access;



      localStorage.setItem(this.tokenKey, token);

      console.info(token);
      return response.data;
    } catch (error) {
      if (error instanceof AxiosError && error.response?.data) {
        throw new Error(JSON.stringify(error.response.data));
      }
      throw error;
    }
  }


  public logout(): void {
    localStorage.removeItem(this.tokenKey);
    this.removeAuthHeader();
  }

  public getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  public isAuthenticated(): boolean {
    return this.getToken() !== null;
  }


  public getAuthenticatedApi(): AxiosInstance {
    return this.api;
  }


  public async checkAuthStatus(): Promise<boolean> {
    try {
      const token = this.getToken();
      if (!token) return false;

      await this.api.get('/auth/user/');
      return true;
    } catch (error) {
      this.logout();
      return false;
    }
  }
}


export const authService = new AuthService();
export default authService;


export { AuthService };