# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is "yarns" - an AI-driven autonomous agent system built around a central agent called "yarno". The project implements an attention-free paradigm (无注意力范式) where AI agents work asynchronously to analyze user context and execute tasks with minimal human intervention.

## Development Commands

```bash
# Run the main yarno agent
python3 yarno/agent.py
```

## Architecture

The system follows a core workflow:
1. yarno analyzes user needs hourly and schedules agent execution
2. Agents execute tasks and return results to yarno  
3. yarno determines if human intervention is needed
4. If not needed, yarno continues agent interactions until satisfied with results
5. All progress is recorded in the notebook system

### Key Components

- **yarno agent** (`yarno/agent.py`): Main autonomous agent with context analysis, authorization system, and agent coordination
- **Context system** (`yarno/context.md`): Detailed user context including personal info, tech preferences (Next.js, Tailwind, FastAPI, Go, Supabase), and potential needs
- **Notebook system** (`yarno/notebook.md`): Records agent thoughts, actions, and interaction history

### Planned Architecture (MVP)

- **Agent marketplace**: Simple JSON-based registry for agent discovery
- **A2A protocol**: Asynchronous communication between yarno and external agents
- **Payment system**: Shared ledger for resource allocation between agents
- **Authentication**: Agent-to-agent handshake mechanism replacing traditional user login systems

The end goal is "yarns" - an AI consulting marketplace where users can deploy their agents to provide services to others.