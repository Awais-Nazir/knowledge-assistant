from abc import ABC, abstractmethod


class BaseStorage(ABC):
    @abstractmethod
    async def save(
        self,
        file_bytes: bytes,
        destination: str,
    ) -> str:
        """Save file and return the storage path."""
        ...

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete file at given path."""
        ...

    @abstractmethod
    async def get_url(self, path: str) -> str:
        """Return a URL or path to access the file."""
        ...
