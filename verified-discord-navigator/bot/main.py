import os
import sys
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Ensure core and models imports resolve properly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.decision_engine import DecisionEngine
from bot.commands import NavigatorCommands
from bot.embeds import create_result_embed
from bot.views import VerifiedResultView, ConflictResultView, InsufficientResultView
from models.result import DecisionStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifiedNavigatorBot")

load_dotenv()


class VerifiedNavigatorBot(commands.Bot):
    def __init__(self, engine: DecisionEngine, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = engine

    async def setup_hook(self):
        await self.add_cog(NavigatorCommands(self, self.engine))
        try:
            guild_id = os.getenv("DISCORD_GUILD_ID")
            if guild_id and guild_id.strip():
                guild = discord.Object(id=int(guild_id.strip()))
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} slash commands to Guild {guild_id}")
            else:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} slash commands globally")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")


def create_bot(enable_message_content: bool = True) -> tuple[commands.Bot, DecisionEngine]:
    intents = discord.Intents.default()
    if enable_message_content:
        try:
            intents.message_content = True
        except AttributeError:
            pass

    engine = DecisionEngine()
    bot = VerifiedNavigatorBot(engine=engine, command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        logger.info(f"✅ Bot registered successfully as {bot.user} (ID: {bot.user.id})")

    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        if bot.user in message.mentions:
            clean_question = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
            if not clean_question:
                await message.channel.send("Bạn cần hỏi gì? Hãy thử: `@VerifiedBot Workshop 2 khi nào có slide?`")
                return

            intent = engine.classifier.classify(clean_question)
            ann_channel_id = os.getenv("ANNOUNCEMENT_CHANNEL_ID", "1532306560871567390").strip()

            live_messages = []
            if ann_channel_id and intent in ["schedule", "workshop", "deadline", "unknown"]:
                live_messages = await engine.retriever.fetch_live_messages_async(bot, ann_channel_id)

            db_messages = engine.retriever.load_all_messages()
            all_messages = live_messages + db_messages if live_messages else db_messages

            result = engine.process_query(
                question=clean_question,
                user_id=str(message.author.id),
                channel_id=str(message.channel.id),
                messages=all_messages
            )

            embed = create_result_embed(result)
            if result.status == DecisionStatus.VERIFIED:
                view = VerifiedResultView(result)
            elif result.status == DecisionStatus.VERIFIED_WITH_CONFLICT_RESOLVED:
                view = ConflictResultView(result)
            else:
                view = InsufficientResultView(result)

            # Send ONLY 1 SINGLE clean embed message
            await message.channel.send(embed=embed, view=view)
            return

        await bot.process_commands(message)

    return bot, engine


def main():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token or token == "YOUR_DISCORD_BOT_TOKEN":
        logger.warning("DISCORD_BOT_TOKEN not set in environment or .env file.")
        return

    try:
        bot, engine = create_bot(enable_message_content=True)
        bot.run(token)
    except discord.errors.PrivilegedIntentsRequired:
        logger.warning("Message Content Intent not enabled in Dev Portal. Falling back to Slash Command mode...")
        bot, engine = create_bot(enable_message_content=False)
        bot.run(token)


if __name__ == "__main__":
    main()
