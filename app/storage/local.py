import aiofiles
import os
from pathlib import Path

from app.storage.base import BaseStorage


class LocalStorage(BaseStorage):

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, file_bytes: bytes, destination: str) -> str:
        full_path = self.base_dir / destination
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file_bytes)
        return str(destination)

    async def delete(self, path: str) -> None:
        full_path = self.base_dir / path
        if full_path.exists():
            full_path.unlink()

    async def get_url(self, path: str) -> str:
        return str(self.base_dir / path)


def get_storage() -> LocalStorage:
    from app.core.config import settings
    return LocalStorage(base_dir=settings.LOCAL_UPLOAD_DIR)