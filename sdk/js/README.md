# Nova Node SDK

Node 18+ (recommended) with global fetch.

Example:

```js
const { NovaClient } = require("./index.js");
(async () => {
  const c = new NovaClient({ baseUrl: "http://127.0.0.1:8000" });
  const agent = await c.createAgent("node-sdk-agent");
  const runId = await c.postGoal(agent, "ping", "http_call");
  console.log("runId", runId);
})();
```
