# src/character/character.py
from typing import Optional, List
from .loader import CharacterLoader
from .prompt_builder import PromptBuilder
from .memory_manager import MemoryManager


class Character:
    def __init__(self, character_id: str):
        self.loader = CharacterLoader()
        self.loader.load_all_characters()
        self.character_data = self.loader.get_character(character_id)
        if not self.character_data:
            raise ValueError(f"Character {character_id} not found")

        self.prompt_builder = PromptBuilder()
        self.memory_manager = MemoryManager(self.character_data)

    def get_system_prompt(self) -> str:
        return self.prompt_builder.build_prompt(self.character_data)

    def get_context_hints(self, context: str) -> Optional[str]:
        return self.memory_manager.get_context_hints(context)

    def get_common_phrases(self) -> List[str]:
        return self.memory_manager.get_common_phrases()