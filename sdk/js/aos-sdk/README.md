# AOS SDK for JavaScript/TypeScript

The official JavaScript/TypeScript SDK for AOS (Agentic Operating System) - the most predictable, reliable, deterministic SDK for building machine-native agents.

## Installation

```bash
npm install @agenticverz/aos-sdk
# or
yarn add @agenticverz/aos-sdk
# or
pnpm add @agenticverz/aos-sdk
```

## Quick Start

```typescript
import { AOSClient } from '@agenticverz/aos-sdk';

// Initialize client
const client = new AOSClient({
  apiKey: 'your-api-key',
  baseUrl: 'http://localhost:8000'
});

// Check available capabilities
const caps = await client.getCapabilities();
console.log(`Budget remaining: ${caps.budget_remaining_cents}c`);
console.log(`Available skills: ${caps.skills_available.join(', ')}`);

// Simulate before executing
const result = await client.simulate([
  { skill: 'http_call', params: { url: 'https://api.example.com' } },
  { skill: 'llm_invoke', params: { prompt: 'Summarize the response' } }
]);

if (result.feasible) {
  console.log(`Plan is feasible! Estimated cost: ${result.estimated_cost_cents}c`);
} else {
  console.log(`Plan not feasible: ${result.reason}`);
}
```

## Machine-Native Features

AOS is designed for agents to operate efficiently, not humans to babysit:

- **Queryable execution context** - Not log parsing
- **Capability contracts** - Not just tool lists
- **Structured outcomes** - Never throws exceptions
- **Failure as data** - Navigable, not opaque
- **Pre-execution simulation** - Know before you run

## API Reference

### AOSClient

```typescript
const client = new AOSClient({
  apiKey: '...',           // Optional, uses AOS_API_KEY env var
  baseUrl: 'http://...',   // Default: http://127.0.0.1:8000
  timeout: 30000           // Request timeout in milliseconds
});
```

### Machine-Native APIs

```typescript
// Simulate a plan before execution
const result = await client.simulate(plan, budgetCents);

// Query runtime state
const budget = await client.query('remaining_budget_cents');
const attempts = await client.query('what_did_i_try_already', {}, undefined, runId);

// List and describe skills
const { skills } = await client.listSkills();
const skill = await client.describeSkill('http_call');

// Get capabilities
const caps = await client.getCapabilities();
```

### Agent Workflow APIs

```typescript
// Create agent and execute goal
const agentId = await client.createAgent('my-agent');
const runId = await client.postGoal(agentId, 'Check the weather in London');
const result = await client.pollRun(agentId, runId);

// Memory recall
const memories = await client.recall(agentId, 'weather queries', 5);
```

## TypeScript Support

This SDK is written in TypeScript and includes full type definitions:

```typescript
import type {
  AOSClientOptions,
  PlanStep,
  SimulateResult,
  Capabilities,
  Skill,
  SkillDescriptor,
  Run
} from '@agenticverz/aos-sdk';
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AOS_API_KEY` | API key for authentication | (none) |
| `AOS_BASE_URL` | Base URL for AOS server | `http://127.0.0.1:8000` |

## Requirements

- Node.js 18+ (uses native fetch)
- For older Node.js versions, you'll need a fetch polyfill

## License

MIT License - see LICENSE file for details.
