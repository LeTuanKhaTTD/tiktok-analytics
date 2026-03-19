import json
from pathlib import Path

p = Path("phobert_finetune.ipynb")
nb = json.loads(p.read_text(encoding="utf-8-sig"))

for cell in nb.get("cells", []):
    src = cell.get("source", [])
    new_src = []
    for line in src:
        if "    STRICT_MANUAL_ONLY = False" in line:
            line = line.replace(
                "    STRICT_MANUAL_ONLY = False",
                "    STRICT_MANUAL_ONLY = True",
            )
        if "STRICT_MANUAL_ONLY = False  # Cho phép train cả nhãn ngoài manual" in line:
            line = line.replace(
                "STRICT_MANUAL_ONLY = False  # Cho phép train cả nhãn ngoài manual",
                "STRICT_MANUAL_ONLY = True  # Ưu tiên train nhãn thủ công để giảm nhiễu",
            )
        if 'TRAIN_PRESET = "stable"  # chọn: stable | negative_focus' in line:
            line = line.replace(
                'TRAIN_PRESET = "stable"  # chọn: stable | negative_focus',
                'TRAIN_PRESET = "negative_focus"  # chọn: stable | negative_focus',
            )
        new_src.append(line)
    cell["source"] = new_src

p.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("Notebook config updated and JSON normalized.")
