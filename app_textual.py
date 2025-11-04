"""
Textual-based UI for the Document Assistant
Beautiful terminal interface with web accessibility support
"""

import os
import sys
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header,
    Footer,
    Input,
    Button,
    Static,
    Label,
    RichLog,
    TabbedContent,
    TabPane,
)
from textual.screen import Screen
from textual.binding import Binding
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.assistant import DocumentAssistant


class MessageDisplay(Static):
    """Widget to display a single message"""

    def __init__(self, role: str, content: str, metadata: dict = None):
        super().__init__()
        self.role = role
        self.content = content
        self.metadata = metadata or {}

    def compose(self) -> ComposeResult:
        if self.role == "user":
            yield Static(
                f"[bold cyan]👤 You:[/bold cyan]\n{self.content}",
                classes="user-message",
            )
        else:
            # Format assistant message with metadata
            message = f"[bold green]🤖 Assistant:[/bold green]\n{self.content}"

            if self.metadata.get("intent"):
                intent_type = self.metadata["intent"].get("intent_type", "unknown")
                message += f"\n\n[dim]Intent: {intent_type}[/dim]"

            if self.metadata.get("tools_used"):
                tools = ", ".join(self.metadata["tools_used"])
                message += f"\n[dim]Tools: {tools}[/dim]"

            if self.metadata.get("sources"):
                sources = ", ".join(self.metadata["sources"])
                message += f"\n[dim]Sources: {sources}[/dim]"

            yield Static(message, classes="assistant-message")


class DocumentAssistantApp(App):
    """A Textual app for the Document Assistant"""

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 100%;
        layout: vertical;
    }

    #chat-container {
        height: 1fr;
        border: solid $primary;
        background: $panel;
        padding: 1;
    }

    #input-container {
        height: auto;
        layout: horizontal;
        padding: 1;
        background: $surface;
    }

    #message-input {
        width: 1fr;
        margin-right: 1;
    }

    #send-button {
        width: auto;
        min-width: 10;
    }

    .user-message {
        background: $boost;
        padding: 1;
        margin: 1;
        border: solid $accent;
    }

    .assistant-message {
        background: $panel;
        padding: 1;
        margin: 1;
        border: solid $primary;
    }

    .thinking {
        background: $boost;
        border: dashed $warning;
        opacity: 0.8;
        padding: 1 2;
        margin: 1 1 2 1;
    }

    #status-bar {
        height: 3;
        background: $surface;
        padding: 1;
        border: solid $primary;
    }

    #sidebar {
        width: 40;
        background: $panel;
        border: solid $primary;
        padding: 1;
    }

    .info-panel {
        height: auto;
        margin: 1;
        padding: 1;
        background: $boost;
        border: solid $accent;
    }

    InfoScreen {
        align: center middle;
    }

    #info-dialog {
        width: 80;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 2;
    }

    #info-content {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+d", "show_docs", "Documents", show=True),
        Binding("ctrl+h", "show_help", "Help", show=True, priority=True),
        Binding("ctrl+n", "new_session", "New Session", show=True, priority=True),
        Binding("f1", "show_help", "Help (F1)", show=False),
        Binding("f2", "show_docs", "Docs (F2)", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.assistant = None
        self.session_id = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)

        with Container(id="main-container"):
            with Horizontal():
                # Main chat area
                with Vertical(id="chat-section"):
                    yield ScrollableContainer(id="chat-container")
                    with Horizontal(id="input-container"):
                        yield Input(
                            placeholder="Type your message here...",
                            id="message-input",
                        )
                        yield Button("Send", variant="primary", id="send-button")

                # Sidebar with info
                with Vertical(id="sidebar"):
                    yield Static(
                        "[bold]📊 Session Info[/bold]", classes="info-panel"
                    )
                    yield Static(id="session-info", classes="info-panel")
                    yield Static(
                        "[bold]📝 Quick Commands[/bold]\n\n"
                        "• F1 or Ctrl+H - Help\n"
                        "• F2 or Ctrl+D - Documents\n"
                        "• Ctrl+N - New session\n"
                        "• Ctrl+Q - Quit\n"
                        "• Enter - Send message",
                        classes="info-panel",
                    )

            yield Static(id="status-bar")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the assistant when the app starts."""
        status = self.query_one("#status-bar", Static)
        status.update("[yellow]⏳ Initializing assistant...[/yellow]")

        # Load environment variables
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            status.update(
                "[red]❌ Error: OPENAI_API_KEY not found. Please create a .env file.[/red]"
            )
            return

        try:
            # Initialize assistant
            self.assistant = DocumentAssistant(
                openai_api_key=api_key, model_name="gpt-4o", temperature=0.1
            )

            # Start session
            user_id = "textual_user"
            self.session_id = self.assistant.start_session(user_id)

            # Update UI
            session_info = self.query_one("#session-info", Static)
            session_info.update(
                f"[green]✓ Session: {self.session_id[:8]}...[/green]\n"
                f"[dim]Started: {datetime.now().strftime('%H:%M:%S')}[/dim]"
            )

            status.update("[green]✓ Ready! Type your message below.[/green]")

            # Add welcome message
            chat = self.query_one("#chat-container", ScrollableContainer)
            welcome = MessageDisplay(
                "assistant",
                "👋 Welcome to the Document Assistant!\n\n"
                "I can help you with:\n"
                "• Answering questions about documents\n"
                "• Summarizing documents\n"
                "• Performing calculations on document data\n\n"
                "Try asking: 'What's the total amount in invoice INV-001?'",
            )
            await chat.mount(welcome)

        except Exception as e:
            status.update(f"[red]❌ Error: {str(e)}[/red]")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "send-button":
            await self.send_message()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "message-input":
            await self.send_message()

    async def send_message(self) -> None:
        """Send a message to the assistant."""
        message_input = self.query_one("#message-input", Input)
        user_message = message_input.value.strip()

        if not user_message:
            return

        # Clear input
        message_input.value = ""

        # Get widgets
        chat = self.query_one("#chat-container", ScrollableContainer)
        status = self.query_one("#status-bar", Static)

        # Display user message
        user_msg = MessageDisplay("user", user_message)
        await chat.mount(user_msg)
        chat.scroll_end(animate=False)

        # Show thinking indicator with animation
        thinking_msg = Static(
            "[bold green]🤖 Assistant:[/bold green]\n[dim italic]💭 Thinking...[/dim italic]",
            classes="assistant-message thinking",
            id="thinking-indicator"
        )
        await chat.mount(thinking_msg)
        chat.scroll_end(animate=True)

        # Update status
        status.update("[yellow]⏳ Processing your request...[/yellow]")

        # Force UI refresh before blocking call
        await asyncio.sleep(0.1)
        
        # Start processing in background
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Run blocking process_message in thread pool to keep UI responsive
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor, 
                    self.assistant.process_message, 
                    user_message
                )

            # Ensure thinking indicator shows for at least 0.5 seconds
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed < 0.5:
                await asyncio.sleep(0.5 - elapsed)

            # Remove thinking indicator
            thinking_msg.remove()

            if result["success"]:
                # Display assistant response
                assistant_msg = MessageDisplay(
                    "assistant",
                    result["response"] or "No response generated.",
                    metadata={
                        "intent": result.get("intent"),
                        "tools_used": result.get("tools_used", []),
                        "sources": result.get("sources", []),
                    },
                )
                await chat.mount(assistant_msg)
                chat.scroll_end(animate=False)

                status.update("[green]✓ Response received[/green]")
            else:
                # Display error
                error_msg = MessageDisplay(
                    "assistant",
                    f"❌ Error: {result.get('error', 'Unknown error')}",
                )
                await chat.mount(error_msg)
                chat.scroll_end(animate=False)

                status.update("[red]❌ Error occurred[/red]")

        except Exception as e:
            # Remove thinking indicator if still present
            try:
                thinking_msg.remove()
            except:
                pass
            
            error_msg = MessageDisplay("assistant", f"❌ Unexpected error: {str(e)}")
            await chat.mount(error_msg)
            chat.scroll_end(animate=False)
            status.update(f"[red]❌ Error: {str(e)}[/red]")

    def action_show_docs(self) -> None:
        """Show available documents."""
        if not self.assistant:
            return

        docs_text = "📚 Available Documents:\n\n"
        for doc_id, doc in self.assistant.retriever.documents.items():
            docs_text += f"• {doc_id}: {doc.title} ({doc.doc_type})\n"
            if "total" in doc.metadata:
                docs_text += f"  Amount: ${doc.metadata['total']:,.2f}\n"

        self.push_screen(InfoScreen(docs_text, "Documents"))

    def action_show_help(self) -> None:
        """Show help information."""
        help_text = """
# Document Assistant Help

## Example Queries

### Q&A
- What's the total amount in invoice INV-001?
- What are the terms of contract CON-001?
- Show me details about claim CLM-001

### Summarization
- Summarize all contracts
- Give me a summary of invoice INV-002
- Summarize the insurance claims

### Calculations
- Calculate the sum of all invoice totals
- What's the average amount of all documents?
- Add the totals from INV-001 and INV-002

## Keyboard Shortcuts
- **Ctrl+D** - Show documents
- **Ctrl+H** - Show this help
- **Ctrl+N** - Start new session
- **Ctrl+Q** - Quit application
- **Enter** - Send message
"""
        self.push_screen(InfoScreen(help_text, "Help"))

    def action_new_session(self) -> None:
        """Start a new session."""
        if self.assistant:
            self.session_id = self.assistant.start_session("textual_user")
            session_info = self.query_one("#session-info", Static)
            session_info.update(
                f"[green]✓ New Session: {self.session_id[:8]}...[/green]\n"
                f"[dim]Started: {datetime.now().strftime('%H:%M:%S')}[/dim]"
            )
            status = self.query_one("#status-bar", Static)
            status.update("[green]✓ New session started[/green]")


class InfoScreen(Screen):
    """Modal screen to display information."""

    def __init__(self, content: str, title: str = "Info"):
        super().__init__()
        self.content = content
        self.title = title

    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"[bold]{self.title}[/bold]\n\n{self.content}", id="info-content"),
            Button("Close", variant="primary", id="close-button"),
            id="info-dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-button":
            self.app.pop_screen()


def main():
    """Run the Textual app."""
    app = DocumentAssistantApp()
    app.run()


if __name__ == "__main__":
    main()
