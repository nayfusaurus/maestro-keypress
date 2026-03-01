# GUI Redesign: Icon Rail Navigation + Multi-Page Layout

## Overview

Replace the top menu bar and single-view two-column layout with a left icon rail (56px) + QStackedWidget page system. Five pages: Dashboard, Settings, Info, Error Log, plus an Exit action.

## Navigation: Icon Rail

56px wide vertical bar on the left edge of the window. Background: `surface0` (distinct from page content `base`).

### Icons (top to bottom)

| Position | Icon | Tooltip | Action |
|----------|------|---------|--------|
| Top | Home/dashboard | "Dashboard" | Switch to Dashboard page |
| | Gear | "Settings" | Switch to Settings page |
| | Info circle | "About" | Switch to Info page |
| | File/document | "Error Log" | Switch to Log page |
| Bottom (pinned) | Door/exit | "Exit" | Show exit confirmation dialog |

### Visual states

- **Active**: 3px accent-colored left edge bar + brighter icon color
- **Hover**: background lightens to `surface2`
- **Disabled**: dimmed icon color (used during first-launch disclaimer)
- **Notification badge**: 6px accent-colored dot in top-right corner of icon (used on Settings icon when update available)

### Implementation

- Icons drawn via QPainter (lines, circles, rects) — no icon library dependency
- Rail is a custom QWidget with fixed 56px width
- Clicking an icon calls `QStackedWidget.setCurrentIndex()`
- Exit icon triggers confirmation dialog instead of page switch
- **Window title updates per page**: "Maestro - Dashboard", "Maestro - Settings", "Maestro - About", "Maestro - Error Log". Title updates when page switches.
- **Window icon**: loaded from `assets/icon.png` on startup (swallows errors if missing), set via `setWindowIcon()`

---

## First-Launch Disclaimer Flow

1. App starts, checks `disclaimer_accepted` in config (default: `false`)
2. If `false`: QStackedWidget shows the Info page with Accept/Reject buttons visible
3. All other sidebar icons (Dashboard, Settings, Log) are disabled/grayed out
4. **Accept**: saves `disclaimer_accepted: true` to config, enables all icons, navigates to Dashboard
5. **Reject**: calls `QApplication.quit()`
6. Subsequent launches: go straight to Dashboard

---

## Page 0: Dashboard

Two-column layout: fixed 400px left column + flexible right column.

### Left Column (400px, scrollable)

Three surface-card sections stacked vertically:

#### Section 1: Import

- URL text input + Import button (primary) on one row
- Info icon (i) beside Import button — tooltip: "Paste a YouTube link to download and convert to MIDI"
- Isolate piano: modern ToggleSwitch (disabled when demucs model not installed, tooltip explains why)
- Status label (hidden when idle, shows progress/success/error during import)
- Imported songs auto-appear in song list after completion

#### Section 2: Game Settings

- **Game**: dropdown (Heartopia / Where Winds Meet)
- **Keys**: dropdown (22-key, 15-double, 15-triple, Conga, Xylophone) — hidden for WWM
- **Sharps**: dropdown (skip / snap) — visible only for 15-key layouts
- **Transpose to range**: ToggleSwitch. When toggled, song list dynamically recalculates compatibility (re-fires `note_compatibility_requested` with transpose flag)
- **Note Preview**: ToggleSwitch. When ON, piano roll appears below Section 3

#### Section 3: Now Playing / Transport

- Error label (red, hidden by default, shown when errors occur — above song name)
- Song name (or "No song loaded")
- Progress bar: `0:00 ▓▓▓▓▓░░ 3:45` (thin transport style)
- Status line below progress bar: "Stopped" / "Playing" / "Starting in 3..." / "Finished" on left, last key pressed `[G]` on right
- Speed slider: range 0.5x to 2.0x, snaps to 0.1 increments (16 discrete stops), displays current value
- Play button (primary accent) + Stop button (secondary)
- Favorite star (ghost)

#### Section 4: Piano Roll (conditional)

- Only visible when Note Preview toggle is ON
- PianoRollWidget with lookahead selector (2/5/10 sec)

### Right Column (flexible)

- Header row: Filter text input (stretch) + Refresh button (visible, not ghost)
- Song list: SongListWidget with custom delegate (rich two-line items, accent bars, stars, metadata)
- **Double-click to play**: double-clicking a song in the list triggers Play (same as clicking Play button). Existing `song_double_clicked` signal preserved.
- Dynamic compatibility: when key layout or transpose changes, compatibility recalculates for selected song

---

## Page 1: Settings

Four surface-card sections:

### Library Card (top)

- Current folder path displayed (truncated with tooltip for full path)
- Song count: "42 songs loaded"
- Browse button to change folder (opens QFileDialog)
- **On folder change**: clears validation cache, triggers fresh validation scan, refreshes song list, emits `folder_changed` signal

### Appearance Card

- **Dark Theme**: ToggleSwitch (default ON)
- **Start in Full Screen**: ToggleSwitch (default OFF). OFF = opens at 80% of screen. ON = `showMaximized()`
- **Auto-minimize on Play**: ToggleSwitch (default ON). When ON, window minimizes when playback starts on primary monitor. Skipped on secondary monitors.

### Hotkeys Card

- Three rows: Play, Stop, Panic
- Each row: action label + key badge display + Bind button (ghost)
- Press-to-bind with `grabKeyboard()` for key capture
- **Conflict resolution dialog**: when binding a key already used by another action, a QMessageBox asks "This key is already bound to [action]. Replace?" — Yes swaps the binding, No cancels. Same behavior as current implementation.

### Piano Isolation Card

- Description paragraph: "Piano isolation uses Demucs, an AI model that separates piano audio from a mixed track before transcribing to MIDI. This improves accuracy for songs with vocals or other instruments."
- Model size: ~1 GB
- Location: ~/.maestro/models/
- Status: "Not installed" or "Installed" (green)
- Download/Remove button
- Progress bar shown during download

### Updates Card

- **Check on launch**: ToggleSwitch (default ON)
- Status line: "Up to date (vX.X.X)" / "Update available! vX.X.X [View Release]" / "Checking... [progress bar]" / "Auto-check disabled"
- Check Now button (always available)
- When update is available: notification badge (6px accent dot) appears on Settings gear icon in the rail

---

## Page 2: Info (About + Disclaimer)

### About Card

- Centered layout: app name, version (from APP_VERSION), description, author
- Ko-fi support button (primary) — opens browser

### Disclaimer Card

- Scrollable read-only QTextEdit with full disclaimer text
- **Normal state** (after first launch): no buttons, read-only reference
- **First-launch state** (`disclaimer_accepted: false`): "Please read and accept to continue." message + Accept (primary) and Reject (secondary) buttons at bottom

---

## Page 3: Error Log

### Header Row

- Page title "ERROR LOG"
- Open in Editor button — opens log file in OS default text editor (existing `open_log_file()`)
- Refresh Log button

### Log Viewer

- Read-only QTextEdit with monospace font
- Background: `surface0`
- Auto-reads log file from disk every time the page is navigated to (auto-refresh on page show)
- Refresh button re-reads from disk while staying on the page
- Auto-scrolls to bottom on every load/refresh
- Empty state: "No log entries" in subdued text if log file doesn't exist or is empty

---

## Exit Behavior

Triggered by: exit icon in rail OR window X close button.

### Confirmation Dialog

- Small centered modal dialog
- "Exit Maestro?" title
- "Are you sure you want to close the application?" body
- Cancel button (secondary) + Exit button (primary)
- Exit: stops playback, releases held keys, calls `QApplication.quit()`
- Cancel: returns to current page
- `closeEvent` on MainWindow overridden to show this dialog instead of closing immediately

---

## Modern Toggle Switch Component

Reusable custom widget used across Dashboard and Settings pages.

### Usage locations (6 total)

- Dashboard: Isolate Piano, Transpose to Range, Note Preview
- Settings: Dark Theme, Start Full Screen, Auto-minimize on Play, Check on Launch

### Specs

- Size: 40px wide x 22px tall
- Track: rounded rectangle (11px radius)
- Thumb: 16px circle, 3px inset from edges
- OFF: track = `surface_active`, thumb = `overlay`
- ON: track = `accent`, thumb = `base`
- Animated: QPropertyAnimation ~150ms ease-in-out on thumb position
- Hover: OFF → `surface_hover` track, ON → `accent_hover` track
- Disabled: muted colors, no hover effect
- Signal: `toggled(bool)` — same interface as QCheckBox

---

## Speed Slider Change

- Range: 0.5x to 2.0x (was 0.25x to 1.5x)
- Snaps to 0.1 increments (16 discrete stops)
- QSlider with range 5-20, value mapped to float (value / 10)
- Display: "1.0x" label beside slider

---

## Config Changes

### New keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `disclaimer_accepted` | bool | `false` | Whether user accepted the disclaimer |
| `start_fullscreen` | bool | `false` | Open window maximized |
| `check_updates_on_launch` | bool | `true` | Auto-check GitHub releases on startup |
| `auto_minimize_on_play` | bool | `true` | Minimize window when playback starts |

### Modified keys

| Key | Change |
|-----|--------|
| `speed` | Range changes from 0.25-1.5 to 0.5-2.0, validation updated |

---

## Files Created

| File | Purpose |
|------|---------|
| `gui/icon_rail.py` | IconRail widget — 56px nav bar with QPainter icons, active states, notification badge |
| `gui/toggle_switch.py` | ToggleSwitch widget — animated 40x22 toggle, replaces QCheckBox for on/off |
| `gui/pages/dashboard.py` | Dashboard page — two-column layout (import + settings + transport | song list) |
| `gui/pages/settings_page.py` | Settings page — library, appearance, hotkeys, piano isolation, updates |
| `gui/pages/info_page.py` | Info page — about + disclaimer with first-launch accept/reject |
| `gui/pages/log_page.py` | Log page — built-in log viewer with refresh + open in editor |
| `gui/exit_dialog.py` | Exit confirmation dialog |

## Files Modified

| File | Changes |
|------|---------|
| `gui/main_window.py` | Major rewrite: remove menu bar, add IconRail + QStackedWidget, wire page switching, override closeEvent |
| `gui/theme.py` | Add QSS for ToggleSwitch, IconRail styling |
| `gui/__init__.py` | Update exports |
| `config.py` | Add new config keys, update speed validation range |
| `main.py` | Update startup flow for disclaimer check, wire new signals |

## Files Removed

| File | Reason |
|------|--------|
| `gui/about_dialog.py` | Content moves to Info page |
| `gui/update_banner.py` | Update status moves to Settings page |

## Files Unchanged

| File | Reason |
|------|--------|
| `gui/song_list.py` | Song list delegate and widget stay as-is |
| `gui/piano_roll.py` | Piano roll widget stays as-is |
| `gui/controls_panel.py` | Play/Stop/Favorite buttons stay as-is (Refresh moves out) |
| `gui/progress_panel.py` | Now Playing panel stays as-is |
| `gui/import_panel.py` | Import panel stays as-is (checkbox → toggle is a swap) |
| `gui/splash.py` | Splash screen stays as-is |
| `gui/workers.py` | Worker threads stay as-is |
| `gui/signals.py` | May need minor additions for page navigation |
| `gui/constants.py` | Unchanged |
| `gui/utils.py` | Unchanged |
