from json import loads
from pathlib import Path

import aiofiles

BASE_PATH = Path(__file__).parent


async def load_template(file_path: str):
    async with aiofiles.open(file_path, "rb") as fp:
        return loads(await fp.read())
