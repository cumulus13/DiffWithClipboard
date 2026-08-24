#!/usr/bin/env python3
# File: DiffWithClipboard.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-08-22
# Description: Diff the current file (or selection) against the clipboard,
#              using any configured external diff tool.
# License: MIT

import os
import shutil
import subprocess
import tempfile

import sublime
import sublime_plugin

SETTINGS_FILE = "DiffWithClipboard.sublime-settings"

# ---------------------------------------------------------------------------
# Tool registry
#   type: "gui"  -> plain fire-and-forget subprocess.Popen
#         "cli"  -> run, capture stdout, show result in a new Sublime tab
#         "tui"  -> needs a real terminal (vimdiff, sdiff); spawned in one
#   unix/win: candidate executables. Absolute paths are checked with
#             os.path.exists; bare names are resolved with shutil.which.
#   args: argument template, {left} / {right} are substituted.
# ---------------------------------------------------------------------------
TOOLS = {
    "delta":        {"type": "cli", "unix": ["delta"], "win": ["delta.exe"],
                      "args": ["{left}", "{right}"]},
    "diff":         {"type": "cli", "unix": ["diff"], "win": ["diff.exe"],
                      "args": ["-u", "{left}", "{right}"]},
    "sdiff":        {"type": "tui", "unix": ["sdiff"], "win": [],
                      "args": ["{left}", "{right}"]},
    "vimdiff":      {"type": "tui", "unix": ["vimdiff"], "win": ["vim.exe", "gvim.exe"],
                      "args": ["-d", "{left}", "{right}"]},
    "meld":         {"type": "gui", "unix": ["meld"],
                      "win": [r"C:\Program Files\Meld\Meld.exe",
                              r"C:\Program Files (x86)\Meld\Meld.exe"],
                      "args": ["{left}", "{right}"]},
    "kdiff3":       {"type": "gui", "unix": ["kdiff3"],
                      "win": [r"C:\Program Files\KDiff3\kdiff3.exe"],
                      "args": ["{left}", "{right}"]},
    "diffmerge":    {"type": "gui", "unix": ["diffmerge"],
                      "win": [r"C:\Program Files\SourceGear\DiffMerge\DiffMerge.exe"],
                      "args": ["{left}", "{right}"]},
    "kompare":      {"type": "gui", "unix": ["kompare"], "win": [],
                      "args": ["{left}", "{right}"]},
    "tkdiff":       {"type": "gui", "unix": ["tkdiff"], "win": [],
                      "args": ["{left}", "{right}"]},
    "bcompare":     {"type": "gui", "unix": ["bcompare"],
                      "win": [r"C:\Program Files\Beyond Compare 4\BCompare.exe"],
                      "args": ["{left}", "{right}"]},
    "filemerge":    {"type": "gui", "unix": ["opendiff"], "win": [],
                      "args": ["{left}", "{right}"]},
    "kaleidoscope": {"type": "gui", "unix": ["ksdiff"], "win": [],
                      "args": ["{left}", "{right}"]},
    "winmerge":     {"type": "gui", "unix": [],
                      "win": [r"C:\Program Files\WinMerge\WinMergeU.exe",
                              r"C:\Program Files (x86)\WinMerge\WinMergeU.exe"],
                      "args": ["{left}", "{right}"]},
    "amerge":       {"type": "gui", "unix": ["compare"],
                      "win": [r"C:\Program Files\Araxis\Araxis Merge\Compare.exe"],
                      "args": ["{left}", "{right}"]},
}

DEFAULT_TOOL = "meld"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_settings():
    return sublime.load_settings(SETTINGS_FILE)


def resolve_tool_executable(alias, settings):
    """Return an absolute path to the executable for `alias`, or None."""
    if alias not in TOOLS:
        return None

    tool_paths = settings.get("tool_paths", {}) or {}
    override = tool_paths.get(alias)
    if override and os.path.exists(override):
        return override

    info = TOOLS[alias]
    candidates = info["win"] if sublime.platform() == "windows" else info["unix"]
    for c in candidates:
        if os.path.isabs(c):
            if os.path.exists(c):
                return c
        else:
            found = shutil.which(c)
            if found:
                return found
    return None


def parse_simple_yaml_key(path, key):
    """Best-effort extraction of `key: value` from a small YAML file.

    Tries a real YAML parser first (if the environment happens to have
    one); falls back to a naive line parser so this works with Sublime's
    stock Python and no extra dependencies.
    """
    try:
        import yaml  # noqa: local import, optional dependency
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict) and key in data and data[key]:
            return str(data[key]).strip()
    except ImportError:
        pass
    except Exception:
        pass

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith(key + ":"):
                    val = line.split(":", 1)[1].strip()
                    val = val.strip('"').strip("'")
                    if val:
                        return val
    except Exception:
        pass
    return None


def find_project_diff_tool(view, settings):
    """Look for pt.yml / pt.yaml (project root, then the file's folder)."""
    config_filenames = settings.get("config_filenames", ["pt.yml", "pt.yaml"])

    dirs = []
    window = view.window()
    if window:
        dirs.extend(window.folders())
    file_name = view.file_name()
    if file_name:
        dirs.append(os.path.dirname(file_name))

    seen = set()
    for d in dirs:
        d = os.path.normpath(d)
        if not d or d in seen or not os.path.isdir(d):
            continue
        seen.add(d)
        for fn in config_filenames:
            p = os.path.join(d, fn)
            if os.path.isfile(p):
                tool = parse_simple_yaml_key(p, "diff_tool")
                if tool:
                    return tool
    return None


def resolve_tool_alias(view, settings, explicit_tool=None):
    """Priority: explicit arg > pt.yml/pt.yaml > settings > default."""
    if explicit_tool:
        return explicit_tool.strip().lower()
    project_tool = find_project_diff_tool(view, settings)
    if project_tool:
        return project_tool.strip().lower()
    return (settings.get("diff_tool") or DEFAULT_TOOL).strip().lower()


def build_args(alias, settings, left, right):
    template = TOOLS[alias]["args"]
    args = [a.format(left=left, right=right) for a in template]
    extra = (settings.get("extra_args", {}) or {}).get(alias, [])
    return args + list(extra)


def run_gui(exe, args):
    subprocess.Popen([exe] + args)


def run_cli_capture(exe, args, window, title):
    try:
        proc = subprocess.run([exe] + args, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=30)
        output = proc.stdout.decode("utf-8", errors="replace")
    except Exception as e:
        output = "Failed to run '{}':\n{}".format(exe, e)

    v = window.new_file()
    v.set_scratch(True)
    v.set_name(title)
    v.run_command("append", {"characters": output or "(no differences)"})
    try:
        v.assign_syntax("Packages/Diff/Diff.sublime-syntax")
    except Exception:
        pass


def run_tui(exe, args, settings):
    plat = sublime.platform()
    if plat == "windows":
        quoted = " ".join('"{}"'.format(a) for a in args)
        cmd = 'start "" cmd /k ""{}" {}"'.format(exe, quoted)
        subprocess.Popen(cmd, shell=True)
    elif plat == "osx":
        joined = " ".join('"{}"'.format(a) for a in args)
        script = 'tell application "Terminal" to do script "{} {}"'.format(exe, joined)
        subprocess.Popen(["osascript", "-e", script])
    else:
        terminals = settings.get(
            "linux_terminals",
            ["x-terminal-emulator", "gnome-terminal", "konsole", "xfce4-terminal", "xterm"],
        )
        for t in terminals:
            path = shutil.which(t)
            if path:
                subprocess.Popen([path, "-e", exe] + args)
                return
        sublime.error_message(
            "DiffWithClipboard: no terminal emulator found to run '{}'.\n"
            "Install one of: {}".format(exe, ", ".join(terminals))
        )


def dispatch_diff(alias, exe, args, window, settings, title):
    kind = TOOLS[alias]["type"]
    if kind == "gui":
        run_gui(exe, args)
    elif kind == "cli":
        run_cli_capture(exe, args, window, title)
    elif kind == "tui":
        run_tui(exe, args, settings)


def write_temp(content, ext, suffix_tag):
    with tempfile.NamedTemporaryFile(
        mode="w+", delete=False, suffix="_{}{}".format(suffix_tag, ext), encoding="utf-8"
    ) as f:
        f.write(content)
        return f.name


def tool_not_found_message(alias):
    return (
        "Diff tool '{0}' was not found.\n\n"
        "Install it, make sure it's on PATH, or set an explicit path in\n"
        "DiffWithClipboard.sublime-settings under:\n"
        '  "tool_paths": {{ "{0}": "C:\\\\path\\\\to\\\\tool.exe" }}'
    ).format(alias)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
class DiffCurrentWithClipboardCommand(sublime_plugin.TextCommand):
    """Diff the whole current file (as saved on disk) against the clipboard."""

    def run(self, edit, tool=None):
        settings = get_settings()

        file_path = self.view.file_name()
        if not file_path or not os.path.exists(file_path):
            sublime.error_message("File must be saved to disk first to pass the real path.")
            return

        if self.view.is_dirty():
            self.view.run_command("save")

        clipboard_content = sublime.get_clipboard()
        if not clipboard_content.strip():
            sublime.status_message("Clipboard is empty. Cannot diff.")
            return

        alias = resolve_tool_alias(self.view, settings, tool)
        exe = resolve_tool_executable(alias, settings)
        if not exe:
            sublime.error_message(tool_not_found_message(alias))
            return

        ext = os.path.splitext(file_path)[1] or ".txt"
        clip_temp_path = write_temp(clipboard_content, ext, "clipboard")

        args = build_args(alias, settings, file_path, clip_temp_path)
        title = "Diff: {} <-> clipboard".format(os.path.basename(file_path))

        self.view.set_status("diff_with_clipboard", "[ {} launching... ]".format(alias))
        try:
            dispatch_diff(alias, exe, args, self.view.window(), settings, title)
            self.view.set_status("diff_with_clipboard", "[ {} opened ]".format(alias))
        except Exception as e:
            sublime.error_message("Failed to launch {}:\n{}".format(alias, e))
        finally:
            sublime.set_timeout(lambda: self.view.erase_status("diff_with_clipboard"), 3000)


class DiffSelectionWithClipboardCommand(sublime_plugin.TextCommand):
    """Diff the current selection against the clipboard."""

    def run(self, edit, tool=None):
        settings = get_settings()

        regions = [r for r in self.view.sel() if not r.empty()]
        if not regions:
            sublime.status_message("No text selected. Cannot diff.")
            return

        selected_text = "\n".join(self.view.substr(r) for r in regions)

        clipboard_content = sublime.get_clipboard()
        if not clipboard_content.strip():
            sublime.status_message("Clipboard is empty. Cannot diff.")
            return

        alias = resolve_tool_alias(self.view, settings, tool)
        exe = resolve_tool_executable(alias, settings)
        if not exe:
            sublime.error_message(tool_not_found_message(alias))
            return

        file_path = self.view.file_name()
        ext = os.path.splitext(file_path)[1] if file_path else ".txt"
        ext = ext or ".txt"

        left_temp_path = write_temp(selected_text, ext, "selection")
        clip_temp_path = write_temp(clipboard_content, ext, "clipboard")

        args = build_args(alias, settings, left_temp_path, clip_temp_path)
        title = "Diff: selection <-> clipboard"

        self.view.set_status("diff_with_clipboard", "[ {} launching... ]".format(alias))
        try:
            dispatch_diff(alias, exe, args, self.view.window(), settings, title)
            self.view.set_status("diff_with_clipboard", "[ {} opened ]".format(alias))
        except Exception as e:
            sublime.error_message("Failed to launch {}:\n{}".format(alias, e))
        finally:
            sublime.set_timeout(lambda: self.view.erase_status("diff_with_clipboard"), 3000)

    def is_enabled(self):
        return any(not r.empty() for r in self.view.sel())

    def is_visible(self):
        return any(not r.empty() for r in self.view.sel())


class DiffWithClipboardSetToolCommand(sublime_plugin.WindowCommand):
    """Quick panel to pick and persist the default diff tool."""

    def run(self):
        aliases = sorted(TOOLS.keys())
        settings = get_settings()
        current = (settings.get("diff_tool") or DEFAULT_TOOL).strip().lower()

        items = []
        for alias in aliases:
            marker = "  (current)" if alias == current else ""
            items.append("{} [{}]{}".format(alias, TOOLS[alias]["type"], marker))

        def on_done(index):
            if index == -1:
                return
            chosen = aliases[index]
            user_settings = sublime.load_settings(SETTINGS_FILE)
            user_settings.set("diff_tool", chosen)
            sublime.save_settings(SETTINGS_FILE)
            sublime.status_message("DiffWithClipboard: default tool set to '{}'.".format(chosen))

        self.window.show_quick_panel(items, on_done)
