import json
from pathlib import Path

NB_PATH = Path("phobert_finetune.ipynb")

with NB_PATH.open("r", encoding="utf-8-sig") as f:
    nb = json.load(f)

for cell in nb.get("cells", []):
    cid = cell.get("id", "")

    if cid == "#VSC-dce55ed3":
        src = "".join(cell.get("source", []))
        src = src.replace("STRICT_MANUAL_ONLY = False", "STRICT_MANUAL_ONLY = True")
        cell["source"] = [line + "\n" for line in src.split("\n")[:-1]] + ([src.split("\n")[-1]] if src and not src.endswith("\n") else [])

    if cid == "#VSC-aa3bc17c":
        src = "".join(cell.get("source", []))
        src = src.replace(
            "STRICT_MANUAL_ONLY = False  # Cho phép train cả nhãn ngoài manual",
            "STRICT_MANUAL_ONLY = True  # Fixed: chi train nhan manual",
        )
        cell["source"] = [line + "\n" for line in src.split("\n")[:-1]] + ([src.split("\n")[-1]] if src and not src.endswith("\n") else [])

    if cid == "#VSC-1d9009e9":
        cell["source"] = [
            "from sklearn.model_selection import train_test_split\n",
            "import collections\n",
            "\n",
            "# ===== Fixed split settings (do not change) =====\n",
            "RANDOM_STATE = 42\n",
            "EXPECTED_TEST_SUPPORT = {'positive': 70, 'neutral': 80, 'negative': 21}\n",
            "\n",
            "# Chia 70/15/15 voi stratify de giu ty le class\n",
            "X = df_labeled['text_clean'].values\n",
            "y = df_labeled['label'].values\n",
            "\n",
            "X_train, X_temp, y_train, y_temp = train_test_split(\n",
            "    X, y, test_size=0.30, random_state=RANDOM_STATE, stratify=y\n",
            ")\n",
            "X_val, X_test, y_val, y_test = train_test_split(\n",
            "    X_temp, y_temp, test_size=0.50, random_state=RANDOM_STATE, stratify=y_temp\n",
            ")\n",
            "\n",
            "print(f'Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}')\n",
            "print(f'Random state fixed: {RANDOM_STATE}')\n",
            "\n",
            "ID2LABEL = {0: 'positive', 1: 'neutral', 2: 'negative'}\n",
            "split_dist = {}\n",
            "for split_name, labels in [('Train', y_train), ('Val', y_val), ('Test', y_test)]:\n",
            "    cnt = collections.Counter(labels)\n",
            "    named = {ID2LABEL[k]: v for k, v in sorted(cnt.items())}\n",
            "    split_dist[split_name] = named\n",
            "    print(f'  {split_name}: ' + ', '.join(f'{k}={v}' for k, v in named.items()))\n",
            "\n",
            "# ===== Sanity check before training =====\n",
            "test_support = split_dist['Test']\n",
            "if test_support != EXPECTED_TEST_SUPPORT:\n",
            "    raise ValueError(\n",
            "        'SANITY CHECK FAILED: Test support mismatch. '\n",
            "        f'Expected {EXPECTED_TEST_SUPPORT}, got {test_support}. '\n",
            "        'Do not compare metrics across runs when support differs.'\n",
            "    )\n",
            "\n",
            "print('✅ SANITY CHECK PASSED: Test support = 70/80/21 (positive/neutral/negative)')\n",
        ]

with NB_PATH.open("w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Updated notebook guards successfully.")
