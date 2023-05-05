from logging import getLogger, Logger
from os import getenv, listdir

from disnake.abc import MISSING
from disnake.ext.commands import InteractionBot

from bard.bard import Bard


class Bot(InteractionBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bard: Bard = MISSING

        self.logger: Logger = getLogger("bot")

    async def setup_bard(self, session_id: str) -> Bard:
        """
        Set up the Bard instance. This should be called when the bot is ready.
        :param session_id: The 1PSID cookie from Google.
        :return: The Bard instance.
        """
        self.logger.info("Setting up Bard...")
        self.bard = await Bard().initialize(session_id)

        return self.bard

    def __load_extensions(self):
        """
        Load the extensions.
        """
        self.logger.info("Loading extensions...")

        for extension in listdir("bot/cogs"):
            if not extension.endswith(".py"):
                continue

            self.load_extension(f"bot.cogs.{extension[:-3]}")
            self.logger.info("Loaded extension %s", extension)

    async def on_ready(self):
        await self.setup_bard(getenv("SESSION_ID"))

        self.__load_extensions()
