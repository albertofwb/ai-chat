# src/character/memory_manager.py
from typing import List, Dict, Optional
from src.vector.vector_store import vector_store


class MemoryManager:
    """记忆管理器"""

    def __init__(self, character: Dict, character_id: str = None):
        self.character = character
        self.character_id = character_id
        
        # 传统的关键词映射，作为回退方案
        self.keywords_map = {
            '想你': ['friendship_events', 'daily_life'],
            '吃': ['daily_routine'],
            '工作': ['daily_routine', 'hobbies'],
            '孩子': ['family_events'],
            '累': ['daily_routine'],
            '家': ['family_events', 'daily_routine']
        }
        
        # 确保角色记忆已导入向量存储
        if self.character_id:
            self._ensure_memories_imported()
    
    def _ensure_memories_imported(self) -> None:
        """确保角色记忆已导入向量存储"""
        try:
            # 检查是否已有记忆
            memories = vector_store.search_relevant_memories(
                query="test",
                character_id=self.character_id,
                limit=1
            )
            
            # 如果没有记忆，则导入
            if not memories:
                vector_store.import_character_memories_from_yaml(
                    character_data=self.character, 
                    character_id=self.character_id
                )
        except Exception as e:
            print(f"导入记忆失败: {str(e)}")
            # 失败时不阻止程序运行，使用传统方式继续

    def get_context_hints(self, context: str) -> Optional[str]:
        """获取上下文相关的提示"""
        # 使用向量搜索获取相关记忆
        if self.character_id:
            vector_hints = self._get_vector_hints(context)
            if vector_hints:
                return vector_hints
        
        # 如果向量搜索失败或没有结果，使用关键词搜索作为备选
        keyword_hints = self._get_keyword_hints(context)
        return "\n".join(keyword_hints) if keyword_hints else None
        
    def _get_vector_hints(self, context: str) -> Optional[str]:
        """使用向量搜索获取相关提示"""
        try:
            # 搜索相关记忆
            memories = vector_store.search_relevant_memories(
                query=context,
                character_id=self.character_id,
                limit=3  # 限制返回结果数量
            )
            
            # 处理搜索结果
            if memories:
                # 根据相关性排序
                memories.sort(key=lambda x: x["relevance"], reverse=True)
                
                # 构建提示
                hints = []
                for memory in memories:
                    if memory["relevance"] > 0.5:  # 只使用相关性高的记忆
                        memory_type = memory["metadata"].get("memory_type", "记忆")
                        text = memory["text"]
                        hints.append(f"[{memory_type}] {text}")
                
                return "\n".join(hints) if hints else None
        
        except Exception as e:
            print(f"向量搜索失败: {str(e)}")
            return None
    
    def _get_keyword_hints(self, context: str) -> List[str]:
        """使用关键词匹配获取相关提示"""
        hints = []

        for keyword, memory_types in self.keywords_map.items():
            if keyword in context:
                for memory_type in memory_types:
                    memories = self._get_memories_by_type(memory_type)
                    hints.extend(memories)

        return hints

    def _get_memories_by_type(self, memory_type: str) -> List[str]:
        """从角色定义中获取特定类型的记忆"""
        memories = self.character.get('memories', {})
        return memories.get(memory_type, [])

    def add_memory(self, content: str, memory_type: str) -> bool:
        """添加新的记忆"""
        if not self.character_id:
            return False
            
        try:
            # 添加到向量存储
            vector_store.add_character_memory(
                memory=content,
                character_id=self.character_id,
                memory_type=memory_type
            )
            return True
        except Exception as e:
            print(f"添加记忆失败: {str(e)}")
            return False

    def get_common_phrases(self) -> List[str]:
        """获取角色常用短语"""
        speaking_style = self.character.get('speaking_style', {})
        return speaking_style.get('common_phrases', [])