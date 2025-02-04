import signal
import asyncio
import sys
from typing import Optional
from character.loader import CharacterLoader
from src.chatbot import ChatBot, ChatBotError
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown


class ChatInterface:
    def __init__(self):
        self.console = Console()
        self.running = True
        self.chatbot = ChatBot()
        self.commands = {
            'quit': self.quit_chat,
            'clear': self.clear_history,
            'switch': self.switch_character,
            'help': self.show_help
        }

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
                    self.display_response(response)
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
- quit: 退出程序

请开始你的对话...
"""
        self.console.print(Panel(Markdown(welcome_text), title="系统信息"))

    async def get_user_input(self) -> Optional[str]:
        """获取用户输入"""
        return Prompt.ask("\n[bold green]你[/bold green]")

    def display_response(self, response: str):
        """显示 AI 响应"""
        self.console.print("\n[bold blue]AI[/bold blue]:", style="blue")
        self.console.print(Panel(response, border_style="blue"))

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
- quit: 退出程序

## 使用建议
1. 可以自然地进行对话，就像和真人聊天一样
2. 如果对话偏离了方向，可以使用 clear 命令重新开始
3. 可以通过 switch 命令切换到其他角色
4. 随时可以输入 help 查看此帮助信息
"""
        self.console.print(Panel(Markdown(help_text), title="帮助信息"))
        return True


def main():
    """主函数"""
    # 检查 Python 版本
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required.")
        sys.exit(1)

    # 创建并启动聊天界面
    interface = ChatInterface()
    asyncio.run(interface.start())


if __name__ == "__main__":
    main()