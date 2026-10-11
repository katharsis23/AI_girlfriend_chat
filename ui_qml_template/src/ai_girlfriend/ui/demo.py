"""Offline demo core so the UI can run without the real pipeline (`python -m ai_girlfriend.ui --demo`)."""

from __future__ import annotations

import asyncio
import itertools
from dataclasses import dataclass, field


@dataclass
class CharacterInfo:
    character_id: str
    name: str
    personality: str
    initial_expression: str = "neutral"
    greeting: str = ""
    photo_emoji_map: dict = field(default_factory=dict)


@dataclass
class Reply:
    text: str
    expression: str
    chat_id: int


@dataclass
class DemoConfig:
    characters: list


class DemoPipeline:
    _ids = itertools.count(1)

    def __init__(self, character: CharacterInfo):
        self.character = character

    async def chat(self, text: str, chat_id=None) -> Reply:
        await asyncio.sleep(1.1)
        low = text.lower()
        if low.strip() == "/error":
            raise RuntimeError("Модель не відповіла вчасно. Спробуйте ще раз.")
        if any(w in low for w in ("привіт", "hello", "hi")):
            expr, reply = (
                "happy",
                f"Привіт! Я {self.character.name}. Рада тебе бачити 😊",
            )
        elif "?" in low:
            expr, reply = (
                "thinking",
                "Хм, цікаве питання… дай мені секунду подумати над цим.",
            )
        elif any(w in low for w in ("сум", "погано", "sad")):
            expr, reply = "sad", "Мені шкода це чути. Хочеш розповісти більше?"
        elif any(w in low for w in ("люблю", "love", "гарна")):
            expr, reply = "shy", "О… дякую, мені дуже приємно."
        else:
            expr, reply = "surprised", "Оо, справді? Розкажи далі!"
        return Reply(reply, expr, chat_id or next(self._ids))


class DemoRoot:
    def __init__(self):
        self.config = DemoConfig(
            [
                CharacterInfo(
                    "mika",
                    "Міка",
                    "Тепла, жартівлива, трохи сором'язлива.",
                    "happy",
                    "Привіт! Я Міка. Про що поговоримо сьогодні?",
                ),
                CharacterInfo(
                    "aria",
                    "Арія",
                    "Спокійна й вдумлива, любить глибокі розмови.",
                    "thinking",
                    "Добрий день. Я Арія — можемо почати з будь-якої теми.",
                ),
                CharacterInfo(
                    "nova",
                    "Нова",
                    "Енергійна, цікава до всього нового.",
                    "surprised",
                    "Хей! Я Нова. Що нового?",
                ),
            ]
        )

    def build_pipeline(self, character=None):
        return DemoPipeline(character or self.config.characters[0])
