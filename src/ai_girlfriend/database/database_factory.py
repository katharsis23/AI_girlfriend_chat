from src.ai_girlfriend.database.sqlite_provider import SQLiteProvider


DatabaseProviders = {
    "sqlite": SQLiteProvider
}

class DatabaseFactory:
    """
    Creates the database provider instance provided in config
    Params:
        - provider: Passes in GfPipeline class in setup 
    """
    def get_database(self, provider: str):
        if provider == "sqlite":
            return DatabaseProviders["sqlite"]
        else:
            raise NotImplementedError("Only SQLite provider has been created")
                                     