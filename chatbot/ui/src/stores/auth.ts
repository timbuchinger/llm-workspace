import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('userState') || 'null'),
  }),
  actions: {
    setUser(user: object | null) {
      this.user = user;
      localStorage.setItem('userState', JSON.stringify(user));
    },
    clearUser() {
      this.user = null;
      localStorage.removeItem('userState');
    },
  },
  getters: {
    isAuthenticated: (state) => !!state.user,
  },
});