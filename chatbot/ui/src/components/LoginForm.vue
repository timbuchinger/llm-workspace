<template>
  <div class="flex items-center justify-center flex-1 bg-gray-100">
    <form
      @submit.prevent="handleSubmit"
      class="w-full max-w-md p-6 bg-white rounded-lg shadow-md space-y-6"
    >
      <div class="form-group">
        <label for="username" class="block font-medium text-gray-700">
          Username:
        </label>
        <input
          type="text"
          id="username"
          v-model="formData.username"
          required
          placeholder="user1@somedomain.org"
        class="w-full p-2 border rounded mt-4 border-gray-300"
        >
      </div>

      <div class="form-group">
        <label for="password" class="block font-medium text-gray-700">
          Password:
        </label>
        <input
          type="password"
          id="password"
          v-model="formData.password"
          required
          placeholder="*************"
        class="w-full p-2 border rounded mt-4 border-gray-300"

        >
      </div>

      <div v-if="error" class="text-red-600 text-sm">
        {{ error }}
      </div>

      <button
        type="submit"
        :disabled="isLoading"
        class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-default-600 hover:bg-default-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-default-500"
      >
        <span v-if="isLoading">Loading...</span>
        <span v-else>Login</span>
      </button>
    </form>
  </div>
</template>


<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { authService } from '@/services/AuthService';
import type { LoginFormData } from '@/types/auth';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const error = ref<string | null>(null);
const isLoading = ref(false);
const authStore = useAuthStore();

const formData = reactive<LoginFormData>({
  username: '',
  password: ''
});

const handleSubmit = async () => {
  error.value = null;
  isLoading.value = true;

  try {
    await authService.login({
      username: formData.username,
      password: formData.password
    });
    authStore.setUser({ id: 1, name: 'John Doe' }); // Set user data
    router.push('/chat');
  } catch (e) {
    if (e instanceof Error) {
      try {
        const errorData = JSON.parse(e.message);
        error.value = errorData.non_field_errors?.[0] || 'Login failed';
      } catch {
        error.value = e.message;
      }
    } else {
      error.value = 'An unexpected error occurred';
    }
  } finally {
    isLoading.value = false;
  }
};
</script>
