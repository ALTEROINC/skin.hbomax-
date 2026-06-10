#!/usr/bin/env python3
import hashlib

with open("addon.xml", "r") as f:
    addon_content = f.read().strip()

addons_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    "<addons>\n"
    + addon_content
    + "\n</addons>\n"
)

with open("site/addons.xml", "w") as f:
    f.write(addons_xml)

md5 = hashlib.md5(addons_xml.encode("utf-8")).hexdigest()
with open("site/addons.xml.md5", "w") as f:
    f.write(md5)

print(f"Generated addons.xml (md5: {md5})")
