from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def run(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)


class AsyncCommand(ABC):
    @abstractmethod
    async def run(self, *args, **kwargs):
        pass

    async def __call__(self, *args, **kwargs):
        return await self.run(*args, **kwargs)
