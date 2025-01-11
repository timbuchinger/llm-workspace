<template>
  <ul>
    <li class="text-red-900" v-for="message in messages" :key="message.id">
      <div v-if="message.sender == Sender.User" class="flex flex-wrap my-2">
        <div class="hidden xl:block flex-1" />
        <div
          class="max-w-4xl w-full flex-grow text-stone-200 dark:text-stone-700 rounded-lg border bg-stone-700 dark:bg-stone-300 border-stone-800 dark:border-stone-500 flex flex-col items-center"
        >

          <div
            class="mb-2 w-full p-2 flex-grow bg-stone-400 rounded-tr-lg rounded-tl-lg"
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
                d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"
              />
            </svg>
          </div>

          <div class="w-full flex-grow pb-2 pl-2 rounded-br-lg rounded-bl-lg">
            <p>{{ message.content }}</p>
          </div>
        </div>
      </div>

      <div v-if="message.sender == Sender.Chatbot" class="flex flex-wrap my-2">
        <div
          class="max-w-4xl w-full flex-grow text-stone-200 dark:text-stone-700 rounded-lg border bg-stone-700 dark:bg-stone-300 border-stone-800 dark:border-stone-500 flex flex-col items-center"
        >

          <div
            class="mb-2 w-full p-2 flex-grow bg-stone-400 rounded-tr-lg rounded-tl-lg"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
              class="w-6 h-6"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M2.25 15a4.5 4.5 0 0 0 4.5 4.5H18a3.75 3.75 0 0 0 1.332-7.257 3 3 0 0 0-3.758-3.848 5.25 5.25 0 0 0-10.233 2.33A4.502 4.502 0 0 0 2.25 15Z"
              />
            </svg>
          </div>

          <div class="w-full flex-grow pb-2 pl-2 rounded-br-lg rounded-bl-lg">
            <p>{{ message.content }}</p>
          </div>
        </div>
      </div>
    </li>
    <li v-if="thinking">
      <div class="w-full flex-grow flex pt-2"><div
          class="h-4 w-4 bg-stone-400 rounded-full animate-bounce [animation-delay:-0.3s]"
        ></div>
        <div
          class="h-4 w-4 mx-1 bg-stone-400 rounded-full animate-bounce [animation-delay:-0.15s]"
        ></div>
        <div class="h-4 w-4 bg-stone-400 rounded-full animate-bounce"></div></div>
    </li>

  </ul>
</template>

<script setup lang="ts">
import type { ChatMessage } from "@/types/chat";
import { Sender } from "@/types/chat";

defineProps<{
  messages?: ChatMessage[];
  thinking?: boolean;
}>();
</script>
