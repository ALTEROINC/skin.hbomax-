#!/usr/bin/env python3
import hashlib
import os
import re

ADDONS = [
    ("addon.xml", "skin.hbomax.dev"),
    ("repository.hbomaxdev/addon.xml", "repository.hbomaxdev"),
]


def read_addon(path, addon_id):
    with open(path, "r") as f:
        content = f.read().strip()
    m = re.search(r'id="%s"[^>]*version="([^"]+)"' % re.escape(addon_id), content)
    version = m.group(1) if m else "0.0.1"
    # Strip this file's own XML declaration line — a second <?xml ...?>
    # partway through the generated addons.xml is invalid XML and breaks
    # Kodi's repository update-checker parsing.
    body = "\n".join(
        line for line in content.splitlines()
        if not line.strip().startswith("<?xml")
    )
    return body, version


entries = []
zip_info = []
for path, addon_id in ADDONS:
    body, version = read_addon(path, addon_id)
    entries.append(body)
    zip_name = f"{addon_id}-{version}.zip"
    zip_path = f"site/{addon_id}/{zip_name}"
    zip_size = os.path.getsize(zip_path) if os.path.exists(zip_path) else 0
    zip_info.append((addon_id, version, zip_name, zip_size))

# Generate addons.xml
addons_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    "<addons>\n"
    + "\n".join(entries)
    + "\n</addons>\n"
)
with open("site/addons.xml", "w") as f:
    f.write(addons_xml)

# Generate addons.xml.md5
md5 = hashlib.md5(addons_xml.encode("utf-8")).hexdigest()
with open("site/addons.xml.md5", "w") as f:
    f.write(md5)

# Generate Apache-style index.html so Kodi can browse and find the zips
rows = []
for addon_id, version, zip_name, zip_size in zip_info:
    size_str = f"{zip_size // 1024}K" if zip_size else "-"
    rows.append(f'<a href="{addon_id}/{zip_name}">{addon_id}/{zip_name}</a>   {size_str}')
rows_html = "\n".join(rows)

index_html = f"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<html>
<head>
  <title>Index of /</title>
  <style>
    body {{ font-family: monospace; background: #0d1117; color: #e6edf3; padding: 20px; }}
    h1 {{ color: #fff; }}
    a {{ color: #79c0ff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    pre {{ font-size: 14px; }}
    hr {{ border-color: #30363d; }}
  </style>
</head>
<body>
<h1>Index of /</h1>
<pre><hr>
{rows_html}
<a href="addons.xml">addons.xml</a>
<a href="addons.xml.md5">addons.xml.md5</a>
<hr></pre>
<p style="color:#8b949e">First-time setup: install <code style="color:#79c0ff">repository.hbomaxdev</code> from zip once (add this page as a file source in Kodi, then Install from zip). After that, Kodi's Add-ons browser will auto-detect and install updates to the skin — no manual reinstall needed.</p>
</body>
</html>
"""
with open("site/index.html", "w") as f:
    f.write(index_html)

for addon_id, version, zip_name, zip_size in zip_info:
    size_str = f"{zip_size // 1024}K" if zip_size else "-"
    print(f"{addon_id}: {version} -> {zip_name} ({size_str})")
print(f"md5: {md5}")
print("Generated: addons.xml, addons.xml.md5, index.html")
