import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from langchain.chains import RetrievalQA
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaEmbeddings, OllamaLLM

from .models import ChatMessage, ChatSession


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        chat_id = self.scope["url_route"]["kwargs"].get("chat_id")
        self.current_chat = await self.get_chat_by_id(chat_id)

        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)

        message_id = data["message_id"]
        if not self.current_chat:
            raise ("No active chat session.")

        current_message = await self.get_chat_message(message_id=message_id)

        response, sources = await self.get_chatbot_response(current_message.content)

        response = await self.save_message(self.current_chat, "Chatbot", response)

        await self.send(json.dumps({"message_id": response.id}))

    @database_sync_to_async
    def get_chat_by_id(self, chat_id):
        """Fetch a ChatSession by its ID."""
        try:
            return ChatSession.objects.get(unique_key=chat_id, user=self.user)
        except ChatSession.DoesNotExist:
            return None

    @database_sync_to_async
    def get_chat_messages(self, chat_session):
        """Retrieve messages for a given ChatSession."""
        return list(
            chat_session.messages.order_by("timestamp").values("sender", "content")
        )

    @database_sync_to_async
    def get_chat_message(self, message_id):
        """Retrieve messages for a given ChatSession."""
        return ChatMessage.objects.get(id=message_id)

    @database_sync_to_async
    def save_message(self, chat_session, sender, content):
        """Save a message to the database."""
        return ChatMessage.objects.create(
            chat_session=chat_session, sender=sender, content=content
        )

    async def get_chatbot_response(self, query):
        """Generate a response from the chatbot using the RAG pipeline."""

        embeddings = OllamaEmbeddings(
            base_url="https://{OLLAMA_ENDPOINT}", model="nomic-embed-text"
        )
        vector_store = Chroma(
            persist_directory="./vector_store", embedding_function=embeddings
        )
        retriever = vector_store.as_retriever(
            search_type="similarity", search_kwargs={"k": 5}
        )

        llm = OllamaLLM(model="llama3", base_url="https://{OLLAMA_ENDPOINT}")
        prompt = PromptTemplate(
            template=(
                "You are an assistant in a conversational setting. Use the following "
                "context to answer the user's questions. Maintain the context of prior interactions:\n\n"
                "{context}\n\nCurrent Question: {question}\n\nAnswer:"
            ),
            input_variables=["context", "question"],
        )
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},
        )

        context = []
        for msg in await self.get_chat_messages(self.current_chat):  # .messages.all():
            context.append(f"{msg['sender']}: {msg['content']}")
        context = "\n".join(context)

        result = qa_chain.invoke({"context": context, "query": query})

        answer = result["result"]
        sources = [
            doc.metadata.get("source", "Unknown") for doc in result["source_documents"]
        ]
        return answer, sources
