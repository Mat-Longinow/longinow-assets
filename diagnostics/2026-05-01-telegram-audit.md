# 📡 Telegram outbound audit — last 48h

**Window:** 2026-04-29 07:00 PDT → 2026-05-01 08:00 PDT (49h)
**Author:** Alfred (diagnostic, no policy changes shipped)
**Source files scanned:** `agents/_shared/telegram.py` log lines (`Telegram sent / silent / failed / skipped`) across every agent in the fleet, plus the alfred-bot's chat-reply traffic for context.

## 🎯 Top-line numbers

| Source | Pings (48h) | Loud / Silent / Failed |
| --- | ---: | --- |
| project-manager drainer | **36** | 31 / 5 / 0 |
| personal-assistant drainer | **11** | 7 / 4 / 0 |
| event-brief | **10** | 4 / 6 / 0 |
| morning-brief | 0 | — |
| Mail Man | 0 | — |
| financial / transcript / weekly-cleanup / dashboard / reacher / time-blocks | 0 | — |
| **TOTAL push pings** | **57** | 42 / 15 / 0 |

For context, the alfred-bot's `launchd.log` shows 0 proactive `Notification sent` events in the window — every chat-style sendMessage logged there is a reply to one of Mat's inbound messages, not a push. So the 57 push pings above are the entire universe of unsolicited Telegram pings the fleet fired at Mat in 48h.

## 🚨 Signal vs. digest vs. noise

| Bucket | Pings | What it is |
| --- | ---: | --- |
| ✅ Genuine signal — Mat's eyes were needed | **17** | task completions / Needs Input prompts / first-time status pivots |
| 📬 Digest-worthy — true but should batch | **14** | calendar reminders, duplicate completions, recurring daily events |
| 🗑️ Noise — should not have fired | **26** | 24× pre-refactor Progress storm on warranty-refund + 2× redundant External Wait re-fires after pivot already announced |
| **TOTAL** | **57** | |

## 🥇 Top 3 offenders

### 1. project-manager warranty-refund Progress storm — 4/30 16:22–16:42

**19 ▶️ Progress pings on the same project in 20 minutes** (one every ~60s). Plus an earlier 5-ping cluster 09:09–09:16. All pre-refactor (the rebuild went live at 17:05). These are the loudest noise in the window.

```
[2026-04-30 16:22:27] Telegram sent: 🎩 ▶️ warranty-refund (Progress)
[2026-04-30 16:23:44] Telegram sent: 🎩 ▶️ warranty-refund (Progress)
... 17 more lines, 16:25 → 16:42 ...
[2026-04-30 16:41:56] Telegram sent: 🎩 ▶️ warranty-refund (Progress)
```

**Why it fired:** the old drainer pinged on every cycle while the project was Active. The 2026-04-30 PM refactor specifically targets this — Progress-with-no-pivot is now silent. Storm is closed historically; this is a backward-looking artifact, not an ongoing issue.

### 2. project-manager External Wait re-firing every cycle — POST-refactor bug

**8 🟣 External Wait pings overnight 4/30 17:46 → 5/1 03:06** on miriam-birthday (×7) and warranty-refund (×1). These are *after* the refactor went live. They're the exact "just holding" pattern Mat described — the project hasn't moved, status hasn't pivoted, but the drainer pings every cycle anyway to reaffirm "still externally waiting."

**Root cause — `agents/project-manager/run.py:829`:**

```python
pivoted  = status_before != status_after
terminal = status != "PROGRESS"          # ← BUG
should_ping = pivoted or terminal or material
```

`terminal` here is named misleadingly. It includes EXTERNAL_WAIT, NEEDS_INPUT, STUCK, and ACTIVE — every status that isn't PROGRESS. So any cycle that returns one of those statuses, even if the prior cycle returned the *same* one, fires a ping. The variable should mean *truly terminal* — i.e. COMPLETED or ABANDONED — and only those should always-ping.

This is a one-line fix that would silence the dominant ongoing noise pattern without losing any genuine signal. (Not shipping it in this task per scope — recommendation only.)

### 3. personal-assistant duplicate REFACTOR-completion ping — 4/30 17:05 + 17:08

Same task ("REFACTOR: project-manager drainer rebuilt…") fired ✅ Completed twice three minutes apart. Likely a re-trigger of the queue line during the same drainer cycle (the close was a long edit that may have been touched twice). Low-impact, but illustrates that the personal-assistant drainer doesn't dedupe a completion-ping against a recent identical one.

## 📊 Per-source breakdown

### project-manager drainer (36 pings, 63% of fleet volume)

All routed through the personal-assistant Telegram bot (project-manager shares Alfred's bot env — that's why the log says `via personal-assistant`).

- **warranty-refund: 27 pings** — 24 ▶️ Progress (mostly the 16:22–16:42 storm + earlier 09:09–09:16 cluster), 2 🟣 External Wait re-fires, 1 🟣 External Wait genuine pivot (09:16 → 15:50 cluster).
- **miriam-birthday: 7 pings** — all 🟣 External Wait. First one (17:46) is the genuine Active → External Wait pivot; the next 6 are redundant re-fires of the same status across cycles.
- **ca-dl-realid-renewal: 1 ping** — 🤚 Needs Input (17:46). Genuine signal.
- **All other 8 projects: 0 pings.**

Classification: **6 signal · 4 digest · 26 noise.** This is the agent driving the "just holding" perception, full stop.

### personal-assistant drainer (11 pings, 19%)

These all map 1:1 to Mat-authored task transitions on `todos.md`:

| Time | Status | Task |
| --- | --- | --- |
| 4/29 05:55 | 🤚 Needs Input | Hub PWA |
| 4/30 09:01 | ✅ Completed | Lithia follow-up |
| 4/30 09:08 | ✅ Completed | project-manager fix |
| 4/30 09:43 | ▶️ Progress | paragraph-break converter |
| 4/30 09:45 | 🤚 Needs Input | paragraph-break converter |
| 4/30 12:51 | ✅ Completed | verbosity-trim |
| 4/30 15:55 | ✅ Completed | Extend project-manager drainer |
| 4/30 16:26 | 🤚 Needs Input | Bounded parallelism |
| 4/30 16:26 | 🤚 Needs Input | DESIGN PENDING |
| 4/30 17:05 | ✅ Completed | REFACTOR project-manager |
| 4/30 17:08 | ✅ Completed | REFACTOR project-manager (duplicate) |

Classification: **10 signal · 1 digest (the duplicate) · 0 noise.**

The 🤚 Needs Input pair at 4/30 16:26 (38 seconds apart) is a borderline digest case — same drainer cycle surfacing two adjacent tasks. Tolerable but worth a coalescing rule if Mat wants it cleaner.

### event-brief (10 pings, 18%)

Daily calendar-event lead-time reminders. Each ping is a discrete, well-spaced event:

- 4/29: School Drop Off (5:23, silent), Get It Done Coaching (7:52, silent), Mark/StoryArc (11:46), Chloe Neurofeedback (13:22), Jon McBirney (15:19)
- 4/30: School Drop Off (5:25, silent), Chloe Eye Appt (7:43, silent), Miriam birthday run-around (11:46)
- 5/1: School Drop Off (5:16, silent), Counseling with Amanda (6:52, silent)

Classification: **0 noise · 7 signal · 3 digest.** The recurring "School Drop Off — 6:30 AM" daily 5:25 silent ping is digest-worthy — Mat doesn't need a daily reminder of his routine school run if it's been on the books for years. Good candidate for a "silenced recurrence" allowlist.

## 🛠️ Recommended policy tweaks (no action taken — for Mat's review)

In rough order of payoff:

1. **Fix `run.py:829` in project-manager.** Rename the variable and tighten the condition so only TRULY terminal statuses (COMPLETED, ABANDONED) always-ping. EXTERNAL_WAIT, NEEDS_INPUT, STUCK, ACTIVE should ping ONLY on pivot from a different status. This single change kills ~25% of the 48h noise (the 8 "just holding" External Wait re-fires) and brings the per-cycle behavior in line with the refactor's stated intent.

2. **Coalesce duplicate-task pings within a drainer cycle.** If the personal-assistant drainer touches the same task twice in one cycle (the 4/30 17:05 + 17:08 REFACTOR case), only the last status update should ping. Trivial dedup keyed on `(task_id, status)` with a 5-minute TTL.

3. **"Needs Input" batching when more than one fires in a single cycle.** The 4/30 16:26 pair fired 38 seconds apart on different tasks. If two or more 🤚 Needs Input pings are queued from the same cycle, send a single combined ping ("two items want your eyes, sir: …") rather than two discrete pings.

4. **Allowlist of silenced recurrences for event-brief.** Mat's daily 6:30 AM school drop-off doesn't need a 5:25 AM reminder — it's a fixed routine. A short config of "silently skip these recurring events" would zero out ~3 pings/week with no signal loss. Same possibly applies to "Get It Done Coaching" if it's a fixed weekly slot.

5. **Project-level cooldown on External Wait.** Belt-and-suspenders backup to fix #1: if a project is in a non-PROGRESS status, don't ping that same status more than once per N hours regardless of pivot logic. Caps the worst-case blast radius of any future pivot-detection bug.

6. **Pre-existing protection still working:** the 22:00–08:00 quiet-hours silent-ping behavior in `agents/_shared/telegram.py:69-74` is functioning correctly — every overnight 4/30 22:26 → 5/1 03:06 ping was sent silently. Without that, Mat would have woken up to 4 buzzes overnight from the External Wait re-firing bug. Keep this rule untouched.

## 🧮 Cross-reference: Mail Man inbox volume

For correlation with #4's calendar-batching idea, here's email volume in the same window:

- Mail Man drafted/sent **2 emails** (both 2026-04-30: a service-contract refund follow-up at 08:59 and again at 15:34, same thread).
- Mail Man fired **0 Telegram pings** about inbound classifications in the window.
- The personal-assistant inbox has ~80 stuck `*_mail-man_request.json` files due to the unrelated `AttributeError: 'dict' object has no attribute 'strip'` bug currently logged in `run.log` (separate task in the queue — diagnose & fix). Once that's fixed, Mail Man will start firing inbound-email pings to Alfred's drainer, which is when the inbound-classification-batching rule from #3 will start mattering.

## 📎 Raw evidence

- project-manager log: `~/Library/Logs/com.mat.project-manager/run.log` lines 9–624
- personal-assistant log: `agents/personal-assistant/output/run.log` lines 2617–6816 (filtered to 4/29–5/1)
- event-brief log: `agents/event-brief/output/run.log` lines 3502–4330
- alfred-bot launchd: `~/Desktop/the-longinow-group/agents/bots/alfred-bot/logs/launchd.log` (439 chat-reply sendMessage calls, 0 proactive Notification sent events)
- Mail Man sent registry: `agents/mail-man/registry/sent-log.jsonl` (2 emails in window)

## 🎯 Bottom line

Mat's perception is correct. **45% of his 48h Telegram volume (26 of 57 pings) was noise.** The single most actionable lever is the `run.py:829` fix — it would close the ongoing "just holding" pattern with a one-line change. The pre-refactor warranty-refund storms are already addressed by the 4/30 PM rebuild. Calendar lead-time reminders are healthy with one minor polish opportunity.
