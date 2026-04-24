---
name: garmin-connect-cli
description: Use when managing Garmin Connect workouts, scheduled calendar entries, or activities from the command line — e.g. uploading workout JSON files, listing scheduled sessions, renaming or retyping activities. Requires the garmin-connect-cli tool installed and a login session established with `garmin login`.
---

# garmin-connect-cli

Use this skill when the user wants to interact with their Garmin Connect
account from the command line using the `garmin` CLI, including building
and uploading structured workout JSON files.

## Prerequisites

Before running any `garmin` command, check the CLI is installed:

```bash
command -v garmin
```

If it's not, install with `pipx` (preferred — isolated venv, global binary):

```bash
pipx install git+https://github.com/frankmatheron/garmin-connect-cli
```

Or with `pip` into the active environment:

```bash
pip install git+https://github.com/frankmatheron/garmin-connect-cli
```

Then the user needs to log in once:

```bash
garmin login
```

This prompts for username and password interactively and caches session
tokens at `$XDG_DATA_HOME/garmin-connect-cli/tokens/` (default
`~/.local/share/garmin-connect-cli/tokens/`). If any `garmin` command
later fails with `"ERROR: Not logged in"`, prompt the user to re-run
`garmin login` — tokens may have expired.

Built on the `garminconnect` Python library.

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

### Zones

Read and write HR zone configuration on the Garmin Connect server.
Zones are stored per sport — a `DEFAULT` set plus optional sport
overrides like `RUNNING`. Structured workouts that target
`heart.rate.zone` (via `zoneNumber: N`) resolve symbolically against
the sport-specific set if one exists, else against `DEFAULT`. A
desynced `RUNNING` override silently makes workout HR targets drift
away from the values shown under profile zones in the web UI — this
is the usual cause of "I updated my zones but the workout still shows
the old numbers."

```bash
garmin zones list                                 # current zones per sport
garmin -p zones list                              # pretty table
garmin zones set --max-hr 190 --rhr 47            # updates DEFAULT + RUNNING (Karvonen)
garmin zones set --max-hr 190 --rhr 47 --sport RUNNING
garmin zones set --max-hr 190 --rhr 47 --method PERCENT_MAX_HR
garmin zones set --max-hr 190 --rhr 47 --zones 118,133,147,161,176
```

`set` auto-computes Z1–Z5 floors at the standard 50/60/70/80/90
percentages for the chosen method (`HR_RESERVE` for Karvonen / %HRR,
default; `PERCENT_MAX_HR` for %Max). Use `--zones` to override floors
explicitly.

Effects:
- Applies to newly-recorded activities and to structured workouts
  resolved from the server from now on (workout JSON uses
  `zoneNumber: N` symbolically, not absolute bpm).
- Past activities keep the zone distribution frozen at the config
  that was active when they were recorded; re-upload the FIT file if
  you need them re-classified.
- The watch keeps its own local copy of zones — force a sync (pull-
  down menu on watch) after changing zones on the server so the
  watch's real-time display and in-workout HR targets match.

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
| Interval   | 3          | `interval`  | Running portions; strength exercises |
| Recovery   | 4          | `recovery`  | Walking inside repeats              |
| Rest       | 5          | `rest`      | Rest between strength sets          |
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

## Strength workouts

For strength training workouts, set `sportType` to `strength_training`:

```json
"sportType": {"sportTypeId": 5, "sportTypeKey": "strength_training", "displayOrder": 5}
```

### Exercise taxonomy

Each strength `interval` step can specify an exercise using Garmin's
two-level taxonomy:

- `category` — exercise group (broad, e.g. `PUSH_UP`, `PLANK`, `SQUAT`)
- `exerciseName` — specific variant within the group

Without these, the watch shows a generic timed/rep block with your
`description` as a label. With them, the watch prompts the exercise by
name, can show animations, and can do auto-rep detection on supported
devices.

Example strength step:

```json
{
  "type": "ExecutableStepDTO",
  "stepOrder": 2,
  "stepType": {"stepTypeId": 3, "stepTypeKey": "interval", "displayOrder": 3},
  "description": "Pushups",
  "endCondition": {"conditionTypeId": 10, "conditionTypeKey": "reps", "displayOrder": 10, "displayable": true},
  "endConditionValue": 10.0,
  "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1},
  "category": "PUSH_UP",
  "exerciseName": "PUSH_UP"
}
```

### Rep-based end condition

For counted movements (pushups, squats, rows, etc.), use reps:

```json
"endCondition": {"conditionTypeId": 10, "conditionTypeKey": "reps", "displayOrder": 10, "displayable": true},
"endConditionValue": 10.0
```

For held movements (planks, side planks, wall sits), use time
(`conditionTypeId: 2`) — same encoding as running time intervals.

### Rest steps

Rest between strength sets uses `stepType: rest` (stepTypeId 5) with a
time-based end condition:

```json
{
  "type": "ExecutableStepDTO",
  "stepOrder": 3,
  "stepType": {"stepTypeId": 5, "stepTypeKey": "rest", "displayOrder": 5},
  "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time", "displayOrder": 2, "displayable": true},
  "endConditionValue": 60.0,
  "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1}
}
```

Pattern inside a repeat group for strength: **exercise step → rest
step**, repeated `numberOfIterations` times.

### Looking up category + exerciseName codes

`strength-exercises.json` in this skill's directory is a complete dump
of Garmin's exercise taxonomy: 47 categories, ~1500 exercises, with
muscle group metadata. Structure:

```json
{
  "categories": {
    "PUSH_UP": {
      "exercises": {
        "PUSH_UP": {"primaryMuscles": [...], "secondaryMuscles": [...]},
        "WIDE_GRIP_PUSH_UP": {...},
        ...
      }
    },
    ...
  }
}
```

To find a code: grep the file for the exercise name or guess the
category.

### All 47 categories

| Category              | # exercises | Notes                                            |
|-----------------------|-------------|--------------------------------------------------|
| `BANDED_EXERCISES`    |          44 | Resistance band movements                        |
| `BATTLE_ROPE`         |          29 | Battle rope drills                               |
| `BENCH_PRESS`         |          28 | Horizontal pressing                              |
| `BIKE_OUTDOOR`        |           1 | Outdoor cycling                                  |
| `CALF_RAISE`          |          22 | All calf raise variants                          |
| `CARDIO`              |          22 | General cardio (jumping jacks, burpees, etc.)    |
| `CARRY`               |          10 | Farmer's walks, overhead carries                 |
| `CHOP`                |          24 | Cable/dumbbell woodchops                         |
| `CORE`                |          56 | Core stability (non-crunch)                      |
| `CRUNCH`              |          86 | Crunch variants                                  |
| `CURL`                |          48 | Biceps and hamstring curls                       |
| `DEADLIFT`            |          25 | All deadlift variants                            |
| `ELLIPTICAL`          |           1 | Elliptical                                       |
| `FLOOR_CLIMB`         |           1 | Stair climber                                    |
| `FLYE`                |           9 | Chest flyes                                      |
| `HIP_RAISE`           |          44 | Glute bridges, hip thrusts                       |
| `HIP_STABILITY`       |          36 | Clamshells, fire hydrants                        |
| `HIP_SWING`           |           5 | Kettlebell swings                                |
| `HYPEREXTENSION`      |          39 | Back/hip extensions                              |
| `INDOOR_BIKE`         |           3 | Indoor cycling                                   |
| `LADDER`              |           2 | Agility ladder                                   |
| `LATERAL_RAISE`       |          35 | Shoulder lateral raises                          |
| `LEG_CURL`            |          14 | Hamstring curl variants                          |
| `LEG_RAISE`           |          23 | Hanging/lying leg raises                         |
| `LUNGE`               |          91 | All lunge variants                               |
| `OLYMPIC_LIFT`        |          29 | Cleans, snatches, jerks                          |
| `PLANK`               |         131 | Planks + side planks + variations                |
| `PLYO`                |          38 | Plyometric / jump work                           |
| `PULL_UP`             |          46 | Pull-up + chin-up variants                       |
| `PUSH_UP`             |          89 | All push-up variants                             |
| `ROW`                 |          51 | Rowing movements                                 |
| `RUN`                 |           5 | Running                                          |
| `RUN_INDOOR`          |           2 | Treadmill running                                |
| `SANDBAG`             |          20 | Sandbag training                                 |
| `SHOULDER_PRESS`      |          28 | Overhead pressing                                |
| `SHOULDER_STABILITY`  |          37 | Rotator cuff / scap work                         |
| `SHRUG`               |          21 | Trap shrugs                                      |
| `SIT_UP`              |          41 | Sit-up variants                                  |
| `SLED`                |           6 | Sled pushes/pulls                                |
| `SLEDGE_HAMMER`       |           3 | Sledgehammer strikes                             |
| `SQUAT`               |          98 | All squat variants                               |
| `STAIR_STEPPER`       |           1 | Stair stepper                                    |
| `SUSPENSION`          |          33 | TRX / suspension trainer                         |
| `TIRE`                |           2 | Tire flips                                       |
| `TOTAL_BODY`          |          18 | Compound/full-body (thrusters, burpees w/ row)   |
| `TRICEPS_EXTENSION`   |          43 | All triceps extension variants                   |
| `WARM_UP`             |          70 | Dynamic warmup movements                         |

Total: **1510 exercises across 47 categories.**

For the exact `exerciseName` values within a category, grep
`strength-exercises.json`. Commonly-needed exercise codes (confirmed
via Garmin Connect round-trip):

| Exercise            | category     | exerciseName                       |
|---------------------|--------------|------------------------------------|
| Pushup              | `PUSH_UP`    | `PUSH_UP`                          |
| Plank               | `PLANK`      | `PLANK`                            |
| Side plank          | `PLANK`      | `SIDE_PLANK`                       |
| Glute bridge        | `HIP_RAISE`  | `HIP_RAISE`                        |
| Single-leg calf raise | `CALF_RAISE` | `SINGLE_LEG_STANDING_CALF_RAISE` |

Gotchas:

- Category names are anatomical/movement-based, not colloquial. "Glute
  bridge" lives under `HIP_RAISE`, not `GLUTE_BRIDGE`.
- Sub-variants sometimes live under a parent category: side plank is
  `category: PLANK`, `exerciseName: SIDE_PLANK`.
- Uploading with an invalid `category` returns
  `API Error 400 - Invalid category`. Confirm against
  `strength-exercises.json` before uploading.
- Always set both `category` and `exerciseName`. Setting only one is
  likely to fail or silently drop.

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
- **Zones per sport:** editing HR zones in the Garmin Connect web UI
  often updates only one of the per-sport sets (e.g. `DEFAULT` stays at
  old values while `RUNNING` gets changed, or vice versa). Structured
  workouts read from the sport-specific set, so a mismatch silently
  makes workout HR targets disagree with the profile zones shown in the
  UI. When the user reports "my zones look right but the workout
  shows wrong numbers," run `garmin -p zones list` first — that reveals
  the desync in one command. Use `garmin zones set` to align both sets.
