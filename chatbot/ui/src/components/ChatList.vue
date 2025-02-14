<template>
  <div>
    <ul class="space-y-2">
  <li v-for="chat in chatSessions" :key="chat.unique_key" class="px-2">
    <div class="flex w-full gap-2">
      <button
        @click="selectChat(chat.unique_key)"
        :class="['flex-1 max-w-[250px] px-3 py-2 rounded-lg flex items-center text-white bg-default-700 focus:ring-4 focus:ring-default-200 dark:focus:ring-default-900 ', selectedChatId == chat.unique_key ? 'bg-default-500' : 'hover:bg-default-800']"
      >
        <div class="text-left truncate w-full">
          {{ chat.title }}
        </div>
      </button>
      <button
        @click.stop="handleDelete(chat.unique_key)"
        class="z-10  text-gray-400 dark:text-gray-500 hover:text-gray-500 dark:hover:text-gray-400"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="size-6"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
          />
        </svg>
      </button>
    </div>
    <DeleteConfirmationModal
      :is-open="showDeleteModal"
      @confirm="confirmDelete"
      @cancel="showDeleteModal = false"
    />
  </li>
</ul>
  </div>
</template>

<script setup lang="ts">
import { chatService } from "@/services/ChatService";
import type { ChatSession } from "@/types/chat";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import DeleteConfirmationModal from "@/components/DeleteConfirmationModal.vue";

import { watch } from 'vue'
let isLoading = false;
const router = useRouter();
const selectedChatId = ref<string | null>(null);

const props = defineProps<{
  refreshTrigger: number
}>()

watch(() => props.refreshTrigger, async () => {
  await fetchChatSessions()
})

const selectChat = (id: string): void => {
  selectedChatId.value = id;
  router.push({ path: `/chat/${id}` });
};

const showDeleteModal = ref(false)
const chatToDelete = ref<string | null>(null)

const handleDelete = (chatKey: string) => {
  chatToDelete.value = chatKey
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (chatToDelete.value) {

    console.log("Deleting chat with ID:", chatToDelete.value);
    await chatService.deleteChatSession(chatToDelete.value);
    await fetchChatSessions();
    showDeleteModal.value = false
    if (selectedChatId.value === chatToDelete.value) {
      selectedChatId.value = null
      router.push({ path: `/chat` });
    }
  }
}

const chatSessions = ref<ChatSession[]>([]);
const fetchChatSessions = async () => {
  isLoading = true;
  const newChatSessions = await chatService.getChatSessions();
  console.info(newChatSessions)
  chatSessions.value.splice(0, chatSessions.value.length, ...newChatSessions);
  isLoading = false;
};

onMounted(() => {
  fetchChatSessions();
});
</script>
