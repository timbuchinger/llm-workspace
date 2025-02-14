import { ref, type Ref } from 'vue'
import { chatService } from '@/services/ChatService'
import type { ChatMessage } from '@/types/chat'

export function useChat(chatSessionId: string) {
  const messages: Ref<ChatMessage[]> = ref([])
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  const fetchMessages = async () => {
    isLoading.value = true
    error.value = null

    try {
      console.info('Fetching chat messages...')
      messages.value = await chatService.getChatMessages(chatSessionId)
      console.info(messages.value)
      console.info('Chat messages fetched successfully!')
    } catch (e) {
      error.value = e as Error
      console.error('Failed to fetch chat messages:', e)
    } finally {
      isLoading.value = false
    }
  }

  return {
    messages,
    isLoading,
    error,
    fetchMessages
  }
}
