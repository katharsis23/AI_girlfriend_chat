from pydantic import BaseModel, Field


class CharacterInfo(BaseModel):
    """
    Model representing character information for the AI Girlfriend application.
    """

    name: str = Field(description="The name of the character.")

    personality: str = Field(
        description="A brief description of the character's personality."
    )

    photo_emoji_map: dict[str, str] = Field(
        description="A mapping of photo URLs to corresponding emojis representing the character."
    )

    greeting_message: str = Field(
        description="A greeting message that the character will use when interacting with users."
    )
