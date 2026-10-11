from src.ai_girlfriend.config.config import Config, config

class CompositionRoot:
    def __init__(self, config: Config):
        self.config = config


    def build_pipeline(self):
        ...