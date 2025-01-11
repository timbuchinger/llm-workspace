#!/usr/bin/env node

import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createServer } from "./memory.js";

async function main() {
  console.log("Configuring transport");
  const transport = new StdioServerTransport();
  console.log("Starting server");
  const { server, cleanup } = createServer();
  console.log("Connecting server");
  await server.connect(transport);
  console.log("Server connected.");
  // Cleanup on exit
  process.on("SIGINT", async () => {
    console.log("Received SIGINT");
    await cleanup();
    await server.close();
    process.exit(0);
  });
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
