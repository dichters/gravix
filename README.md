# gravix
A lightweight, local-first engine for AI agent retrieval and memory
---

## Quick Start

```bash
# Create a gravix_conf.yaml in your project root, then:
gravix init

# Or specify a custom config file:
gravix init -c /path/to/config.yaml

# Or use environment variables only:
export GRAVIX_WORK_DIR=.gravix
export GRAVIX_LITE_BASE_URL=https://api.example.com/v1
export GRAVIX_LITE_SK=sk-xxxx
export GRAVIX_FULL_BASE_URL=https://api.example.com/v1
export GRAVIX_FULL_SK=sk-xxxx
gravix init
```

## Configuration

Config values are resolved with priority: **environment variable > config file**. Missing values cause an error.

| Config Key | Environment Variable | Description |
|---|---|---|
| `work_dir` | `GRAVIX_WORK_DIR` | Workspace directory (relative to pwd or absolute) |
| `lite_base_url` | `GRAVIX_LITE_BASE_URL` | Lite LLM API base URL (OpenAI-compatible) |
| `lite_sk` | `GRAVIX_LITE_SK` | Lite LLM API key |
| `full_base_url` | `GRAVIX_FULL_BASE_URL` | Full LLM API base URL (OpenAI-compatible) |
| `full_sk` | `GRAVIX_FULL_SK` | Full LLM API key |

Default config file: `gravix_conf.yaml` in the current working directory.

## What `gravix init` Creates

```
{{work_dir}}/
├── graph.lbug      # Ladybug graph database (nodes + relations)
├── abstract.db     # SQLite database with FTS5 full-text search
└── raw/            # Raw document storage
```
