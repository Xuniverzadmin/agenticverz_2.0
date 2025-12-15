# AOS Beta Testing Instructions

**Version:** 1.0
**Beta Phase:** Private Beta
**Last Updated:** 2025-12-13

---

## Welcome Beta Testers!

Thank you for participating in the AOS (Agentic Operating System) beta program. Your feedback is crucial for improving the platform before public release.

---

## Getting Started

### 1. Access Credentials
You should have received:
- API Key: `aos_beta_XXXX...`
- Console URL: `https://agenticverz.com/console`

If you haven't received these, contact support@agenticverz.com

### 2. First Login
1. Navigate to `https://agenticverz.com/console/login`
2. Enter your API key
3. Click "Connect"
4. You'll be redirected to the Dashboard

### 3. Verify Connection
Check the status bar at the bottom - it should show "Connected" in green.

---

## Beta Testing Focus Areas

### Week 1-2: Core Functionality
- [ ] Agent creation and management
- [ ] Job simulation and execution
- [ ] Budget tracking
- [ ] Skill invocation

### Week 3-4: Edge Cases
- [ ] Rate limiting behavior
- [ ] Error handling
- [ ] Recovery mechanisms
- [ ] Performance under load

### Ongoing: Usability
- [ ] UI/UX feedback
- [ ] Documentation clarity
- [ ] Feature requests

---

## Test Scenarios to Complete

### Scenario A: Basic Agent Workflow
**Objective:** Create an agent and run a simple job

1. Go to Agents page
2. Click "Create Agent"
3. Name: `test-agent-001`
4. Type: `worker`
5. Click Create
6. Verify agent appears in list

### Scenario B: Job Simulation
**Objective:** Simulate a multi-step job

1. Go to Jobs page
2. Click "Simulate Job"
3. Add steps:
   - Step 1: `http_call` - URL: `https://api.github.com/users/octocat`
   - Step 2: `json_transform` - JQ: `.login`
   - Step 3: `llm_invoke` - Prompt: `Describe this user`
4. Set budget: 100 cents
5. Click "Simulate"
6. Review cost estimate and feasibility

### Scenario C: Budget Enforcement
**Objective:** Verify budget limits work

1. Create job with 10 LLM steps
2. Set budget to 10 cents (below cost)
3. Simulate - should show "Budget Insufficient"
4. Increase budget to 100 cents
5. Simulate - should show "Feasible"

### Scenario D: Skill Discovery
**Objective:** Explore available skills

1. Go to Dashboard
2. Check "Available Skills" section
3. Note which skills are available
4. Try each skill type in a simulation

---

## Reporting Issues

### Bug Reports
Use this template:

```
**Title:** [BUG] Brief description

**Environment:**
- Browser: Chrome/Firefox/Safari version
- OS: Windows/Mac/Linux
- Time: UTC timestamp

**Steps to Reproduce:**
1. Step one
2. Step two
3. Step three

**Expected Result:**
What should have happened

**Actual Result:**
What actually happened

**Screenshots:**
Attach if applicable

**Console Errors:**
Open DevTools (F12) → Console tab → Copy errors
```

### Feature Requests
Use this template:

```
**Title:** [FEATURE] Brief description

**Problem Statement:**
What problem does this solve?

**Proposed Solution:**
How should it work?

**Alternatives Considered:**
Other approaches you thought of

**Priority:**
- Critical (blocking work)
- High (significant improvement)
- Medium (nice to have)
- Low (minor enhancement)
```

### Where to Report
- GitHub Issues: https://github.com/agenticverz/aos/issues
- Email: beta@agenticverz.com
- Discord: #beta-feedback channel

---

## Known Limitations (Beta)

| Limitation | Description | ETA |
|------------|-------------|-----|
| Auth Provider | Using stub auth, real OAuth pending | M8 |
| Skill Count | 7 skills available, more coming | M11 |
| Rate Limits | Conservative limits during beta | M12 |
| Recovery UI | Limited recovery visualization | M10 |

---

## API Quick Reference

### Authentication
All API requests require the `X-API-Key` header:
```bash
curl -H "X-API-Key: your-api-key" https://agenticverz.com/api/v1/health
```

### Key Endpoints
```
GET  /api/v1/runtime/capabilities   - List skills and limits
POST /api/v1/runtime/simulate       - Simulate execution plan
GET  /api/v1/agents                 - List agents
POST /api/v1/agents                 - Create agent
GET  /api/v1/jobs                   - List jobs
POST /api/v1/runs                   - Execute a run
```

### Example: Create Agent via API
```bash
curl -X POST https://agenticverz.com/api/v1/agents \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-agent", "type": "worker"}'
```

---

## Feedback Schedule

| Date | Feedback Type | How to Submit |
|------|---------------|---------------|
| Weekly | Bug reports | GitHub Issues |
| Bi-weekly | Feature requests | Discord/Email |
| Monthly | Survey | Email link |
| End of Beta | Final review | Scheduled call |

---

## Support Channels

- **Documentation:** https://docs.agenticverz.com
- **Discord:** https://discord.gg/agenticverz (invite in welcome email)
- **Email:** beta@agenticverz.com
- **Office Hours:** Fridays 2pm UTC (Zoom link in Discord)

---

## Legal & Privacy

- Beta data may be reset without notice
- Do not store production/sensitive data
- Feedback may be used to improve the product
- See full terms at https://agenticverz.com/beta-terms

---

## Thank You!

Your participation in this beta helps shape the future of agentic systems. We value every piece of feedback, big or small.

Questions? Reach out anytime at beta@agenticverz.com
