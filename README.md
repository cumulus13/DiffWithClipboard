# DiffWithClipboard

A Sublime Text plugin that diffs the current file, or just the current
selection, against the contents of the clipboard — using whichever
external diff tool you prefer.

## Features

- **Diff current file** with clipboard (uses the real path on disk on the
  left side; auto-saves the file first if it's dirty).
- **Diff selection** with clipboard (works on unsaved buffers too).
- **Any diff tool**: GUI tools (Meld, KDiff3, WinMerge, Beyond Compare, ...),
  CLI tools (`diff`, `delta` — output opens in a new Sublime tab), and TUI
  tools (`vimdiff`, `sdiff` — opened in a terminal window).
- **Per-project override** via a `pt.yml` / `pt.yaml` file.
- **Command palette / menu / keybindings / right-click context menu.**

## Commands

| Command | Palette name | Default keybinding |
|---|---|---|
| `diff_current_with_clipboard` | Diff With Clipboard: Diff Current File | `Ctrl+Alt+D` |
| `diff_selection_with_clipboard` | Diff With Clipboard: Diff Selection | `Ctrl+Alt+Shift+D` |
| `diff_with_clipboard_set_tool` | Diff With Clipboard: Set Default Tool | — |

Both diff commands accept an optional `tool` argument, so you can bind a
key to a specific tool regardless of your configured default:

```json
{ "keys": ["ctrl+alt+m"], "command": "diff_current_with_clipboard", "args": {"tool": "winmerge"} }
```

## Choosing a diff tool

Resolution order (first match wins):

1. `"tool": "..."` argument passed to the command (keybinding/menu/palette).
2. `diff_tool:` key in a `pt.yml` / `pt.yaml` file found in a project
   folder or the current file's folder.
3. `"diff_tool"` in `DiffWithClipboard.sublime-settings`.
4. Built-in default: `meld`.

`pt.yml` example:

```yaml
diff_tool: winmerge
```

### Supported tools

| Tool | Alias (config value) | Platform | Type | License | Home Page / Download |
|------|-----------------------|----------|------|---------|-----------------------|
| **Delta (git diff)** | `delta` | Linux, macOS, Windows | CLI | Open Source | <https://dandavison.github.io/delta/> |
| **GNU diff** | `diff` | Linux, macOS, Windows | CLI | Open Source | <https://www.gnu.org/software/diffutils/> |
| **GNU sdiff** | `sdiff` | Linux, macOS | CLI (TUI) | Open Source | <https://www.gnu.org/software/diffutils/> |
| **vimdiff** | `vimdiff` | Linux, macOS, Windows | CLI (TUI) | Open Source | <https://www.vim.org/> |
| **Meld** ⭐ | `meld` | Linux, macOS, Windows | GUI | Open Source | <https://meldmerge.org> |
| **KDiff3** | `kdiff3` | Linux, macOS, Windows | GUI | Open Source | <https://invent.kde.org/sdk/kdiff3> |
| **DiffMerge** | `diffmerge` | Linux, macOS, Windows | GUI | Freeware | <https://sourcegear.com/diffmerge/> |
| **Kompare** | `kompare` | Linux | GUI | Open Source | <https://apps.kde.org/kompare/> |
| **TkDiff** | `tkdiff` | Linux, macOS, Windows | GUI | Open Source | <https://sourceforge.net/projects/tkdiff/> |
| **Beyond Compare** ⭐ | `bcompare` | Linux, macOS, Windows | GUI + CLI | Commercial | <https://www.scootersoftware.com/> |
| **FileMerge (Xcode)** | `filemerge` | macOS | GUI | Free (Xcode) | <https://developer.apple.com/xcode/> |
| **Kaleidoscope** | `kaleidoscope` | macOS | GUI | Commercial | <https://kaleidoscope.app/> |
| **WinMerge** | `winmerge` | Windows | GUI | Open Source | <https://winmerge.org> |
| **Araxis Merge** | `amerge` | Windows, macOS | GUI | Commercial | <https://www.araxis.com/merge> |

- **GUI** tools are launched directly against two files.
- **CLI** tools (`diff`, `delta`) run headless; their output is captured and
  opened in a new, unsaved Sublime tab.
- **TUI** tools (`vimdiff`, `sdiff`) need an interactive terminal, so the
  plugin opens one for you (`cmd.exe` on Windows, Terminal.app on macOS,
  the first available emulator from `linux_terminals` on Linux).

If a tool isn't found automatically (not on `PATH`, or installed somewhere
non-standard), point straight at it in settings:

```json
"tool_paths": {
    "winmerge": "D:\\Tools\\WinMerge\\WinMergeU.exe"
}
```

## Settings reference

`Preferences > Package Settings > DiffWithClipboard > Settings`

| Key | Type | Default | Description |
|---|---|---|---|
| `diff_tool` | string | `"meld"` | Default tool alias, see table above. |
| `tool_paths` | object | `{}` | Explicit executable path per alias. |
| `config_filenames` | array | `["pt.yml", "pt.yaml"]` | Project config filenames to search for. |
| `extra_args` | object | `{}` | Extra CLI args appended per alias, e.g. `{"diff": ["-w"]}`. |
| `linux_terminals` | array | see settings file | Terminal emulators tried in order for TUI tools on Linux. |

## Installation

1. Copy this folder into your Sublime Text `Packages` directory, or
   `git clone` it there directly:
   - Windows: `%APPDATA%\Sublime Text\Packages\DiffWithClipboard`
   - macOS: `~/Library/Application Support/Sublime Text/Packages/DiffWithClipboard`
   - Linux: `~/.config/sublime-text/Packages/DiffWithClipboard`
2. Restart Sublime Text (or run `View > Show Console` and check for
   plugin load errors).
3. Install your preferred diff tool and confirm it's on `PATH`, or set
   `tool_paths` as above.

## Notes / limitations

- Clipboard (and selection) content is written to a temporary file per
  diff; these aren't deleted automatically afterwards (the launched tool
  may still be reading them) — your OS temp-directory cleanup handles
  that over time.
- `diff_current_with_clipboard` requires the file to exist on disk (it
  auto-saves dirty buffers first); `diff_selection_with_clipboard` works
  on unsaved buffers since it only needs the selected text.
- `filemerge` (`opendiff`) and `kaleidoscope` (`ksdiff`) are macOS-only;
  `kompare` is Linux-only — they simply won't resolve to an executable on
  other platforms.

## License

MIT — see [LICENSE](LICENSE).

---

## 👤 Author
        
[Hadi Cahyadi](mailto:cumulus13@gmail.com)
    

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/cumulus13)

[![Donate via Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/cumulus13)
 
[Support me on Patreon](https://www.patreon.com/cumulus13)