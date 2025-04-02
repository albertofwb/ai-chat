# src/web/app.py
from pathlib import Path
import asyncio
import json
import uuid
from typing import List, Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

# 添加到 requirements.txt
# fastapi
# uvicorn
# jinja2
# websockets

# 导入项目组件
from src.character.loader import CharacterLoader
from src.chatbot import ChatBot


app = FastAPI(title="AI Chat Web")

# 设置模板和静态文件
base_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(base_dir / "templates"))

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(base_dir / "static")), name="static")

# 聊天连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.chatbots: Dict[str, ChatBot] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        # 初始化默认角色的ChatBot
        if client_id not in self.chatbots:
            self.chatbots[client_id] = ChatBot(character_id="li_ming")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    def get_chatbot(self, client_id: str) -> Optional[ChatBot]:
        return self.chatbots.get(client_id)


# 创建连接管理器
manager = ConnectionManager()


# 请求模型
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[int] = None


class CharacterSelect(BaseModel):
    character_id: str


class SessionInfo(BaseModel):
    session_id: int


# 路由
@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """主页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/characters", response_class=JSONResponse)
async def get_characters():
    """获取所有可用角色"""
    try:
        character_loader = CharacterLoader()
        character_loader.load_all_characters()
        
        characters = []
        for char_id, char_data in character_loader.characters.items():
            characters.append({
                "id": char_id,
                "name": char_data.get('name', char_id),
                "description": char_data.get('system_prompt', '')[:100] + '...'
            })
        
        return {"characters": characters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions", response_class=JSONResponse)
async def get_sessions():
    """获取最近的会话"""
    try:
        # 创建临时ChatBot来获取会话
        temp_bot = ChatBot()
        sessions = temp_bot.get_recent_sessions(limit=10)
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket处理聊天消息"""
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            action = payload.get("action")
            
            chatbot = manager.get_chatbot(client_id)
            if not chatbot:
                await manager.send_message(client_id, {
                    "error": "ChatBot不可用",
                    "action": action
                })
                continue
            
            if action == "chat":
                user_message = payload.get("message", "")
                if not user_message:
                    continue
                
                # 发送正在思考状态
                await manager.send_message(client_id, {
                    "status": "thinking",
                    "action": "status"
                })
                
                # 处理消息
                try:
                    response = await chatbot.chat(user_message)
                    
                    # 发送响应
                    await manager.send_message(client_id, {
                        "message": response,
                        "action": "response",
                        "session_id": chatbot.get_session_id()
                    })
                    
                except Exception as e:
                    await manager.send_message(client_id, {
                        "error": str(e),
                        "action": "error"
                    })
            
            elif action == "select_character":
                character_id = payload.get("character_id")
                if not character_id:
                    continue
                
                # 切换角色
                try:
                    chatbot.load_character(character_id)
                    
                    # 发送成功响应
                    await manager.send_message(client_id, {
                        "character_id": character_id,
                        "action": "character_changed",
                        "session_id": chatbot.get_session_id()
                    })
                    
                except Exception as e:
                    await manager.send_message(client_id, {
                        "error": str(e),
                        "action": "error"
                    })
            
            elif action == "load_session":
                session_id = payload.get("session_id")
                if not session_id:
                    continue
                
                # 加载会话
                try:
                    chatbot.load_session(session_id)
                    
                    # 获取会话历史消息
                    history = chatbot.get_conversation_history()
                    
                    # 发送成功响应
                    await manager.send_message(client_id, {
                        "history": history,
                        "action": "session_loaded",
                        "session_id": session_id
                    })
                    
                except Exception as e:
                    await manager.send_message(client_id, {
                        "error": str(e),
                        "action": "error"
                    })
            
            elif action == "clear_history":
                # 清除聊天历史
                try:
                    chatbot.clear_history()
                    
                    # 发送成功响应
                    await manager.send_message(client_id, {
                        "action": "history_cleared",
                        "session_id": chatbot.get_session_id()
                    })
                    
                except Exception as e:
                    await manager.send_message(client_id, {
                        "error": str(e),
                        "action": "error"
                    })
            
            elif action == "get_summary":
                # 获取或生成摘要
                try:
                    # 获取现有摘要
                    summary = chatbot.get_latest_summary()
                    
                    # 如果不存在，则生成新摘要
                    if not summary:
                        summary = await chatbot.generate_summary()
                    
                    # 发送响应
                    await manager.send_message(client_id, {
                        "summary": summary,
                        "action": "summary_result",
                        "session_id": chatbot.get_session_id()
                    })
                    
                except Exception as e:
                    await manager.send_message(client_id, {
                        "error": str(e),
                        "action": "error"
                    })
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket错误: {str(e)}")
        manager.disconnect(client_id)


# 启动Web应用
def start_web_app():
    """启动Web应用"""
    uvicorn.run("src.web.app:app", host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    start_web_app()
