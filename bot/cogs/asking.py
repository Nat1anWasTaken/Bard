from os import getenv

from disnake import Message, MessageInteraction, ButtonStyle, SelectOption
from disnake.abc import MISSING
from disnake.ext.commands import Cog
from disnake.ui import Button, StringSelect

from bard.response import Response
from bot.bot import Bot


def render(response: Response) -> dict:
    """
    Render a response. You can pass this to send().
    :param response: The response to render.
    :return: The rendered response.
    """
    message = {
        "content": response.content,
        "components": [
            Button(
                label="Google it",
                custom_id="google_it",
                style=ButtonStyle.gray,
                emoji="<:google:1104043088005050559>"
            ),
            Button(
                label="Reset conversation",
                custom_id="reset_conversation",
                style=ButtonStyle.gray,
                emoji="<:reset:1104043528335659059>"
            ),
            StringSelect(
                custom_id="choice",
                placeholder="View other drafts",
                options=[
                    SelectOption(
                        label=f"Option {i + 1}",
                        value=choice.choice_id,
                        description=choice.content[:100]
                    ) for i, choice in enumerate(response.choices)
                ]
            )
        ]
    }

    return message


class Asking(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.last_message: Message = MISSING

    @Cog.listener(name="on_message_interaction")
    async def on_message_interaction(self, interaction: MessageInteraction):
        if int(getenv("OWNER_ONLY")):
            if interaction.author.id != int(getenv("OWNER_ID")):
                return

        if interaction.data.custom_id == "reset_conversation":
            await interaction.response.send_message(content="Resetting conversation...")

            self.bot.bard.reset()

            await self.last_message.edit(components=[])

            return await interaction.edit_original_message(content="✅ Conversation reset.")

        elif interaction.data.custom_id == "choice":
            await interaction.response.defer()

            choice_id = interaction.values[0]

            self.bot.bard.choose(choice_id)

            return await interaction.edit_original_message(**render(self.bot.bard.last_response))

        elif interaction.data.custom_id == "google_it":
            return await interaction.response.send_message(
                content="Google it!",
                components=[
                    Button(
                        label=query,
                        url=f"https://google.com/search?q={query.replace(' ', '+')}",
                        style=ButtonStyle.link
                    ) for query in self.bot.bard.last_response.text_query[:-1]
                ],
                ephemeral=True
            )

    @Cog.listener(name="on_message")
    async def on_message(self, message: Message):
        if int(getenv("OWNER_ONLY")):
            if message.author.id != int(getenv("OWNER_ID")):
                return

        if not (self.bot.user.id in [member.id for member in message.mentions]):
            return  # The bot was not mentioned.

        await message.channel.trigger_typing()

        parsed_message = message.content.replace(self.bot.user.mention, "").strip()

        await self.bot.bard.ask(parsed_message)

        if self.last_message:
            await self.last_message.edit(components=[])

        self.last_message = await message.reply(**render(self.bot.bard.last_response), mention_author=True)


def setup(bot: Bot):
    bot.add_cog(Asking(bot))
