import { ref, computed } from 'vue';
import { authService } from '../services/AuthService';

export function useAuth() {
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const isAuthenticated = computed(() => authService.isAuthenticated());

  const checkAuth = async () => {
    isLoading.value = true;
    error.value = null;

    try {
      return await authService.checkAuthStatus();
    } catch (e) {
      error.value = 'Authentication check failed';
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const logout = () => {
    authService.logout();
  };

  return {
    isAuthenticated,
    isLoading,
    error,
    checkAuth,
    logout
  };
}
