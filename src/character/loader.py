# src/character/
# ├── __init__.py
# ├── loader.py         # 基础加载器
# ├── prompt_builder.py # 提示构建器
# └── memory_manager.py # 记忆管理器

# src/character/loader.py
from pathlib import Path
import yaml
from typing import Dict, Optional
from config.config_manager import config_manager


class CharacterLoader:
    """角色配置加载器"""

    def __init__(self, characters_dir: Optional[Path] = None):
        self.characters_dir = characters_dir or config_manager.get_character_dir()
        self.characters: Dict[str, dict] = {}
        self.load_all_characters()

    def load_all_characters(self) -> None:
        for filename in self.characters_dir.glob('*.yaml'):
            character_id = filename.stem
            self.characters[character_id] = self._load_character(filename)

    def _load_character(self, file_path: Path) -> dict:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_character(self, character_id: str) -> Optional[dict]:
        return self.characters.get(character_id)


if __name__ == '__main__':
    print(config_manager)