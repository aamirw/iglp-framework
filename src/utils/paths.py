from pathlib import Path

PROJECT_PATH = Path(__file__).parents[2]
DATA_PATH = PROJECT_PATH / "data"
DATA_PATH.mkdir(parents=False, exist_ok=True)
