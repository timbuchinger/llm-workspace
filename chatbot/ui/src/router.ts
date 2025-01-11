import { createRouter, createWebHistory } from "vue-router";
import HomePage from "./components/HomePage.vue";
import LoginForm from "./components/LoginForm.vue";
import MainComponent from "./components/MainComponent.vue";
import ChatSessionComponent from "./components/ChatSessionComponent.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      component: HomePage,
    },

    {
      path: "/chat",
      name: "Chat",
      component: MainComponent,
      children: [
        {
          path: ":chatId",
          component: ChatSessionComponent,
        },
      ],
    },
    { path: "/login", name: "Login", component: LoginForm },
  ],
});
