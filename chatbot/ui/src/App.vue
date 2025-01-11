<template>
  <div id="app" class="flex flex-col h-screen">
    <NotificationComponent
      :notifications="notificationStore.notifications"
      @dismiss="notificationStore.dismissNotification"
    />
    <Navbar />
    <router-view></router-view>
  </div>
</template>

<script setup lang="ts">
import Navbar from "./components/Navbar.vue";
import NotificationComponent from "@/components/NotificationComponent.vue";
import { useNotificationStore } from "@/stores/notifications";

const notificationStore = useNotificationStore();

</script>
