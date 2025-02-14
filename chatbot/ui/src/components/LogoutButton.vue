<template>
  <button
    @click="handleLogout"
    class="rounded-md px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
  >
    Logout
  </button>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const tokenKey = 'token'; // Make sure this matches your token key
const router = useRouter();
const authStore = useAuthStore();

const handleLogout = (): void => {
  // Remove token from localStorage
  localStorage.removeItem(tokenKey);

  // Clear any auth state in Vuex if you're using it
  // this.$store.commit('auth/clearAuth');

  // Optional: Clear other auth-related data
  clearAuthData();
  authStore.clearUser(); // Clear user data
  // authStore.logout()

  // Redirect to login page
  router.push('/login');
};

const clearAuthData = (): void => {
  // Clear any additional auth-related data
  sessionStorage.clear();

  // Clear any cookies if you're using them
  document.cookie.split(';').forEach(cookie => {
    document.cookie = cookie
      .replace(/^ +/, '')
      .replace(/=.*/, `=;expires=${new Date().toUTCString()};path=/`);
  });
};
</script>
