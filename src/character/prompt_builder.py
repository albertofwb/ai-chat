# src/character/prompt_builder.py
from typing import List, Dict
import yaml


class PromptBuilder:
    """系统提示构建器"""

    @staticmethod
    def build_prompt(character: Dict) -> str:
        prompt_parts = []

        # 添加基础提示
        prompt_parts.extend(PromptBuilder._build_base_prompt(character))

        # 添加性格信息
        prompt_parts.extend(PromptBuilder._build_characteristics(character))

        # 添加背景信息
        prompt_parts.extend(PromptBuilder._build_background(character))

        # 添加说话风格
        prompt_parts.extend(PromptBuilder._build_speaking_style(character))

        # 添加记忆信息
        prompt_parts.extend(PromptBuilder._build_memories(character))

        return "\n".join(prompt_parts)

    @staticmethod
    def _build_base_prompt(character: Dict) -> List[str]:
        return  [
            character['system_prompt']
            ]

    @staticmethod
    def _build_characteristics(character: Dict) -> List[str]:
        characteristics = character.get('characteristics', '')
        if not characteristics:
            return []

        return [
            "\n### 角色特征：",
            characteristics if isinstance(characteristics, str) else yaml.dump(
                characteristics, allow_unicode=True, default_flow_style=False
            )
        ]


    @staticmethod
    def _build_background(character: Dict) -> List[str]:
        background = character.get('background', '')
        if not background:
            return []

        return [
            "\n### 背景信息：",
            background if isinstance(background, str) else yaml.dump(
                background, allow_unicode=True, default_flow_style=False
            )
        ]

    @staticmethod
    def _build_speaking_style(character: Dict) -> List[str]:
        style = character.get('speaking_style', {})
        if not style:
            return []

        parts = ["\n### 说话特点："]

        if isinstance(style, dict):
            if 'tone' in style:
                parts.append(f"- 语气：{style['tone']}")
            if 'dialect' in style:
                parts.append(f"- 方言：{style['dialect']}")
            if 'patterns' in style:
                parts.append("- 表达模式：")
                parts.extend(f"  - {pattern}" for pattern in style['patterns'])
            if 'common_phrases' in style:
                parts.append("- 常用语：")
                parts.extend(f"  - {phrase}" for phrase in style['common_phrases'])
        else:
            parts.append(str(style))

        return parts

    @staticmethod
    def _build_memories(character: Dict) -> List[str]:
        memories = character.get('memories', {})
        if not memories:
            return []

        parts = ["\n### 重要记忆："]
        for memory_type, items in memories.items():
            parts.append(f"- {memory_type}：")
            if isinstance(items, list):
                parts.extend(f"  - {item}" for item in items)
            else:
                parts.append(f"  {items}")
        return parts