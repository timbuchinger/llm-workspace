<template>
  <div class="flex flex-col flex-1 bg-gray-800 dark:bg-gray-100">

    <div class="flex w-full overflow-y-auto">

      <div class="hidden xl:block flex-1">

        <p class="p-4">&nbsp;</p>
      </div>


      <div class="w-full xl:w-[800px] 2xl:w-[1000px] text-white">
        <div class="flex-1 p-4" style="max-height: calc(100vh - 64px)">
          <div
      v-if="chat"
      class="text-stone-300 dark:text-stone-700 text-center px-4 py-2 rounded"
    >
      Title: {{ chat?.title }}
    </div>
          <div
            v-if="!chat"
            class="flex flex-col items-center justify-center min-h-[400px] px-4"
          >
            <div
              class="max-w-md w-full bg-white rounded-xl shadow-lg p-8 transform transition-all duration-300 hover:scale-105"
              :class="{ 'shadow-xl': true }"
            >
              <h2 class="text-2xl font-bold text-gray-800 mb-4 text-center">
                Ready to start a conversation?
              </h2>

              <p class="text-gray-600 mb-6 text-center">
                Begin chatting with our AI assistant for instant help and
                engaging discussions.
              </p>

              <div class="flex justify-center">
                <button
                  class="inline-flex items-center px-6 py-3 rounded-lg bg-indigo-600 text-white font-medium transition-colors duration-200 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <span class="mr-2">Start Chatting</span>
                  <svg
                    class="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <ChatMessageComponent :messages="messages" :thinking="thinking" />


          <input
            v-model="query"
            @keyup.enter="sendMessage"
            placeholder="Ask a question..."
            class="w-full p-2 border rounded mt-4 text-gray-200 dark:text-gray-700 border-gray-300"
          />
          <div class="text-center text-sm p-2 text-gray-300 dark:text-gray-600">
            Stay safe out there.
          </div>
        </div>
      </div>


      <div class="hidden xl:block flex-1">

        <p class="p-4">&nbsp;</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { useRoute } from "vue-router";
import ChatMessageComponent from "./ChatMessageComponent.vue";
import { Sender, type ChatMessage, type ChatSession } from "@/types/chat";
import { chatService } from "@/services/ChatService";

const isLoading = ref<boolean>(false);
const error = ref<string | null>(null);
const route = useRoute();
const chat = ref<ChatSession | null>(null);
const messages = ref<ChatMessage[]>([]);
let thinking = ref<boolean>(false);
const query = ref<string>("");

const loadChatData = async (chatId: string) => {
  console.info("Loading chat data for chat ID:", chatId);
  try {
    thinking.value = false
    chat.value = await chatService.getChatSession(chatId);
    messages.value = chat.value.messages.map((message) => ({
      id: message.id,
      sender: message.sender,
      content: message.content,
      created_at: new Date(message.created_at),
    }));
    socket = new WebSocket("ws://localhost:8000/ws/chat/" + chatId + "/");
    socket.onmessage = function (event) {
      const data = JSON.parse(event.data);
      chatService.getChatMessage(data.message_id).then((message) => {
        messages.value.push({
          id: message.id,
          sender: Sender.Chatbot,
          content: message.content,
          created_at: new Date(message.created_at),
        });
        thinking.value = false
      });


    };
  } catch (e) {
    if (e instanceof Error) {
      try {
        const errorData = JSON.parse(e.message);
        error.value = errorData.non_field_errors?.[0] || "Login failed";
      } catch {
        error.value = e.message;
      }
    } else {
      error.value = "An unexpected error occurred";
    }
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  if (route.params.chatId) {
    loadChatData(route.params.chatId as string);
  } else {
    chat.value = null
  }
});

watch(
  () => route.params.chatId,
  (newChatId) => {
    if (newChatId) loadChatData(newChatId as string);
  },
  { immediate: true }
);

let socket: WebSocket;

const sendMessage = async () => {
  if (query.value) {
    thinking.value = true
    if(!chat.value) {
      throw new Error("Chat session not initialized");
    }
    const newMessage = await chatService.sendMessage(chat.value.unique_key, query.value);
    console.info("New message:", newMessage);
    messages.value.push({
      id: newMessage.id,
      sender: Sender.User,
      content: query.value,
      created_at: newMessage.created_at,
    });
    socket.send(JSON.stringify({ message_id: newMessage.id }));
    console.log("Sending message:", query.value);
    query.value = "";
    // thinking.value = false
  }
};
</script>
