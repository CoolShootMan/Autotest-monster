
import yaml
import os

path = r"d:\new test\Autotest-moster\test_case\UI\Test_Katana\Katana_curator_smoke.yaml"
try:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        print(f"Loaded {len(data)} items.")
        print("Keys:", list(data.keys()))
except Exception as e:
    print(f"Error: {e}")
