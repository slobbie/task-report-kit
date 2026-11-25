# Task Report Kit

[한국어](README.ko.md)

Agent skills for Codex and Claude Code that review a task before work and verify it after, turning real app and web screenshots into numbered AS-IS/TO-BE HTML reports. Works with mobile apps (iOS, Android) and web services. The skill instructions and report text are written in Korean.

<img width="2400" height="1084" alt="AS-IS/TO-BE report example" src="https://github.com/user-attachments/assets/458d3509-1976-4432-98dd-fb38c6bf7acf" />

The image above shows the first item of the example report in [examples/coupon-checkout](examples/coupon-checkout): a demo shop where an expired coupon still applied at checkout. The screens were captured from the demo app before and after the fix with `web_capture.mjs`, and the report was built with `build_report.py`. Download `report.html` and open it in a browser to try the platform toggle.

## Skills

| Skill | When | Output |
| --- | --- | --- |
| `task-asis` | Before starting work, to find the problems in the current screens from specs, policies, Figma, or improvement requests | A review report: current screenshots with numbered problems (AS-IS), matching numbered changes and reasons (TO-BE), and a task list |
| `task-asis-tobe` | While implementing a task, or when verifying work already done | A result report pairing before/after screenshots with numbered changes and the problems they solve |
| `task-tobe` | When building a new screen, or reporting only the result without a before state | A TO-BE-only report: result screenshots with numbered markers and what each does |

All three skills share the report builder and writing guides in `task-asis-tobe`, so install them together. `task-plan` was renamed to `task-asis`; if you installed an earlier version, remove the `task-plan` folder and reinstall.

## What it does

- Captures screens that were actually run, not mockups. It tries the dev environment, then test data, then production (view only, personal data masked).
- Puts numbered markers on the screen and pairs each AS-IS problem with the TO-BE change of the same number. Marker positions come from element coordinates or pixel measurement.
- Uses one toggle for platforms that show the same screens, such as iOS and Android.
- Writes AS-IS as the problem (who is affected, why, and what happens) and TO-BE as the change and which problem it removes. Writing guides are in `skills/task-asis-tobe/references/` (Korean).
- Marks temporary capture code with `TEMP-CAPTURE` and removes it afterwards. Actions with real side effects (SMS, payments) are never executed.

## Install

### skills CLI

```bash
npx skills add slobbie/task-report-kit
```

Select all three skills, then choose Codex, Claude Code, or both. Add `-g` to install for the current user.

### Install script (macOS, Linux)

```bash
git clone https://github.com/slobbie/task-report-kit.git
cd task-report-kit
./install.sh          # copy into ~/.agents/skills (Codex) and ~/.claude/skills (Claude Code)
./install.sh --link   # symlink instead, for updating with git pull
```

Existing folders are never overwritten.

### Recommended companion

Install [natural-writing-kr](https://github.com/slobbie/natural-writing-kr) in the same skills folder to apply its Korean writing guidance as well.

## Requirements

- Common: Python 3, Google Chrome
- Web: Node.js, Playwright (installed in a scratch folder, not in your project)
- Mobile: Xcode Simulator, Android Emulator with `adb`, [Maestro](https://maestro.mobile.dev)

The mobile workflow was verified on React Native (Expo dev build). Other stacks follow the same steps with their own build commands.

## Usage

Claude Code: `/task-asis`, `/task-asis-tobe`, `/task-tobe`. Codex: `$task-asis`, `$task-asis-tobe`, `$task-tobe`.

```text
/task-asis Find the current problems on the sign-up screen using the attached spec and Figma link.
```

```text
/task-asis-tobe Add a "Forgot password" link to the login screen and report before/after screens on iOS and Android.
```

```text
/task-tobe Build a new order confirmation screen and report the result screens.
```

## License

MIT
