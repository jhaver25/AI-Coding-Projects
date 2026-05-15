# PM Status Reporting Assistant — Python CLI Tool

A command-line tool for engineering program managers that transforms raw status meeting notes (bullet points, call notes, scribbles) into polished, executive-ready weekly engineering status reports using the Anthropic Claude API.

---

## Overview

After weekly project status calls, a PM typically has a pile of raw bullet points — team accomplishments, blockers, risks, dependencies — and needs to turn them into a structured report that engineering VPs and C-suite can read and act on in minutes. This tool automates that transformation.

You provide the notes (typed interactively or from a Markdown file). The tool sends them to Claude with a detailed system prompt that encodes the report structure, style guidelines, and output format. Claude returns a fully formatted weekly status report in Markdown, ready to paste into Confluence, Notion, Google Docs, or an email.

**Key capabilities:**
- Supports any number of teams or projects in a single report run
- Two input modes: interactive (type at the terminal) or file-based (`.md` or `.txt`)
- Streams the report to the terminal as it generates (no waiting for the full response)
- Optionally saves the report to a `.md` file
- Uses prompt caching to reduce API costs on repeated runs
- Supports week offsets to generate reports labeled for past or future weeks

---

## Setup

**Requirements:** Python 3.10+

```bash
# Install the Anthropic SDK
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Usage

### Interactive mode (no file needed)

```bash
python3 pm-status-report-assistant.py
```

The tool prompts you for each team name, then for that team's bullet points. Type `done` when you've entered all teams.

### File-based mode

```bash
python3 pm-status-report-assistant.py -i Meeting-Notes_Demo-Text.md
```

Only `.md` and `.txt` files are supported. A `Meeting-Notes_Template.md` starter file is included in the project directory — copy it, fill in your teams, and pass it with `-i`.

The input file uses `## Team Name` as section headers, one per team:

```markdown
## Checkout & Payments
- Shipped guest checkout to 100% of users
- Performance regression in confirmation page — fix in review

## Platform
- Completed Postgres 16 migration with zero downtime
- Blocked on InfoSec review for S3 bucket policy
```

A file with no `##` headers is treated as a single team's notes under a "General" section.

### Saving output to a file

```bash
python3 pm-status-report-assistant.py -i notes.md -o reports/week-42.md
```

### Other flags

| Flag | Description |
|---|---|
| `-i FILE` / `--input FILE` | Read notes from this file |
| `-o FILE` / `--output FILE` | Save the generated report to this file |
| `-w N` / `--week N` | Week offset: `0` = current week (default), `-1` = last week, `1` = next week |
| `--no-stream` | Wait for the full response before printing (disables streaming) |

---

## File Structure

```
pm-status-report-assistant.py   # Main CLI script
requirements.txt                # Python dependencies (anthropic)
Meeting-Notes_Template.md       # Starter template for multi-team notes input
Meeting-Notes_Demo-Text.md      # Sample multi-team input file
Status-Report_Example-1.md      # Example generated report output
AI-Prompt-Engineering-Guide.md  # Prompt engineering reference for the system prompt
Claude-Code-Review-Notes.md     # Code review notes and change log
Feature-Roadmap.md              # Planned improvements and future feature ideas
```

---

## Function Reference

### `SYSTEM_PROMPT` (module-level constant)

A large, detailed string (~2,500+ tokens) that defines Claude's persona, the required report structure, writing style standards, status indicator logic, and edge-case handling rules. It is deliberately written to exceed Sonnet 4.6's 2,048-token prompt caching minimum so it gets cached after the first call.

The system prompt instructs Claude to produce a report with these sections every time:
1. **Executive Summary** — 2–4 sentence portfolio health overview
2. **Team & Project Status** — one table per team with Accomplishments, In Progress, Blockers/Risks, and Next Week
3. **Cross-Team Dependencies & Escalations** — inter-team blockers and leadership flags
4. **Milestones & Schedule** — any deadline or milestone updates
5. **Action Items & Decisions Needed** — checklist-formatted follow-ups

---

### `get_week_range(offset: int = 0) -> tuple[date, date]`

Returns the Monday and Friday `date` objects for the target week. `offset=0` is the current week, `offset=-1` is last week, etc. Uses Python's `date.weekday()` to anchor to Monday regardless of what day the tool is run.

---

### `format_week_header(monday: date, friday: date) -> str`

Formats the week range as a human-readable string for use in the report heading and output file header. Handles the month-boundary case cleanly:

- Same month → `"Week of May 12–16, 2025"`
- Cross-month → `"Week of May 26–May 30, 2025"`

---

### `read_notes_from_file(filepath: str) -> dict[str, str]`

Reads a `.md` or `.txt` file and returns a `{team_name: notes_text}` dictionary.

**Parsing logic:**
- If any line **begins with** `## `, the file is parsed as multi-team format — each such header becomes a team name, and the lines beneath it are collected as that team's notes. Headers appearing mid-line (e.g. in a bullet point) do not trigger multi-team parsing.
- If no lines begin with `## `, the entire file is treated as one team's notes under the key `"General"`.
- Whitespace-only team sections are skipped with a warning rather than passed to the API.

Exits with an error message if the file does not exist, is empty or contains only whitespace, or uses an unsupported file type. Only `.md` and `.txt` files are accepted.

---

### `collect_notes_interactively() -> dict[str, str]`

Runs the interactive terminal loop for users who prefer to type notes directly rather than prepare a file. Prompts for a team name, then collects bullet points until the user either types `end` on its own line or presses Enter twice. Loops to collect additional teams until the user types `done` at the team name prompt.

---

### `build_user_message(teams: dict[str, str], week_header: str) -> str`

Assembles the user-turn message sent to the Claude API. Formats the collected notes as a Markdown document with a top-level heading for the week and `## Team Name` subsections, then appends an instruction to follow the system prompt's format guidelines. This message is the variable/non-cached portion of each API request.

---

### `generate_report(teams, week_header, client, use_stream=True) -> str`

The core function that calls the Claude API and returns the generated report text.

Constructs the `system` parameter as a list with a single content block — the full `SYSTEM_PROMPT` text with `"cache_control": {"type": "ephemeral"}` attached, which tells the API to cache this block.

**Streaming path (default):** Uses `client.messages.stream()` as a context manager, printing each text chunk to the terminal as it arrives via `stream.text_stream`. Calls `stream.get_final_message()` at the end to retrieve the complete response object (needed for usage stats). Returns the accumulated full text.

**Non-streaming path (`--no-stream`):** Uses `client.messages.create()` for a single blocking call, prints the full response, then returns the text.

After either path, calls `_print_cache_stats()` to display token usage.

API errors are caught and surfaced as clear, actionable messages rather than raw Python exceptions. Handled cases include authentication failures (bad API key), rate limits, connection issues, and requests rejected due to oversized input.

---

### `_print_cache_stats(usage: object) -> None`

Reads the `usage` object from the API response and prints a summary of prompt cache activity and token counts. Reports:

- **Cache HIT** when `cache_read_input_tokens > 0` — the system prompt was served from cache
- **Cache MISS** when `cache_creation_input_tokens > 0` — the system prompt was freshly cached (first run or cache expired)
- Total uncached input tokens and output tokens for the request

---

### `save_report(report: str, output_path: str, week_header: str) -> None`

Writes the generated report to a `.md` file. Prepends a top-level `# Engineering Weekly Status Report` heading and the week range in italics. Creates any intermediate directories in the output path if they don't already exist.

---

### `main() -> None`

The CLI entry point. Responsibilities:

1. Defines and parses command-line arguments using `argparse`
2. Validates that `ANTHROPIC_API_KEY` is set in the environment
3. Computes the target week range via `get_week_range()` and `format_week_header()`
4. Loads notes from a file (`read_notes_from_file`) or collects them interactively (`collect_notes_interactively`) depending on whether `--input` was provided
5. Initializes the `anthropic.Anthropic()` client (which automatically reads `ANTHROPIC_API_KEY`)
6. Calls `generate_report()` to produce the report
7. Optionally calls `save_report()` if `--output` was specified

---

## API Calls

The tool makes a single Anthropic API call per run via the `generate_report()` function.

### Endpoint

`POST https://api.anthropic.com/v1/messages`

Called through the official `anthropic` Python SDK as either `client.messages.stream()` (default) or `client.messages.create()` (with `--no-stream`).

### Model

`claude-sonnet-4-6` — Anthropic's best combination of speed and intelligence. Well-suited for structured document generation tasks like status reports.

### Request Structure

```python
{
    "model": "claude-sonnet-4-6",
    "max_tokens": 4096,
    "system": [
        {
            "type": "text",
            "text": "<SYSTEM_PROMPT>",
            "cache_control": {"type": "ephemeral"}   # enables prompt caching
        }
    ],
    "messages": [
        {
            "role": "user",
            "content": "<formatted meeting notes + instructions>"
        }
    ]
}
```

### Prompt Caching

The `cache_control: {"type": "ephemeral"}` marker on the system prompt block tells the Anthropic API to cache that prefix after the first request. On all subsequent calls made within the **5-minute cache TTL window**, the system prompt is served from cache instead of being re-processed.

**Why this matters:** The system prompt is ~2,500 tokens — the largest single cost component of each request. Caching it reduces the cost of that portion by approximately 90% on cache hits.

Sonnet 4.6 requires a minimum of **2,048 tokens** for a prefix to be eligible for caching. The `SYSTEM_PROMPT` was intentionally written to exceed this threshold. The tool prints a cache HIT or MISS message after each run so you can confirm caching is working.

---

## Expected Costs

All pricing is based on Anthropic's published rates for `claude-sonnet-4-6` as of May 2025:

| Token type | Price |
|---|---|
| Input (uncached) | $3.00 per 1M tokens |
| Input (cache write, first call) | $3.75 per 1M tokens (1.25× base) |
| Input (cache read, subsequent calls) | $0.30 per 1M tokens (~0.1× base) |
| Output | $15.00 per 1M tokens |

### Typical token counts per run

| Component | Approximate tokens |
|---|---|
| System prompt (SYSTEM_PROMPT constant) | ~2,500 |
| User message (notes for 3–5 teams) | ~400–800 |
| Generated report output | ~800–1,500 |

### Cost per run

**First run of the day (cache miss):**
- System prompt written to cache: 2,500 tokens × $3.75/1M ≈ **$0.009**
- Notes input (uncached): ~600 tokens × $3.00/1M ≈ **$0.002**
- Output: ~1,200 tokens × $15.00/1M ≈ **$0.018**
- **Total first run: ~$0.029 (~3 cents)**

**Subsequent runs within 5 minutes (cache hit):**
- System prompt served from cache: 2,500 tokens × $0.30/1M ≈ **$0.001**
- Notes input (uncached): ~600 tokens × $3.00/1M ≈ **$0.002**
- Output: ~1,200 tokens × $15.00/1M ≈ **$0.018**
- **Total subsequent run: ~$0.021 (~2 cents)**

### Weekly and monthly estimates

| Usage pattern | Estimated cost |
|---|---|
| 1 report per week | ~$0.03/week → **~$0.13/month** |
| 3 reports per week (e.g., multiple PM coverage) | ~$0.09/week → **~$0.39/month** |
| 5 reports per week (daily use) | ~$0.15/week → **~$0.65/month** |
| 20 reports per month with back-to-back reruns (cache hits) | ~**$0.50/month** |

### Notes on cost variability

- **More teams = more input tokens = slightly higher cost.** Each additional team's notes adds roughly 100–300 tokens to the user message ($0.00030–$0.00090 extra per run). The output grows proportionally.
- **Cache hits require runs within 5 minutes of each other.** If you run the tool once in the morning and once in the afternoon, each run will be a cache miss. For most weekly workflows (one run per report), this distinction is minor because the cost difference between a cache hit and miss is only ~$0.008.
- **Longer or more detailed notes increase output length.** A report covering 8 teams with detailed notes could produce 2,000–3,000 output tokens, pushing the per-run cost to ~$0.05.
- **At any realistic usage level, this tool costs well under $1/month.**

---

## Example Output Structure

```markdown
# Engineering Weekly Status Report
_Week of May 12–16, 2025_

## Executive Summary
Engineering shipped three customer-facing features this week and completed a zero-downtime database migration...

## Team & Project Status

**Checkout & Payments** — 🟡 At Risk

| | |
|---|---|
| **Accomplishments** | Guest checkout shipped to 100% of users; international promo code bug fixed |
| **In Progress** | Apple Pay UI component; P99 regression investigation |
| **Blockers / Risks** | **P99 latency on confirmation page rose from 200ms to 1.2s** — fix in review |
| **Next Week** | Deploy Apple Pay; resolve P99 regression; begin Stripe webhook retry planning |

...

## Cross-Team Dependencies & Escalations
- **[Platform → InfoSec]**: S3 bucket policy security review has been pending for 2 weeks. Blocking document storage feature launch.
- **[Data & Analytics → Payments]**: Revenue attribution model blocked on final schema from Payments team.

## Action Items & Decisions Needed
- [ ] **InfoSec**: Respond to Platform team's S3 bucket policy review request
- [ ] **Payments**: Share finalized revenue attribution schema with Data team
```
