# PitchBot 🤖📊

**An autonomous AI agent that analyzes startup pitches and generates comprehensive investment research reports.**

Upload a pitch deck, video, audio, or code—PitchBot extracts key attributes, then deploys an agentic research workflow to synthesize market analysis from 1,000+ web sources. What used to take 5+ hours now takes under 10 minutes.

## What It Does

1. **Multi-modal ingestion** – Accepts PDFs, videos, audio, and code
2. **Attribute extraction** – Uses Llama-4 to identify key startup attributes (market, competitors, team, traction)
3. **Autonomous research** – GPT-4 + Brave Search API agent crawls the web for relevant market data
4. **Report generation** – Synthesizes everything into a structured investment analysis

## Tech Stack

- **LLMs:** Llama-4 (analysis), GPT-4o (research agent), Whisper (transcription)
- **Search:** Brave Search API
- **Backend:** FastAPI, Python
- **Frontend:** React.js

## Architecture
```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Input      │ ──▶ │  Extraction  │ ──▶ │  Research Agent │
│  (PDF/Video)│     │  (Llama-4)   │     │  (GPT-4 + Brave)│
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                  │
                                                  ▼
                                         ┌───────────────┐
                                         │ Final Report  │
                                         └───────────────┘
```
