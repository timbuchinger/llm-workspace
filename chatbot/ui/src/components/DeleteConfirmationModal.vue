<template>
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 bg-gray-500 bg-opacity-35 flex items-center justify-center z-20">
      <div class="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
        <h3 class="text-lg font-medium mb-4">Confirm Delete</h3>
        <p class="text-gray-600 mb-6">Are you sure you want to delete this chat? This action cannot be undone.</p>
        <div class="flex justify-end gap-3">
          <button
            @click="onCancel"
            class="px-4 py-2 border rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            @click="onConfirm"
            class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  isOpen: boolean
  onConfirm: () => void
  onCancel: () => void
}

defineProps<Props>()

</script>

