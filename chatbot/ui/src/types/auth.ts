export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  email: string;
  password1: string;
  password2: string;
}

export interface LoginResponse {
  key: string;
  access: string;
  user?: UserProfile;
}

export interface RegisterResponse {
  key: string;
  user?: UserProfile;
}

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  date_joined?: string;
  last_login?: string;
}

export interface LoginFormData {
  username: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterFormData {
  username: string;
  email: string;
  password1: string;
  password2: string;
}

export interface AuthError {
  non_field_errors?: string[];
  username?: string[];
  email?: string[];
  password?: string[];
  password1?: string[];
  password2?: string[];
  detail?: string;
  code?: string;
  [key: string]: string[] | string | undefined;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: UserProfile | null;
  token: string | null;
  loading: boolean;
  error: AuthError | null;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  uid: string;
  token: string;
  new_password1: string;
  new_password2: string;
}

export interface PasswordChangeRequest {
  old_password: string;
  new_password1: string;
  new_password2: string;
}

// API response types
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

// Enum for authentication status
export enum AuthStatus {
  IDLE = 'idle',
  LOADING = 'loading',
  AUTHENTICATED = 'authenticated',
  UNAUTHENTICATED = 'unauthenticated',
  ERROR = 'error'
}

// Custom error class for authentication errors
export class AuthenticationError extends Error {
  public readonly errors: AuthError;
  public readonly status?: number;

  constructor(message: string, errors: AuthError, status?: number) {
    super(message);
    this.name = 'AuthenticationError';
    this.errors = errors;
    this.status = status;
  }
}

// Form validation types
export interface ValidationRules {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  email?: boolean;
  password?: boolean;
  match?: string;
}

export interface FormField<T = string> {
  value: T;
  error?: string[];
  rules?: ValidationRules;
  dirty?: boolean;
  touched?: boolean;
}

export interface FormState {
  [key: string]: FormField;
}

// Social auth types
export interface SocialAuthProvider {
  id: string;
  name: string;
  icon: string;
  authUrl: string;
}

export interface SocialAuthResponse extends LoginResponse {
  provider: string;
  social_token: string;
}

// Token types
export interface TokenPair {
  access: string;
  refresh: string;
}

export interface RefreshTokenRequest {
  refresh: string;
}