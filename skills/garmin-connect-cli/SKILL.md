---
name: garmin-connect-cli
description: Use when managing Garmin Connect workouts, scheduled calendar entries, or activities from the command line — e.g. uploading workout JSON files, listing scheduled sessions, renaming or retyping activities. Requires the garmin-connect-cli tool installed and a login session established with `garmin login`.
---

# garmin-connect-cli

Use this skill when the user wants to interact with their Garmin Connect
account from the command line using the `garmin` CLI, including building
and uploading structured workout JSON files.

## Prerequisites

- CLI installed: `pip install git+https://github.com/frankmatheron/garmin-connect-cli`
- Logged in once: `garmin login` (interactive prompt). Tokens are cached
  at `$XDG_DATA_HOME/garmin-connect-cli/tokens/` (default
  `~/.local/share/garmin-connect-cli/tokens/`).
- Built on the `garminconnect` Python library.

## Command reference

All commands support `-p` / `--pretty` at the top level for human-readable
table output. Default output is JSON. All commands exit `0` on success,
`1` on usage error, `2` on auth error, `3` on API error.

### Auth

```bash
garmin login       # prompts for username + password, caches tokens
garmin logout      # deletes cached tokens
```

### Workouts

```bash
garmin workouts list
garmin workouts get <id>
garmin workouts create <path-to-json> [<path> ...]      # file(s) or `-` for stdin
garmin workouts delete <id>
```

### Calendar

```bash
garmin calendar list <year> <month>
garmin calendar add <workout-id> <YYYY-MM-DD>
garmin calendar remove <scheduled-id>
```

### Activities

```bash
garmin activities list <start-date> <end-date> [--type <type>]
garmin activities get <id>
garmin activities splits <id>
garmin activities details <id>
garmin activities hr <id>
garmin activities rename <id> "<new name>"
garmin activities retype <id> --type-key <type> [--type-id <id>] [--parent-type-id <id>]
```

## Workout JSON format

Workouts are uploaded as JSON matching Garmin's native structure. When
the user asks you to build a workout, output a JSON object with this
shape.

### Skeleton

Every workout has: **warmup → main block(s) → cooldown**.

```json
{
  "workoutName": "Name shown in Garmin Connect",
  "description": "Free text",
  "sportType": {"sportTypeId": 1, "sportTypeKey": "running", "displayOrder": 1},
  "estimatedDurationInSecs": <total seconds>,
  "author": {},
  "workoutSegments": [
    {
      "segmentOrder": 1,
      "sportType": {"sportTypeId": 1, "sportTypeKey": "running", "displayOrder": 1},
      "workoutSteps": [ /* steps in order */ ]
    }
  ]
}
```

### Step types

| Purpose    | stepTypeId | stepTypeKey | Notes                               |
|------------|------------|-------------|-------------------------------------|
| Warmup     | 1          | `warmup`    | First step; use `no.target`         |
| Cooldown   | 2          | `cooldown`  | Last step; use `no.target`          |
| Interval   | 3          | `interval`  | Running portions                    |
| Recovery   | 4          | `recovery`  | Walking inside repeats              |
| Repeat     | 6          | `repeat`    | `RepeatGroupDTO` wrapper            |

`stepOrder` must be unique and sequential across ALL steps, including
children inside repeat groups.

### End condition (time-based)

```json
"endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time", "displayOrder": 2, "displayable": true},
"endConditionValue": <seconds as float>
```

### Targets

**HR zone** (for running steps):

```json
"targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone", "displayOrder": 4},
"zoneNumber": 2
```

**No target** (warmup, cooldown, walking):

```json
"targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1}
```

Never use `targetValueOne` / `targetValueTwo` for zone targets — that
sets an absolute BPM range. Use `zoneNumber` instead.

### Repeat groups

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
    { /* interval (run) — FIRST */ },
    { /* recovery (walk) — SECOND */ }
  ]
}
```

**Interval before recovery** inside repeats. Run first, then walk.

## Common workflows

### Upload and schedule a workout

```bash
# Build JSON (your task), save to my-workout.json, then:
garmin workouts create my-workout.json
# Response includes {"workoutId": N, ...}. Use N below.
garmin calendar add <N> 2026-05-01
```

### Find today's scheduled workouts

```bash
garmin -p calendar list 2026 5 | grep 2026-05-01
```

### Rename a misclassified activity

```bash
garmin activities rename 12345678 "Long Run — Zone 2"
```

### Retype a walk as a run

```bash
garmin activities retype 12345678 --type-key running --type-id 1 --parent-type-id 17
```

### Delete and replace a workout

```bash
garmin workouts delete <old-id>
garmin workouts create new-version.json
```

## Gotchas

- **HR zone encoding:** use `zoneNumber: N`, not `targetValueOne` /
  `targetValueTwo`. The latter is for absolute BPM ranges.
- **Repeat group order:** interval step comes BEFORE recovery step
  inside the group. Run first, walk second.
- **`stepOrder` uniqueness:** must be unique across the entire workout,
  including children of repeat groups.
- **Warmup + cooldown target:** always `no.target`. Don't set an HR zone
  on warmup/cooldown.
- **Token cache location:** `$XDG_DATA_HOME/garmin-connect-cli/tokens/`.
  If the user reports auth errors on a working account, suggest `garmin
  logout && garmin login` to refresh tokens.
- **Rate limits:** the CLI exits with code `3` on rate-limit errors.
  Wait ~2 minutes between retries.
- **MFA:** not supported in v1. If the user has MFA enabled, login will
  fail.
