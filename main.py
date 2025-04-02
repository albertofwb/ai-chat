import signal
import asyncio
import sys
import threading
from typing import Optional
from src.character.loader import CharacterLoader
from src.chatbot import ChatBot, ChatBotError
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from src.web.app import start_web_app
import webbrowser


class ChatInterface:
    def __init__(self):
        self.console = Console()
        self.running = True
        self.chatbot = ChatBot()
        self.commands = {
            'quit': self.quit_chat,
            'clear': self.clear_history,
            'switch': self.switch_character,
            'help': self.show_help,
            'web': self.open_web_interface,
            'summary': self.show_summary,
            'tts': self.toggle_tts
        }
        
        # TTS功能默认关闭
        self.use_tts = False

    async def quit_chat(self) -> bool:
        """退出聊天"""
        self.console.print("[yellow]感谢使用，再见！[/yellow]")
        self.running = False
        return False

    async def start(self):
        """启动聊天界面"""
        self.show_welcome_message()

        while self.running:
            try:
                user_input = await self.get_user_input()
                if not user_input:
                    continue

                # 检查是否是命令
                command = self.commands.get(user_input.lower())
                if command:
                    should_continue = await command()
                    if not should_continue:
                        break
                    continue

                # 发送消息并获取响应
                response = await self.chatbot.chat(user_input)
                if response:
                    await self.display_response(response)
                else:
                    self.console.print("[red]抱歉，获取响应时出现错误。[/red]")

            except KeyboardInterrupt:
                self.console.print("\n[yellow]正在退出聊天...[/yellow]")
                break
            except ChatBotError as e:
                self.console.print(f"[red]聊天错误: {str(e)}[/red]")
            except Exception as e:
                self.console.print(f"[red]意外错误: {str(e)}[/red]")

    def show_welcome_message(self):
        """显示欢迎信息"""
        welcome_text = f"""
# 欢迎来到温情对话系统

当前角色: {self.chatbot.get_current_character()}

可用命令:
- help: 显示帮助信息
- clear: 清除对话历史
- switch: 切换对话角色
- web: 打开Web界面
- summary: 生成并显示对话摘要
- tts: 切换文字转语音功能
- quit: 退出程序

请开始你的对话...
"""
        self.console.print(Panel(Markdown(welcome_text), title="系统信息"))

    async def get_user_input(self) -> Optional[str]:
        """获取用户输入"""
        return Prompt.ask("\n[bold green]你[/bold green]")

    async def display_response(self, response: str):
        """显示 AI 响应"""
        self.console.print("\n[bold blue]AI[/bold blue]:", style="blue")
        self.console.print(Panel(response, border_style="blue"))
        
        # 如果启用TTS，请求语音生成
        if self.use_tts:
            try:
                from src.tts.voice_service import voice_service
                audio_file = await voice_service.generate_voice(
                    text=response, 
                    character_id=self.chatbot.get_current_character()
                )
                if audio_file and sys.platform == 'win32':
                    # 在Windows上使用PowerShell播放音频
                    import subprocess
                    subprocess.Popen(
                        ['powershell', '-c', f'(New-Object Media.SoundPlayer "{audio_file}").PlaySync()'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
            except Exception as e:
                self.console.print(f"[red]语音生成失败: {str(e)}[/red]")

    async def quit_chat(self) -> bool:
        """退出聊天"""
        self.console.print("[yellow]感谢使用，再见！[/yellow]")
        return False

    async def clear_history(self) -> bool:
        """清除对话历史"""
        try:
            self.chatbot.clear_history()
            self.console.print("[green]对话历史已清除[/green]")
        except ChatBotError as e:
            self.console.print(f"[red]清除历史失败: {str(e)}[/red]")
        return True

    async def switch_character(self) -> bool:
        """切换角色"""
        try:
            character_loader = CharacterLoader()
            character_loader.load_all_characters()
            # 获取可用角色列表
            available_characters = list(character_loader.characters.keys())

            self.console.print("\n可用角色:")
            for i, char_id in enumerate(available_characters, 1):
                char_data = character_loader.get_character(char_id)
                name = char_data.get('name', char_id)
                self.console.print(f"{i}. {name} ({char_id})")

            choice = Prompt.ask("\n请选择角色编号", default="1")
            try:
                index = int(choice) - 1
                if 0 <= index < len(available_characters):
                    character_id = available_characters[index]
                    self.chatbot.load_character(character_id)
                    self.console.print(f"[green]已切换到角色: {character_id}[/green]")
                else:
                    self.console.print("[red]无效的选择[/red]")
            except ValueError:
                self.console.print("[red]请输入有效的数字[/red]")

        except ChatBotError as e:
            self.console.print(f"[red]切换角色失败: {str(e)}[/red]")
        except Exception as e:
            self.console.print(f"[red]发生错误: {str(e)}[/red]")

        return True

    async def show_help(self) -> bool:
        """显示帮助信息"""
        help_text = """
# 帮助信息

## 基本命令
- help: 显示此帮助信息
- clear: 清除当前对话历史
- switch: 切换到其他角色
- web: 打开Web界面
- summary: 生成并显示对话摘要
- tts: 切换文字转语音功能
- quit: 退出程序

## 使用建议
1. 可以自然地进行对话，就像和真人聊天一样
2. 如果对话偏离了方向，可以使用 clear 命令重新开始
3. 可以通过 switch 命令切换到其他角色
4. 随时可以输入 help 查看此帮助信息
5. 每次对话都会被保存，可以在Web界面中查看历史对话
"""
        self.console.print(Panel(Markdown(help_text), title="帮助信息"))
        return True
        
    async def open_web_interface(self) -> bool:
        """打开Web界面"""
        self.console.print("[green]正在打开Web界面...[/green]")
        try:
            # 在新线程中启动Web服务
            if not hasattr(self, 'web_thread') or not self.web_thread.is_alive():
                self.web_thread = threading.Thread(target=start_web_app, daemon=True)
                self.web_thread.start()
                # 等待服务器启动
                await asyncio.sleep(2)
            
            # 打开浏览器
            webbrowser.open('http://localhost:8000')
            self.console.print("[green]Web界面已打开，你可以继续在控制台也可以在浏览器中聊天[/green]")
        except Exception as e:
            self.console.print(f"[red]打开Web界面失败: {str(e)}[/red]")
        
        return True
        
    async def show_summary(self) -> bool:
        """生成并显示对话摘要"""
        self.console.print("[green]正在生成对话摘要...[/green]")
        
        try:
            summary = await self.chatbot.generate_summary()
            
            if summary:
                self.console.print(Panel(Markdown(summary), title="对话摘要"))
            else:
                self.console.print("[yellow]暂无摘要或对话过短[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]生成摘要失败: {str(e)}[/red]")
            
        return True
        
    async def toggle_tts(self) -> bool:
        """切换文字转语音功能"""
        self.use_tts = not self.use_tts
        
        status = "开启" if self.use_tts else "关闭"
        self.console.print(f"[green]文字转语音功能已{status}[/green]")
        
        # 检查依赖
        if self.use_tts:
            try:
                from src.tts.voice_service import voice_service
                if not voice_service.tts_available:
                    self.console.print("[yellow]警告: TTS服务不可用，请安装edge-tts库: pip install edge-tts[/yellow]")
            except ImportError:
                self.console.print("[yellow]警告: 需要安装edge-tts库: pip install edge-tts[/yellow]")
        
        return True


def main():
    """主函数"""
    # 检查 Python 版本
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required.")
        sys.exit(1)
        
    # 命令行参数处理
    import argparse
    parser = argparse.ArgumentParser(description='AI 温情对话系统')
    parser.add_argument('--web', action='store_true', help='只启动Web界面')
    parser.add_argument('--both', action='store_true', help='同时启动控制台和Web界面')
    args = parser.parse_args()
    
    if args.web:
        # 只启动Web界面
        start_web_app()
    elif args.both:
        # 在新线程中启动Web服务
        web_thread = threading.Thread(target=start_web_app, daemon=True)
        web_thread.start()
        # 主线程执行控制台界面
        console_interface = ChatInterface()
        asyncio.run(console_interface.start())
    else:
        # 默认只启动控制台
        interface = ChatInterface()
        asyncio.run(interface.start())


if __name__ == "__main__":
    main()