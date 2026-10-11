from src.ai_girlfriend.models.database import IDatabaseStorage

class DatabaseController:
    """High level wrapper for Low-level Database API due to DI(dependency inversion)"""
    def __init__(self, provider: IDatabaseStorage):
        self.provider = provider


    async def init(self):
        ...

    
        