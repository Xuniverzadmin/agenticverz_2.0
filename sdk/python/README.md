# Nova Python SDK

Install (dev):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e sdk/python
pip install requests pytest
```

Example:

```py
from nova_sdk import NovaClient
c = NovaClient(base_url="http://127.0.0.1:8000")
agent_id = c.create_agent("sdk-test")
run = c.post_goal(agent_id, "ping", force_skill="http_call")
print("run:", run)
# optionally poll
# c.poll_run(agent_id, run, timeout=10)
```
