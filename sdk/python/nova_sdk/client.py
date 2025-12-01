"""
Minimal Nova Python SDK
Usage:
    from nova_sdk import NovaClient
    client = NovaClient(api_key="...", base_url="http://127.0.0.1:8000")
    agent_id = client.create_agent("test-agent")
    run_id = client.post_goal(agent_id, "ping")
    status = client.poll_run(agent_id, run_id, timeout=10)
"""
from typing import Optional, Dict, Any
import requests
import time
import uuid


class NovaClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"X-AOS-Key": api_key})

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def create_agent(self, name: str) -> str:
        payload = {"name": name}
        r = self.session.post(self._url("/agents"), json=payload)
        r.raise_for_status()
        data = r.json()
        # Expecting agent_id in response or id
        return data.get("agent_id") or data.get("id") or str(uuid.uuid4())

    def post_goal(self, agent_id: str, goal: str, force_skill: Optional[str] = None) -> str:
        payload = {"goal": goal}
        if force_skill:
            payload["force_skill"] = force_skill
        r = self.session.post(self._url(f"/agents/{agent_id}/goals"), json=payload)
        r.raise_for_status()
        data = r.json()
        # try to extract run id from response provenance/plan if present
        run_id = data.get("run_id") or data.get("run", {}).get("id") or data.get("plan", {}).get("plan_id")
        return run_id

    def poll_run(self, agent_id: str, run_id: str, timeout: int = 30, interval: float = 0.5) -> Dict[str, Any]:
        end = time.time() + timeout
        while time.time() < end:
            r = self.session.get(self._url(f"/agents/{agent_id}/runs/{run_id}"))
            if r.status_code == 200:
                data = r.json()
                status = data.get("status") or data.get("run", {}).get("status") or data.get("plan", {}).get("status")
                if status and status in ("succeeded", "failed"):
                    return data
            time.sleep(interval)
        raise TimeoutError(f"Run {run_id} did not complete in {timeout}s")

    def recall(self, agent_id: str, query: str, k: int = 5) -> Dict[str, Any]:
        params = {"q": query, "k": k}
        r = self.session.get(self._url(f"/agents/{agent_id}/recall"), params=params)
        r.raise_for_status()
        return r.json()
