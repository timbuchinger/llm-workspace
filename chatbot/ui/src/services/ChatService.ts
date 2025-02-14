import axios from 'axios'
import type { ChatMessage, ChatSession } from '@/types/chat'
import authService from './AuthService';
import { useNotificationStore } from "@/stores/notifications";
import { router } from '@/router';

export class ChatService {
  async getChatMessage(message_id: string): Promise<ChatMessage> {
    try {
      const token = authService.getToken();
      if (!token) {
        throw new Error("No authentication token found");
      }
      const response = await fetch(
        `http://localhost:8000/api/chat-message/${message_id}/`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.status === 401) {
        throw new Error("Authentication token expired or invalid");
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const message = await response.json();

      return message;
    } catch (err) {
      const error = err as Error;
      this.handleError(error);
      throw error;
    }
  }
  private readonly baseUrl = '/api/chat-messages'

  async deleteChatSession(chatSessionId: string): Promise<void> {
    const notificationStore = useNotificationStore();
    try {
      const token = authService.getToken();
      if (!token) {
        throw new Error("No authentication token found");
      }
      const response = await axios.delete(
        `http://localhost:8000/api/chat-session/${chatSessionId}/`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.status === 401) {
        throw new Error("Authentication token expired or invalid");
      }

      router.push('/chat');
      notificationStore.addNotification({ message: 'Chat session deleted', type: 'success' })
    } catch (err) {
      const error = err as Error;
      this.handleError(error);
    }
  }

  async createChatSession(): Promise<ChatSession> {
    try {
      const token = authService.getToken();
      if (!token) {
        throw new Error("No authentication token found");
      }
      const response = await fetch(
        `http://localhost:8000/api/chat-session/`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.status === 401) {
        throw new Error("Authentication token expired or invalid");
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const sessions = await response.json();
      console.info(sessions);
      return sessions;
    } catch (err) {
      const error = err as Error;
      this.handleError(error);
      throw error;
    }
  }

  async getChatSession(chatSessionId: string): Promise<ChatSession> {
    const notificationStore = useNotificationStore();
    try {
      const token = authService.getToken();
      if (!token) {
        throw new Error("No authentication token found");
      }
      const response = await fetch(
        `http://localhost:8000/api/chat-session/${chatSessionId}/`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.status === 401) {
        throw new Error("Authentication token expired or invalid");
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const sessions = await response.json();

      return sessions;
    } catch (err) {
      const error = err as Error;
      this.handleError(error);
      throw error;
    }
  }

  async getChatSessions(): Promise<ChatSession[]> {
    const notificationStore = useNotificationStore();
    try {
      const token = authService.getToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await fetch("http://localhost:8000/api/chat-session/", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.status === 401) {
        throw new Error("Authentication token expired or invalid");
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const sessions = await response.json();
      console.info("Fetched chat sessions:", sessions);
      return sessions;
    } catch (err) {
      const error = err as Error;
      this.handleError(error);
      throw error;
    }
  };

  async sendMessage(chatSessionId: string, message: string): Promise<ChatMessage> {
    try {
      const token = authService.getToken();
      if (!token) {
        throw new Error("No authentication token found");
      }
      const response = await fetch(
        `http://localhost:8000/api/chat-message/`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ chat_session_id: chatSessionId, content: message }),
        }
      );

      if (response.status === 401) {
        throw new Error("Authentication token expired or invalid");
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const newMessage = await response.json();

      return newMessage;
    } catch (err) {
      const error = err as Error;
      this.handleError(error);
      throw error;
    }
  }

  handleError(error: Error) {
    const notificationStore = useNotificationStore();
    console.error("Error:", error);
    notificationStore.addNotification({ message: error.message, type: 'error' })

    if (error.message.toLowerCase().includes("authentication token expired or invalid")) {
      router.push('/login');
    }
    throw error;
  }
}

export const chatService = new ChatService()
