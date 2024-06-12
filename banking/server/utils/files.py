from json import loads
from pathlib import Path

BASE_PATH = Path(__file__).parent


def load_template(file_path: str):
    with open(file_path, "rb") as fp:
        return loads(fp.read())
