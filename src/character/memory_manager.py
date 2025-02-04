# src/character/memory_manager.py
from typing import List, Dict, Optional


class MemoryManager:
    """记忆管理器"""

    def __init__(self, character: Dict):
        self.character = character
        self.keywords_map = {
            '想你': ['family_events', 'daily_life'],
            '吃': ['special_dishes'],
            '孩子': ['family_events'],
            '累': ['daily_life'],
            '家': ['family_events', 'daily_life']
        }

    def get_context_hints(self, context: str) -> Optional[str]:
        hints = []

        for keyword, memory_types in self.keywords_map.items():
            if keyword in context:
                for memory_type in memory_types:
                    memories = self._get_memories_by_type(memory_type)
                    hints.extend(memories)

        return "\n".join(hints) if hints else None

    def _get_memories_by_type(self, memory_type: str) -> List[str]:
        memories = self.character.get('memories', {})
        return memories.get(memory_type, [])

    def get_common_phrases(self) -> List[str]:
        speaking_style = self.character.get('speaking_style', {})
        return speaking_style.get('common_phrases', [])