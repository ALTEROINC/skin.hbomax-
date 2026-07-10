#!/usr/bin/env python3
import hashlib
import os
import sys

# Read version and addon info from addon.xml
with open("addon.xml", "r") as f:
    addon_content = f.read().strip()

# Extract version for zip filename
version = None
for line in addon_content.splitlines():
    if 'version="' in line and 'id="skin.hbomax.dev"' in line:
        version = line.split('version="')[1].split('"')[0]
        break
if not version:
    import re
    m = re.search(r'version="([^"]+)"', addon_content)
    version = m.group(1) if m else "0.0.1"

zip_name = f"skin.hbomax.dev-{version}.zip"
zip_size = 0
zip_path = f"site/{zip_name}"
if os.path.exists(zip_path):
    zip_size = os.path.getsize(zip_path)

# Generate addons.xml (strip addon.xml's own XML declaration line first —
# a second <?xml ...?> partway through the document is invalid XML and
# breaks Kodi's repository update-checker parsing)
addon_body = "\n".join(
    line for line in addon_content.splitlines()
    if not line.strip().startswith("<?xml")
)
addons_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    "<addons>\n"
    + addon_body
    + "\n</addons>\n"
)
with open("site/addons.xml", "w") as f:
    f.write(addons_xml)

# Generate addons.xml.md5
md5 = hashlib.md5(addons_xml.encode("utf-8")).hexdigest()
with open("site/addons.xml.md5", "w") as f:
    f.write(md5)

# Generate Apache-style index.html so Kodi can browse and find the zip
size_str = f"{zip_size // 1024}K" if zip_size else "-"
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
<a href="{zip_name}">{zip_name}</a>   {size_str}
<a href="addons.xml">addons.xml</a>
<a href="addons.xml.md5">addons.xml.md5</a>
<hr></pre>
<p style="color:#8b949e">Add <code style="color:#79c0ff">https://alteroinc.github.io/skin.hbomax-/</code> as a file source in Kodi, then install from zip.</p>
</body>
</html>
"""
with open("site/index.html", "w") as f:
    f.write(index_html)

print(f"version:  {version}")
print(f"zip:      {zip_name} ({size_str})")
print(f"md5:      {md5}")
print("Generated: addons.xml, addons.xml.md5, index.html")
