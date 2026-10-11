from src.ai_girlfriend.models.character import CharacterInfo

class CharacterManager:
    """
    Manager to rule and validate character expressions
    Params:
        - characters: Global Pool of available characters
    """
    def __init__(self, characters: set(CharacterInfo)):
        self.characters = characters

    def resolve(character: str, expression: str):
        ...

    def asset_path(character: str, expression: str):
        ...

