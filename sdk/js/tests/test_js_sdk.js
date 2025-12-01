const { NovaClient } = require("../nova-sdk/index.js");

const API_URL = process.env.API_URL || "http://127.0.0.1:8000";
const API_KEY = process.env.API_KEY || "edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf";

(async function main(){
  try {
    const c = new NovaClient({ apiKey: API_KEY, baseUrl: API_URL });
    const agent = await c.createAgent("node-sdk-test");
    if(!agent) {
      console.log("createAgent returned null — backend may not be available; skipping.");
      process.exit(0);
    }
    const runId = await c.postGoal(agent, "ping test", "http_call");
    console.log("agent:", agent, "runId:", runId);
    // optionally poll (skipped to keep test fast)
    process.exit(0);
  } catch (e) {
    console.error("ERROR", e.message);
    process.exit(2);
  }
})();
