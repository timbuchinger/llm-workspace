export interface ChatSession {
  unique_key: string;
  user: number;
  title: string;
  created_at: Date;
  messages: ChatMessage[];
}

export interface ChatMessage {
  id: string
  sender: Sender
  content: string
  created_at: Date
}
export enum Sender {
  User = 'User',
  Chatbot = 'Chatbot'
}
