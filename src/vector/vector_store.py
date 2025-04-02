# src/vector/vector_store.py
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import numpy as np
from datetime import datetime

# 添加到 requirements.txt:
# chromadb
# sentence-transformers
# numpy
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("请安装所需依赖: pip install chromadb sentence-transformers numpy")
    raise


class VectorStore:
    """向量存储类，用于管理对话的向量表示和语义检索"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.vector_dir = Path(__file__).parent.parent.parent / 'data' / 'vectors'
        self.vector_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化 ChromaDB
        self.chroma_client = chromadb.PersistentClient(str(self.vector_dir / 'chroma'))
        
        # 加载模型 - 可以根据需要使用不同的模型
        self.model = None  # 延迟加载模型
        
        # 确保必要的集合存在
        self._ensure_collections()
    
    def _load_model(self):
        """延迟加载模型，只在需要时初始化"""
        if self.model is None:
            try:
                self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            except Exception as e:
                print(f"模型加载失败: {str(e)}")
                raise
    
    def _ensure_collections(self):
        """确保必要的集合存在"""
        try:
            # 用户消息集合
            self.user_messages = self.chroma_client.get_or_create_collection(
                name="user_messages",
                metadata={"description": "用户消息的向量存储"}
            )
            
            # 字符记忆集合
            self.character_memories = self.chroma_client.get_or_create_collection(
                name="character_memories",
                metadata={"description": "角色记忆的向量存储"}
            )
            
            # 摘要集合
            self.summaries = self.chroma_client.get_or_create_collection(
                name="summaries",
                metadata={"description": "对话摘要的向量存储"}
            )
        except Exception as e:
            print(f"创建集合失败: {str(e)}")
            raise
    
    def encode_text(self, text: str) -> List[float]:
        """将文本编码为向量"""
        self._load_model()
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def add_user_message(self, 
                         message: str, 
                         session_id: int, 
                         message_id: Optional[int] = None,
                         metadata: Optional[Dict] = None) -> str:
        """添加用户消息到向量存储"""
        self._load_model()
        
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "type": "user_message"
        })
        
        if message_id:
            metadata["message_id"] = message_id
            
        # 生成唯一ID
        doc_id = f"msg_{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 将消息添加到集合
        self.user_messages.add(
            documents=[message],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def add_character_memory(self, 
                           memory: str, 
                           character_id: str,
                           memory_type: str,
                           metadata: Optional[Dict] = None) -> str:
        """添加角色记忆到向量存储"""
        self._load_model()
        
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "character_id": character_id,
            "memory_type": memory_type,
            "timestamp": datetime.now().isoformat()
        })
            
        # 生成唯一ID
        doc_id = f"mem_{character_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 将记忆添加到集合
        self.character_memories.add(
            documents=[memory],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def add_summary(self, 
                   summary: str, 
                   session_id: int,
                   metadata: Optional[Dict] = None) -> str:
        """添加摘要到向量存储"""
        self._load_model()
        
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
            
        # 生成唯一ID
        doc_id = f"sum_{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 将摘要添加到集合
        self.summaries.add(
            documents=[summary],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def search_relevant_user_messages(self, 
                                     query: str, 
                                     session_id: Optional[int] = None,
                                     limit: int = 5) -> List[Dict]:
        """搜索与查询相关的用户消息"""
        self._load_model()
        
        # 构建查询参数
        where_clause = None
        if session_id:
            where_clause = {"session_id": session_id}
        
        # 执行查询
        results = self.user_messages.query(
            query_texts=[query],
            n_results=limit,
            where=where_clause
        )
        
        # 格式化结果
        formatted_results = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            formatted_results.append({
                "text": doc,
                "metadata": metadata,
                "relevance": 1.0 - min(1.0, distance)  # 转换为相关性分数
            })
        
        return formatted_results
    
    def search_relevant_memories(self, 
                               query: str, 
                               character_id: Optional[str] = None,
                               memory_type: Optional[str] = None,
                               limit: int = 5) -> List[Dict]:
        """搜索与查询相关的角色记忆"""
        self._load_model()
        
        # 构建查询参数
        where_clause = {}
        if character_id:
            where_clause["character_id"] = character_id
        if memory_type:
            where_clause["memory_type"] = memory_type
        
        # 执行查询
        results = self.character_memories.query(
            query_texts=[query],
            n_results=limit,
            where=where_clause if where_clause else None
        )
        
        # 格式化结果
        formatted_results = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            formatted_results.append({
                "text": doc,
                "metadata": metadata,
                "relevance": 1.0 - min(1.0, distance)  # 转换为相关性分数
            })
        
        return formatted_results
    
    def import_character_memories_from_yaml(self, character_data: Dict, character_id: str) -> None:
        """从角色定义导入记忆到向量存储"""
        memories = character_data.get('memories', {})
        
        for memory_type, items in memories.items():
            if isinstance(items, list):
                for item in items:
                    self.add_character_memory(
                        memory=item,
                        character_id=character_id,
                        memory_type=memory_type
                    )
            else:
                self.add_character_memory(
                    memory=str(items),
                    character_id=character_id,
                    memory_type=memory_type
                )


# 创建全局向量存储实例
vector_store = VectorStore()
