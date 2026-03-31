from __future__ import annotations

import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
INIT_PY = ROOT / "nokiao_copilot_chat" / "__init__.py"
MARKER = "# AUTO-REGISTER-JS-CHUNKS"


def main() -> None:
    if not INIT_PY.exists():
        raise FileNotFoundError(f"Missing generated file: {INIT_PY}")

    content = INIT_PY.read_text(encoding="utf-8")
    if MARKER in content:
        return

    snippet = f"""

{MARKER}
for _asset in _os.listdir(_current_path):
    if _asset in ('{{}}.js'.format(package_name), '{{}}.js.map'.format(package_name), 'proptypes.js'):
        continue
    if _asset.endswith('.js'):
        _js_dist.append({{
            'relative_package_path': _asset,
            'namespace': package_name,
            'dynamic': True
        }})
    elif _asset.endswith('.js.map'):
        _js_dist.append({{
            'relative_package_path': _asset,
            'namespace': package_name,
            'dynamic': True
        }})
"""

    anchor = "_css_dist = []"
    if anchor not in content:
        raise RuntimeError(f"Expected anchor not found in {INIT_PY}")

    content = content.replace(anchor, snippet + "\n\n" + anchor, 1)
    INIT_PY.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
