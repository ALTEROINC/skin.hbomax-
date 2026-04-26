# Debug Workflow

## Overlay

- Press `D` to toggle the in-skin debug overlay.
- The overlay shows the active window, focused control, focused item art, widget path, resolution, FPS, CPU, memory, and Kodi version.

## Reload

- Press `F5` to run `ReloadSkin()`.

## Kodi Logs

- Windows: `%APPDATA%\Kodi\kodi.log`
- macOS: `~/Library/Logs/kodi.log`
- Linux: `~/.kodi/temp/kodi.log`

## Common Error Patterns

- `Error loading skin file`
- `Unable to load texture`
- `Unknown font`
- `invalid include`
- `ActivateWindow(...) failed`
- `RunScript(...)` failures

## First Load Checklist

- Verify Inter font files exist in `fonts/`
- Verify `addon.xml` loads and dependency IDs resolve
- Verify `xml/Font.xml` loads without font errors
- Verify `colors/defaults.xml` resolves all referenced colors
- Verify Home loads hero art, clearlogos, and shelf posters
- Verify focus movement in nav, shelves, dialogs, and playback OSD
- Verify `D` toggles the debug overlay
- Verify `F5` reloads the skin
