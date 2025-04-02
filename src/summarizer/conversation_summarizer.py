# src/summarizer/conversation_summarizer.py
from typing import List, Dict, Optional
import asyncio
from src.services.chat_service import ChatService
from src.db.db_manager import db_manager
from src.vector.vector_store import vector_store


class ConversationSummarizer:
    """对话摘要生成器"""
    
    def __init__(self):
        self.chat_service = ChatService()
    
    async def generate_summary(self, session_id: int, conversation_history: List[Dict[str, str]]) -> Optional[str]:
        """为指定会话生成摘要"""
        # 如果对话历史太短，不生成摘要
        if len(conversation_history) < 6:  # 如果消息不足6条，不生成摘要
            return None
        
        # 排除系统消息
        user_assistant_messages = [
            msg for msg in conversation_history 
            if msg["role"] in ["user", "assistant"]
        ]
        
        # 如果用户和助手的对话不足5轮，不生成摘要
        if len(user_assistant_messages) < 10:  # 至少5轮对话(用户+助手)
            return None
        
        # 获取现有摘要(如果存在)
        existing_summary = db_manager.get_latest_summary(session_id)
        
        # 构建摘要提示
        system_prompt = self._build_system_prompt(existing_summary)
        user_prompt = self._build_user_prompt(user_assistant_messages)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # 调用API生成摘要
            summary = await self.chat_service.send_message(
                messages=messages,
                temperature=0.3,  # 使用低温度以获得更确定性的结果
                max_tokens=500    # 限制摘要长度
            )
            
            # 保存摘要到数据库
            if summary:
                db_manager.add_summary(session_id, summary)
                
                # 添加到向量存储
                try:
                    vector_store.add_summary(summary, session_id)
                except Exception as e:
                    print(f"保存摘要到向量存储失败: {str(e)}")
            
            return summary
            
        except Exception as e:
            print(f"生成摘要失败: {str(e)}")
            return None
    
    def _build_system_prompt(self, existing_summary: Optional[str]) -> str:
        """构建摘要系统提示"""
        prompt = "你是一个聊天记录摘要专家。你的任务是生成一个简洁但信息丰富的对话摘要，" \
                "重点关注关键信息、用户偏好和重要细节。"
                
        if existing_summary:
            prompt += "\n\n以下是之前的对话摘要，请在此基础上更新：\n" + existing_summary
            
        prompt += "\n\n请确保摘要：\n" \
                "1. 提取用户表达的重要偏好、习惯和生活细节\n" \
                "2. 记录用户与AI角色建立的关系和互动方式\n" \
                "3. 保留可能在未来对话中有用的上下文\n" \
                "4. 避免无关或琐碎的细节\n" \
                "5. 不超过500字"
                
        return prompt
    
    def _build_user_prompt(self, messages: List[Dict[str, str]]) -> str:
        """构建用户提示"""
        formatted_messages = []
        
        for msg in messages:
            role = "用户" if msg["role"] == "user" else "AI"
            content = msg["content"]
            formatted_messages.append(f"{role}: {content}")
        
        return "以下是最近的对话记录，请生成一个摘要：\n\n" + "\n\n".join(formatted_messages)


# 创建全局摘要器实例
conversation_summarizer = ConversationSummarizer()
