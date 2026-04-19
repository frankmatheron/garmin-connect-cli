# garmin-connect-cli

[![CI](https://github.com/frankmatheron/garmin-connect-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/frankmatheron/garmin-connect-cli/actions/workflows/ci.yml)

CLI for managing Garmin Connect workouts, calendar, and activities.

> **Unofficial.** This project is not affiliated with Garmin. It uses the
> community-maintained [`garminconnect`](https://github.com/cyberjunky/python-garminconnect)
> library, which wraps an undocumented Garmin Connect API. Expect occasional
> breakage when Garmin changes things on their end.

## How I use this

I built this CLI to be driven by an agent, not by me. The whole point is to
give Claude a small, predictable surface it can use to read, create, and
schedule Garmin Connect workouts on my behalf — so the interesting work
(designing the training, reviewing how it went) stays in conversation, and
the mechanical work (uploading JSON, scheduling dates, pulling activity
stats) becomes a tool call.

The setup I actually use:

1. **A separate `workout-planning/` repo holds the plan.** It has a
   `PLAN.md` describing a phased marathon progression (5K → 10K → 15K → 21K
   → 42K) based on [Runnersworld.nl](https://www.runnersworld.nl/) schedules,
   plus the source PDFs. That's Claude's long-term context for my training.
2. **Claude generates the workout JSON.** In a session, I'll say something
   like "generate next week's workouts" and Claude writes one JSON file per
   training — warmup, intervals, recovery, cooldown, HR-zone targets, repeat
   groups. It gets the format right because this repo ships a Claude skill
   at `skills/garmin-connect-cli/` with the full JSON reference and command
   catalogue. The skill is the contract between the agent and the CLI.
3. **Claude calls this CLI to sync to Garmin.** Still in the same session,
   Claude runs:

   ```bash
   garmin workouts create garmin_json/10k_w3_fri_05jun.json
   garmin calendar add <workout-id> 2026-06-05
   ```

   …and the session lands on the watch. I don't type those commands; Claude
   does. My job is to say "upload and schedule this week" and approve the
   tool calls.
4. **After the run, Claude pulls the activity back for analysis.** I'll ask
   "how did yesterday's intervals go?" and Claude uses the same CLI to fetch
   the data:

   ```bash
   garmin activities list 2026-06-05 2026-06-05 --type running
   garmin activities splits <activity-id>
   garmin activities hr <activity-id>
   garmin activities details <activity-id>
   ```

   From there we discuss what's actually interesting: time in each HR zone,
   cadence and stride length, how the splits drifted, whether easy runs
   stayed easy. Over weeks and months this turns into a real progression
   conversation — not just a dashboard I glance at.

That's why the CLI looks the way it does: deterministic output, JSON in /
JSON out, flags that mirror the Garmin Connect data model, no interactive
prompts once authenticated. It's designed to be boring and scriptable so an
agent can use it reliably for both sides of the loop — prescribing the
training and reflecting on the result.

If you want to set up something similar, start with
`skills/garmin-connect-cli/SKILL.md` — any agent that loads that skill can
produce valid workouts and drive this CLI without extra hand-holding.

## Install

Requires Python 3.12+.

```bash
pip install git+https://github.com/frankmatheron/garmin-connect-cli
```

For local development:

```bash
git clone https://github.com/frankmatheron/garmin-connect-cli
cd garmin-connect-cli
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Authentication

**Primary flow:**

```bash
garmin login     # prompts for username + password, caches tokens
garmin logout    # deletes cached tokens
```

Tokens are cached at `$XDG_DATA_HOME/garmin-connect-cli/tokens/` (default
`~/.local/share/garmin-connect-cli/tokens/`). Set `GARMIN_TOKEN_DIR` to
override. The password is not stored anywhere — only the session tokens.

**Automation / CI flow:**

Set `GARMIN_USERNAME` and `GARMIN_PASSWORD` as environment variables, or
place them in a `.env` file in the current directory. The env-var path is
used only when no cached tokens exist.

**Known limitation:** MFA accounts are not currently supported.

## Usage

### `workouts`

```bash
garmin workouts list                              # all workouts (JSON)
garmin -p workouts list                           # same, human-readable
garmin workouts get <id>                          # full workout JSON
garmin workouts create path/to/workout.json       # upload one file
garmin workouts create a.json b.json c.json       # upload multiple files
garmin workouts create -                          # upload from stdin
garmin workouts delete <id>                       # delete a workout
```

### `calendar`

```bash
garmin calendar list <year> <month>               # scheduled workouts
garmin calendar add <workout-id> <YYYY-MM-DD>     # schedule on a date
garmin calendar remove <scheduled-id>             # unschedule
```

### `activities`

```bash
garmin activities list <start> <end> [--type running]
garmin activities get <id>                        # full activity JSON
garmin activities splits <id>                     # per-split breakdown
garmin activities details <id>                    # time-series detail
garmin activities hr <id>                         # HR-in-zones summary
garmin activities rename <id> "New name"
garmin activities retype <id> --type-key running
```

## Workout JSON format

Workouts are uploaded as JSON matching Garmin's native structure. Two
runnable files live in `examples/`. The essentials:

### Skeleton

```json
{
  "workoutName": "Name shown in Garmin Connect",
  "description": "Free text",
  "sportType": {"sportTypeId": 1, "sportTypeKey": "running", "displayOrder": 1},
  "estimatedDurationInSecs": 2400,
  "author": {},
  "workoutSegments": [{"segmentOrder": 1, "sportType": {...}, "workoutSteps": [...]}]
}
```

### Step types

| Purpose    | stepTypeId | stepTypeKey | When to use                        |
|------------|------------|-------------|------------------------------------|
| Warmup     | 1          | `warmup`    | First step, no target              |
| Cooldown   | 2          | `cooldown`  | Last step, no target               |
| Interval   | 3          | `interval`  | Running work                       |
| Recovery   | 4          | `recovery`  | Walking within repeats             |
| Repeat     | 6          | `repeat`    | `RepeatGroupDTO` wrapper for sets  |

`stepOrder` must be unique and sequential across **all** steps, including
those inside repeat groups.

### End condition (time-based)

```json
"endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time", "displayOrder": 2, "displayable": true},
"endConditionValue": 300.0
```

### HR zone target

```json
"targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone", "displayOrder": 4},
"zoneNumber": 2
```

Use `zoneNumber` for HR zones — not `targetValueOne` / `targetValueTwo`
(those set an absolute BPM range).

### Repeat group

```json
{
  "type": "RepeatGroupDTO",
  "stepOrder": 2,
  "stepType": {"stepTypeId": 6, "stepTypeKey": "repeat", "displayOrder": 6},
  "numberOfIterations": 5,
  "smartRepeat": false,
  "endCondition": {"conditionTypeId": 7, "conditionTypeKey": "iterations", "displayOrder": 7, "displayable": false},
  "endConditionValue": 5.0,
  "workoutSteps": [
    {/* interval (run) — comes FIRST */},
    {/* recovery (walk) — comes SECOND */}
  ]
}
```

Order inside repeats: **interval before recovery** (run first, then walk).

## Examples

- `examples/workout-continuous-run.json` — 30-minute steady run at HR zone 2.
- `examples/workout-intervals.json` — 5×(3 min run at HR zone 2 / 1 min walk).

Upload either with `garmin workouts create examples/<file>.json`.

## Development

```bash
.venv/bin/pytest                 # run tests
.venv/bin/garmin --help          # CLI help
```

Python 3.12+ required.

## Credits

Built on [`garminconnect`](https://github.com/cyberjunky/python-garminconnect)
by Ron Klinkien, which handles Garmin Connect authentication and the
underlying API calls. Thanks to the maintainers for keeping an unofficial
client alive.

## License

MIT — see [`LICENSE`](LICENSE).
