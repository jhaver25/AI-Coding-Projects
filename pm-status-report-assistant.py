#!/usr/bin/env python3
"""
Weekly Status Report Generator
Transforms engineering project meeting notes into formatted executive status reports.
"""

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path
import anthropic

# Comprehensive system prompt — designed to exceed the 2048-token caching minimum for Sonnet 4.6.
# This stable prompt is cached, so repeated runs only pay ~0.1x for this portion.
SYSTEM_PROMPT = """You are an expert engineering program manager assistant with over 15 years of experience supporting software engineering organizations at high-growth technology companies. You specialize in transforming raw, unstructured meeting notes and status call bullet points into polished, executive-ready weekly status reports that communicate clearly to engineering leaders, VPs, and C-suite stakeholders.

Your deep expertise spans customer-facing application teams, internal tooling and platform teams, data engineering, infrastructure, and security engineering. You understand the full software development lifecycle, agile methodologies, and the operational realities of running multiple concurrent engineering workstreams.

## Core Responsibilities

When given meeting notes or bullet points from project status calls, your job is to:
1. Synthesize raw information into clear, structured narrative
2. Identify and surface the most important signals — achievements, risks, blockers, and dependencies
3. Assign appropriate status indicators based on the context of the notes
4. Produce a report that a senior leader can read and fully understand in under 3 minutes
5. Preserve technical accuracy while translating jargon into business-relevant language where appropriate

## Required Report Structure

Always produce a report with the following sections, in this order:

### Engineering Weekly Status Report — [Week]

#### Executive Summary
Write 2–4 sentences that give a senior leader an immediate pulse on the engineering organization this week. Highlight the single most important achievement, the most critical risk or blocker (if any), and the overall health of the portfolio. This section must stand alone — a reader who only reads the Executive Summary should understand what matters most.

#### Team & Project Status

For each team or project in the notes, create a subsection with this structure:

**[Team / Project Name]** — [Status Indicator]

| | |
|---|---|
| **Accomplishments** | What was completed or shipped this week |
| **In Progress** | Active work underway |
| **Blockers / Risks** | Anything impeding progress or creating schedule/scope risk |
| **Next Week** | Planned priorities for the coming week |

Status Indicators:
- 🟢 **On Track** — Work is progressing as planned; no significant risks to timeline or scope
- 🟡 **At Risk** — One or more issues that could impact the timeline, scope, or quality if not addressed soon
- 🔴 **Blocked** — Work has stopped or will stop due to an unresolved dependency, resource gap, or external factor

#### Cross-Team Dependencies & Escalations
List any situations where one team is waiting on another, or where a risk/blocker requires leadership attention or a decision from outside the team. If nothing significant was noted, write "No cross-team escalations this week."

#### Milestones & Schedule
Summarize any milestone progress, deadline changes, or schedule impacts mentioned in the notes. If no milestones were discussed, write "No milestone updates this week."

#### Action Items & Decisions Needed
List specific action items or decisions that require follow-up, with owners if mentioned. Format each as:
- [ ] **[Owner or Team]**: [Action or Decision]

If no explicit action items were called out, write "No open action items identified."

---

## Writing Style and Quality Standards

**Tone**: Professional, factual, and appropriately direct. This report goes to engineering VPs and potentially to C-suite. Avoid casual language, filler phrases ("it's worth noting that…"), and unnecessary hedging.

**Conciseness**: Every sentence must earn its place. Cut padding. Use bullet points within table cells for multiple items rather than writing long paragraphs.

**Voice**: Active voice throughout. "Team shipped the authentication overhaul" — not "The authentication overhaul was shipped by the team."

**Quantify outcomes**: When notes mention measurable results, preserve them. "Reduced P99 latency from 850ms to 340ms" is far more useful than "improved performance."

**Risk visibility**: Blockers and risks must be impossible to miss. Bold them in the table. If multiple teams are blocked on the same dependency, call it out explicitly in the Cross-Team section.

**Inferring status**: When notes are sparse or ambiguous, use the following heuristics:
- Ongoing work with no blockers mentioned → 🟢 On Track
- Notes mention a concern, delay, or uncertainty → 🟡 At Risk
- Explicit mention of being blocked, waiting on something, or stopped → 🔴 Blocked
- Never invent facts not present in the notes

**Completeness**: If a team's notes are very brief, still generate all required fields. Use "Not mentioned in notes" as a placeholder rather than omitting a row. This signals to the reader that the field wasn't discussed, not that it doesn't exist.

**Markdown formatting**: Use clean Markdown throughout — this report will be copy-pasted into Confluence, Notion, Google Docs, or emailed as a formatted document. Use headers, bold, tables, and checkboxes consistently.

---

## Common Scenarios and How to Handle Them

**On-call / incident notes**: If notes reference an incident, page, or outage, always surface it prominently. Include it in the team's blockers/risks row AND call it out in the Executive Summary if it was significant.

**Launch / release notes**: Treat shipped features, releases, or major deployments as accomplishments. If a launch happened this week and had no issues, that's an 🟢 signal.

**Vague notes**: Sometimes notes say things like "still working on it" or "made progress." Treat these as in-progress work with 🟢 status unless other signals suggest otherwise. Do not fabricate specifics.

**Missing sections in notes**: If notes only cover accomplishments and no next-week plans are mentioned, write "Not discussed in status call" for that row.

**Multiple workstreams per team**: If a single team is working on multiple independent projects, use sub-bullets within each table cell rather than creating separate team entries.

**Dependency callouts**: Pay special attention to phrases like "waiting on," "blocked by," "need approval from," "depends on," or "need a decision about." These always belong in both the team's Blockers row and the Cross-Team section.

---

Your output should be copy-paste ready. Do not include any preamble like "Here is the report:" or "Sure! Below is your status report." Start directly with the report heading."""


def get_week_range(offset: int = 0) -> tuple[date, date]:
    today = date.today()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    friday = monday + timedelta(days=4)
    return monday, friday


def format_week_header(monday: date, friday: date) -> str:
    if monday.month == friday.month:
        return f"Week of {monday.strftime('%B %d')}–{friday.strftime('%d, %Y')}"
    return f"Week of {monday.strftime('%B %d')}–{friday.strftime('%B %d, %Y')}"


def read_notes_from_file(filepath: str) -> dict[str, str]:
    """
    Parse notes file. Supports two formats:
      Multi-team:  sections starting with ## Team Name
      Single-team: plain bullet points (team name defaults to "General")
    """
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    supported_extensions = {".md", ".txt"}
    if path.suffix.lower() not in supported_extensions:
        print(f"Error: Unsupported file type '{path.suffix}'. Supported formats: .md, .txt", file=sys.stderr)
        print("Tip: Copy your notes into a .txt or .md file and try again.", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8").strip()
    if not content:
        print(f"Error: File is empty or contains only whitespace: {filepath}", file=sys.stderr)
        sys.exit(1)

    teams: dict[str, str] = {}

    if any(line.startswith("## ") for line in content.splitlines()):
        current_team: str | None = None
        current_lines: list[str] = []
        for line in content.splitlines():
            if line.startswith("## "):
                notes = "\n".join(current_lines).strip()
                if current_team and notes:
                    teams[current_team] = notes
                elif current_team:
                    print(f"  ! No notes found for '{current_team}' — skipping.", file=sys.stderr)
                current_team = line[3:].strip()
                current_lines = []
            else:
                if current_team is not None:
                    current_lines.append(line)
        if current_team and current_lines:
            teams[current_team] = "\n".join(current_lines).strip()
    else:
        teams["General"] = content

    return teams


def collect_notes_interactively() -> dict[str, str]:
    """Interactive mode: prompt for team names and bullet points."""
    teams: dict[str, str] = {}
    print("\n=== Weekly Status Report Generator ===")
    print("Enter notes for each team or project.")
    print("Type 'done' at the team name prompt when finished.\n")

    while True:
        team_name = input("Team / Project name (or 'done' to generate): ").strip()
        if team_name.lower() == "done":
            if not teams:
                print("Please enter notes for at least one team first.\n")
                continue
            break
        if not team_name:
            continue

        print(f"\nPaste or type bullet points for {team_name}.")
        print("Press Enter twice (or type 'end' on its own line) when done:\n")

        lines: list[str] = []
        blank_streak = 0
        while True:
            line = input()
            if line.strip().lower() == "end":
                break
            if line.strip() == "":
                blank_streak += 1
                if blank_streak >= 2:
                    break
            else:
                blank_streak = 0
                lines.append(line)

        notes = "\n".join(lines).strip()
        if notes:
            teams[team_name] = notes
            print(f"  ✓ Captured notes for {team_name}\n")
        else:
            print(f"  ! No notes entered for {team_name} — skipping.\n")

    return teams


def build_user_message(teams: dict[str, str], week_header: str) -> str:
    sections = [f"# Status Call Notes — {week_header}\n"]
    for team, notes in teams.items():
        sections.append(f"## {team}\n{notes}")
    notes_block = "\n\n".join(sections)

    return (
        f"Please generate the weekly engineering status report from these notes.\n\n"
        f"{notes_block}\n\n"
        f"Follow the report format and style guidelines from your instructions exactly."
    )


def generate_report(
    teams: dict[str, str],
    week_header: str,
    client: anthropic.Anthropic,
    use_stream: bool = True,
) -> str:
    user_message = build_user_message(teams, week_header)

    # System prompt uses cache_control so it is cached after the first call.
    # Sonnet 4.6 requires a minimum of 2048 tokens to cache; the SYSTEM_PROMPT
    # above is written to comfortably exceed that threshold.
    system = [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    print("\n⏳ Generating report...\n")
    print("─" * 60)

    try:
        if use_stream:
            report_text = ""
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                for chunk in stream.text_stream:
                    print(chunk, end="", flush=True)
                    report_text += chunk
                final = stream.get_final_message()

            print("\n" + "─" * 60)
            _print_cache_stats(final.usage)
            return report_text
        else:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": user_message}],
            )
            text = next(b.text for b in response.content if b.type == "text")
            print(text)
            print("─" * 60)
            _print_cache_stats(response.usage)
            return text
    except anthropic.AuthenticationError:
        print("Error: Invalid API key. Check your ANTHROPIC_API_KEY.", file=sys.stderr)
        sys.exit(1)
    except anthropic.RateLimitError:
        print("Error: Rate limit reached. Wait a moment and try again.", file=sys.stderr)
        sys.exit(1)
    except anthropic.APIConnectionError:
        print("Error: Could not connect to the Anthropic API. Check your internet connection.", file=sys.stderr)
        sys.exit(1)
    except anthropic.BadRequestError as e:
        print(f"Error: Request rejected — your notes may be too long to process. ({e})", file=sys.stderr)
        sys.exit(1)
    except anthropic.APIStatusError as e:
        print(f"Error: API returned an unexpected error ({e.status_code}): {e.message}", file=sys.stderr)
        sys.exit(1)


def _print_cache_stats(usage: object) -> None:
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    input_tokens = getattr(usage, "input_tokens", 0) or 0
    output_tokens = getattr(usage, "output_tokens", 0) or 0

    if cache_read:
        print(f"\n💾 Prompt cache HIT  — {cache_read:,} tokens read from cache (saved ~90% on those tokens)")
    elif cache_write:
        print(f"\n💾 Prompt cache MISS — {cache_write:,} tokens written to cache (subsequent calls will be cheaper)")

    print(f"   Tokens: {input_tokens:,} input (uncached) + {output_tokens:,} output")


def save_report(report: str, output_path: str, week_header: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"# Engineering Weekly Status Report\n_{week_header}_\n\n"
    path.write_text(header + report, encoding="utf-8")
    print(f"\n📄 Saved to: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pm-status-report-assistant",
        description="Generate weekly engineering status reports from meeting notes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  Interactive mode (type notes at the prompts):
    python pm-status-report-assistant.py

  From a file (single team):
    python status_report.py -i notes.txt

  From a file (multi-team Markdown sections):
    python status_report.py -i weekly_notes.md

  Save output to a file:
    python status_report.py -i notes.md -o reports/week-42.md

  Last week's report:
    python status_report.py -w -1 -i notes.md

input file format (multi-team):
  ## Team Alpha
  - Shipped the new authentication flow
  - Resolved 3 high-priority bugs

  ## Platform
  - Completed database migration to Postgres 16
  - Blocked on security review for new S3 bucket policy
        """,
    )
    parser.add_argument(
        "--input", "-i",
        metavar="FILE",
        help="Markdown or text file containing meeting notes",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Save generated report to this file (Markdown)",
    )
    parser.add_argument(
        "--week", "-w",
        type=int,
        default=0,
        metavar="N",
        help="Week offset: 0=current (default), -1=last week, 1=next week",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Wait for the full response instead of streaming",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    monday, friday = get_week_range(args.week)
    week_header = format_week_header(monday, friday)
    print(f"\n📅 Report period: {week_header}")

    if args.input:
        teams = read_notes_from_file(args.input)
        team_names = ", ".join(teams.keys())
        print(f"📋 Loaded notes for {len(teams)} team(s): {team_names}")
    else:
        teams = collect_notes_interactively()

    if not teams:
        print("Error: No notes were provided.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic()
    report = generate_report(
        teams=teams,
        week_header=week_header,
        client=client,
        use_stream=not args.no_stream,
    )

    if args.output:
        save_report(report, args.output, week_header)

    print("\n✅ Done.")


if __name__ == "__main__":
    main()
