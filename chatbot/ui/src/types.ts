export interface LoginResponse {
  key: string;
}

export interface RegisterResponse {
  key: string;
}

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

export interface AuthError {
  non_field_errors?: string[];
  [key: string]: string[] | undefined;
}
