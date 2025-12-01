/**
 * Minimal Nova Node SDK (no external deps)
 * Usage (Node 18+ recommended since global fetch is used):
 *
 * const Nova = require('./index.js');
 * const client = new Nova({ baseUrl: 'http://127.0.0.1:8000' });
 */
const { URL } = require("url");

class NovaClient {
  constructor({ apiKey = null, baseUrl = "http://127.0.0.1:8000" } = {}) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.apiKey = apiKey;
    this.headers = { "Content-Type": "application/json" };
    if (apiKey) this.headers["X-AOS-Key"] = apiKey;
  }

  _url(path) {
    return `${this.baseUrl}${path}`;
  }

  async createAgent(name) {
    const res = await fetch(this._url("/agents"), {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error(`createAgent failed ${res.status}`);
    const data = await res.json();
    return data.agent_id || data.id || null;
  }

  async postGoal(agentId, goal, forceSkill = null) {
    const payload = { goal };
    if (forceSkill) payload.force_skill = forceSkill;
    const res = await fetch(this._url(`/agents/${agentId}/goals`), {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`postGoal failed ${res.status}`);
    const data = await res.json();
    return data.run_id || (data.plan && data.plan.plan_id) || null;
  }

  async pollRun(agentId, runId, timeout = 30000, interval = 500) {
    const end = Date.now() + timeout;
    while (Date.now() < end) {
      const res = await fetch(this._url(`/agents/${agentId}/runs/${runId}`), { headers: this.headers });
      if (res.ok) {
        const data = await res.json();
        const status = data.status || (data.run && data.run.status) || (data.plan && data.plan.status);
        if (status && (status === "succeeded" || status === "failed")) return data;
      }
      await new Promise((r) => setTimeout(r, interval));
    }
    throw new Error(`pollRun timeout for ${runId}`);
  }

  async recall(agentId, query, k = 5) {
    const url = new URL(this._url(`/agents/${agentId}/recall`));
    url.searchParams.set("q", query);
    url.searchParams.set("k", String(k));
    const res = await fetch(url.toString(), { headers: this.headers });
    if (!res.ok) throw new Error(`recall failed ${res.status}`);
    return res.json();
  }
}

module.exports = { NovaClient };
