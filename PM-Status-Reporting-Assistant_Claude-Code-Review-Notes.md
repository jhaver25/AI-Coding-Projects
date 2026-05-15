# PM Status Reporting Assistant — Claude Code Review Notes

---

## ISSUE 1: Handling for Empty or Whitespace-Only Input

**Problem:** If a user runs the tool without providing any input (e.g., meeting notes), whether via a file or directly in the terminal, the script will pass an empty string to the Claude API, which wastes API credits and returns a blank, useless report. There aren't sufficient guards to prevent pass-through of empty or whitespace-only strings.

**Fix:** We'll need to make three code changes throughout the script to accommodate this validation — the first for a totally blank file or input in the initial read of the file, the second and third changes for handling blank team sections in multi-team parsing of the file (mid-script).

### Issue 1 — Change #1 (Catch empty or whitespace-only files immediately after reading)

**BEFORE** _(lines 137–138)_
```python
content = path.read_text(encoding="utf-8").strip()
teams: dict[str, str] = {}
```

**AFTER**
```python
content = path.read_text(encoding="utf-8").strip()
if not content:
    print(f"Error: File is empty or contains only whitespace: {filepath}", file=sys.stderr)
    sys.exit(1)

teams: dict[str, str] = {}
```

### Issue 1 — Changes #2 and #3 (Filter whitespace-only team sections in multi-team parsing)

**BEFORE** _(lines 145–146 + 152–153)_
```python
if current_team and current_lines:
    teams[current_team] = "\n".join(current_lines).strip()
```

**AFTER**
```python
notes = "\n".join(current_lines).strip()
if current_team and notes:
    teams[current_team] = notes
elif current_team:
    print(f"  ! No notes found for '{current_team}' — skipping.", file=sys.stderr)
```

**Takeaway:** Need to complete validations and checks up-front, before API calls, to improve both user experience and cost management. Every API call costs money, regardless of the value of the actual output.

---

## ISSUE 2: `##` Detection Bug for Multi-Team Notes (Silent Mis-parse for .md File Input)

**Problem:** If a user's notes happen to include H2 markdown anywhere in the text (e.g., `## Q2 Goals`), the parser will silently misinterpret that heading as the start of another team's notes. This mis-parsing will result in splitting the content incorrectly, resulting in a confusing report output.

**Fix:** We'll handle this via 2 changes — a minor code re-write to handle the `##` mis-parsing, and generating a notes template for users to better enforce the appropriate format for multi-team meeting notes.

### Issue 2 — Change #1 (Use `line.startswith` for identifying team sections)

**BEFORE** _(line 140)_
```python
if "## " in content:
```

**AFTER**
```python
if any(line.startswith("## ") for line in content.splitlines()):
```

### Issue 2 — Change #2 (Notes template)

A `notes_template.md` file was created in the project directory for users to copy and fill in:

```markdown
<!--
  Weekly Status Report Notes Template
  ─────────────────────────────────────
  Instructions:
  • One section per team or project (the ## heading is the team/project name)
  • Use plain bullet points under each section
  • Add or remove team sections as needed
  • Save this file and pass it to the tool: python status_report.py -i my_notes.md
  • Single-team? Delete all but one ## section, or just use a plain .txt file
-->

## Team / Project Name
- What was completed or shipped this week
- Any key accomplishments or milestones hit

## Team / Project Name
- Work in progress this week
- Any blockers or dependencies (e.g. "waiting on security review for S3 policy")
- Plans for next week

## Team / Project Name
- Brief bullet points are fine — the tool will expand them into the full report format
- Mention incidents, outages, or on-call events here if relevant
```

**Takeaway:** The tool's current design has high preference for markdown (.md) files, which are typically used by more technically-oriented users. To accommodate the less technically-inclined, we built a template for those users so they can still make use of the tool — avoiding far more complex code changes for these early iterations of the tool (additional file types and formats are on the roadmap for later). We also eliminated a future issue by making the parsing of markdown format more resilient to user input in case an additional H2 line (`"## "`) is entered elsewhere in the file.

---

## ISSUE 3: API Error Handling

**Problem:** There is no try/except around the Anthropic API call, which could cause confusion for inexperienced users. Rate limits, network failures, invalid API key format errors, context-length overflows, and service outages all surface as raw Python tracebacks, which isn't user-friendly for most. If they don't know what to check, they might be caught at an absolute dead-end and unable to proceed with their task.

**Fix:** Wrap the API call in a try/except to catch various errors and print a clear, actionable message before exiting the script. This requires one large, structural change to handle the following scenarios:

- `AuthenticationError` — bad or expired API key (very common for new users)
- `RateLimitError` — hit usage limits
- `APIConnectionError` — no internet / VPN / firewall issues
- `BadRequestError` — input too long (relevant for large, multi-team notes)
- `APIStatusError` — catch-all for any other HTTP error from the API with the status code included

### Issue 3 — Change #1 (try/except for various error types)

**BEFORE** _(lines 239–266)_
```python
print("\n⏳ Generating report...\n")
print("─" * 60)

if use_stream:
    report_text = ""
    with client.messages.stream(
        ...
    ) as stream:
        ...
    print("\n" + "─" * 60)
    _print_cache_stats(final.usage)
    return report_text
else:
    response = client.messages.create(
        ...
    )
    text = next(b.text for b in response.content if b.type == "text")
    ...
    return text
```

**AFTER**
```python
print("\n⏳ Generating report...\n")
print("─" * 60)

try:
    if use_stream:
        report_text = ""
        with client.messages.stream(
            ...
        ) as stream:
            ...
        print("\n" + "─" * 60)
        _print_cache_stats(final.usage)
        return report_text
    else:
        response = client.messages.create(
            ...
        )
        text = next(b.text for b in response.content if b.type == "text")
        ...
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
```

**Takeaway:** Considering this tool will be available for various types of users, it is important to provide as much information as possible when the tool encounters problems. This change improves user experience by giving the user more clarity on various types of errors and how they can fix the problem to proceed with their task.

---

## ISSUE 4: Unsupported File Types

**Problem:** The tool, in its current iteration, is only designed to work with `.md` or `.txt` file types. We need to provide messaging to users to use only `.md` or `.txt` files when they try to use `.doc`, `.pdf`, or other unsupported file types. We also need to capture when file type extensions are in various cases to prevent further read errors, even when using the correct file types.

**Fix:** Apply a file extension check directly after the "file-exists" check to ensure the correct file type has been used _before_ attempting to read the file. Normalize the case of the extension so that `.MD`, `.TXT`, `.Txt`, etc. all pass through the script.

### Issue 4 — Change #1 (File type validation)

**BEFORE** _(lines 133–138)_
```python
path = Path(filepath)
if not path.exists():
    print(f"Error: File not found: {filepath}", file=sys.stderr)
    sys.exit(1)

content = path.read_text(encoding="utf-8").strip()
```

**AFTER**
```python
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
```

**Takeaway:** Again, providing as much information to users as possible will vastly improve both their experience and usability of the tool. In this instance, we are doing an extension check before the file is read to exit the script at the earliest possible error and to provide the user with feedback (and a tip) so they can make adjustments and proceed with their task. NOTE: including additional file types can be a future improvement on the roadmap, but is not suitable for the current iteration of the tool.

---

## OTHER ISSUES / IMPROVEMENTS IDENTIFIED (ROADMAP)

### Issue 5 — File Encoding Errors

**File:** `read_notes_from_file()`, line 137

`path.read_text(encoding="utf-8")` will raise `UnicodeDecodeError` on files saved from Windows Notepad, older Word exports, or certain Google Doc exports that default to Windows-1252 or Latin-1 encoding. This is common among non-technical stakeholders who paste notes into a Windows text editor.

**Fix:** Add a fallback: try UTF-8 first, then retry with `errors="replace"` or detect encoding via `chardet`, with a warning if fallback is used.

---

### Issue 6 — Preamble Content Silently Dropped

**File:** `read_notes_from_file()`, lines 142–153

In multi-team format, any content before the first `## ` header is silently discarded. A user who adds a date, meeting title, or context paragraph at the top of their notes file will lose that content with no warning.

**Fix:** Capture pre-header content and either include it in the first team's notes, add it to a synthetic "Context" section, or warn the user that it was skipped.

---

### Issue 7 — Report Truncation: `max_tokens=4096` Hardcoded

**File:** `generate_report()`, line 244

For organizations with 6+ teams and detailed notes, the generated report can easily exceed 4,096 output tokens. When this happens, the report is silently truncated mid-sentence with no warning. A `--max-tokens` flag and a check on `stop_reason == "max_tokens"` would let users know this happened.

**Fix:** Add a `--max-tokens` CLI argument (default 4096, allow up to 8192), and after generation check `final.stop_reason` — if it's `"max_tokens"`, print a warning.

---

### Issue 8 — Silent Overwrite of Output Files

**File:** `save_report()`, line 285

`path.write_text(...)` silently overwrites an existing report with no confirmation prompt. A user running the tool a second time with the same `-o` path (e.g. `reports/week-42.md`) will lose the previous report without warning.

**Fix:** Check `path.exists()` before writing and either prompt for confirmation or auto-append a timestamp suffix.

---

### Issue 9 — Duplicate Team Names Silently Overwrite

**File:** `read_notes_from_file()`, lines 145–146

If the same `## Team Name` header appears twice in a notes file, the second one silently overwrites the first in the `teams` dict. A user who accidentally duplicates a section header loses half their notes.

**Fix:** Check for key collision and either merge the content or warn the user.

---

### Issue 10 — Interactive Mode: Blank Lines in Pasted Content Cut Off Early

**File:** `collect_notes_interactively()`, lines 181–189

The double-blank-line sentinel to end input is reasonable for typed notes, but breaks when a user pastes formatted notes that contain intentional blank lines between bullet groups. Input is truncated at the first double blank, silently.

**Fix:** Default the terminator to `end` (already supported) and make the double-blank behavior opt-in, or increase the blank-streak threshold, or prompt the user to use `end` more prominently.

---

### Issue 11 — Email Draft Output Mode

**File:** `main()` / `generate_report()`

There's no way to generate a stakeholder-facing email summary alongside or instead of the full report. This is a high-value workflow for PMs and engineering leads who need to communicate status upward after generating the internal report. The model is already primed with all the right context.

**Fix:** Add a `--email` flag that makes a second (or combined) API call using the generated report as input to produce a concise stakeholder email draft, appended to the output file under an `## Email Draft` section.

---

### Issue 12 — `StopIteration` in Non-Streaming Path

**File:** `generate_report()`, line 262

`next(b.text for b in response.content if b.type == "text")` raises `StopIteration` if the API response contains no text block — theoretically possible if the model returns only a tool call or an error block. A safer pattern is `next((...), "")` with a default and an error check.

---

### Issue 13 — Week Offset Unbounded

**File:** `get_week_range()`, line 113; `main()`, line 335

`--week` accepts any integer. `--week -500` produces a date in 2016 with no warning. Should be bounded (e.g. -52 to +4) with a validation error and message.

---

### Issue 14 — No Model Selection Flag

**File:** `generate_report()`, line 244

The model is hardcoded to `claude-sonnet-4-6`. An engineering executive might want to run a faster/cheaper Haiku pass for a quick draft, or a more thorough Opus pass for a board-level report. A `--model` flag would support this without code changes.
