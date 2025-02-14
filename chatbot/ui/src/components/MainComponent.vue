<template>
  <div
    class="w-full bg-gray-200 shadow md:mt-0 xl:p-0 dark:bg-gray-800 flex-1 h-full"
  >
    <div class="grid grid-cols-[300px_auto] mx-auto h-full flex-1">
      <!-- First Column -->
      <div class="bg-gray-100 dark:bg-gray-800 flex-1">
        <div class="mx-auto px-3 py-5">
          <button
            id="new-chat-btn"
            @click="handleCreateChatSession"
            :disabled="isLoading"
            class="inline-flex items-center my-1 px-4 py-2 text-sm font-medium text-center text-white bg-default-700 rounded-lg focus:ring-4 focus:ring-default-200 dark:focus:ring-default-900 hover:bg-default-800"
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
                d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10"
              />
            </svg>
            &nbsp;&nbsp;&nbsp;{{ isLoading ? "Creating..." : "New Chat" }}
          </button>
          <div
            v-if="error"
            class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4"
          >
            {{ error }}
          </div>
        </div>
        <div class="px-4">
          <h3 class="text-gray-700 dark:text-gray-200 font-bold pb-3">
            Your Chats
          </h3>
        </div>

        <ChatList :refreshTrigger="refreshCount" />

        <div class="mx-auto px-3 py-1"></div>

        <div class="flex-grow border-t border-gray-400"></div>
        <div class="px-5 py-5 text-gray-700 dark:text-gray-200">
          [Other Content]
        </div>
      </div>

      <!-- Second Column (Needs to fill the height of the first div) -->
      <div class="flex flex-col w-full h-full bg-gray-800 dark:bg-gray-100">
        <ChatSessionComponent :selectedId="selectedId" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import ChatSessionComponent from "./ChatSessionComponent.vue";
import { chatService } from "@/services/ChatService";
import ChatList from "@/components/ChatList.vue";
import type { ChatSession } from "@/types/chat";
import { useNotificationStore } from "@/stores/notifications";


const notificationStore = useNotificationStore();
const router = useRouter();
const isLoading = ref(false);
const error = ref<string | null>(null);
const selectedId = ref<string | null>(null);
const chatSessions = ref<ChatSession[]>([]);

const handleCreateChatSession = async () => {
  isLoading.value = true;

  try {
    const chatSession = await chatService.createChatSession();
    const newChatSessions = await chatService.getChatSessions();
    chatSessions.value.splice(0, chatSessions.value.length, ...newChatSessions);
    triggerRefresh();
    router.push("/chat/" + chatSession.unique_key);
  } finally {
    isLoading.value = false;
  }
};

const refreshCount = ref(0)
const triggerRefresh = () => {
  refreshCount.value++
}


</script>

<style scoped>
.size-6 {
  width: 1.5rem;
  height: 1.5rem;
}
</style>
