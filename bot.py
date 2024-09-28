from typing import Optional
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
import traceback
import discord
import asyncio
from observability import get_logger, ColoredFormatter
from scrape import Listing, PartySlot, SlotState, SlotType, Role


@dataclass
class MessageUpdate:
    channel_id: int
    message_id: int
    content: list[Listing]
    title: str


class MessageUpdater(ABC):
    @abstractmethod
    def update(self):
        """
        Update the data with which to generate messages.
        """
        pass

    @abstractmethod
    def messages(self) -> Iterable[MessageUpdate]:
        """
        Retrieve all the messages that need updating and their new content.
        """
        pass


class DiscordClient:
    def __init__(self, token: str):
        intents = discord.Intents.default()
        self.client = discord.Client(intents=intents)
        self.token = token
        self.logger = get_logger("bot")
        self.result = None

    def run_send_message(
        self, channel_id: int, message: list[Listing], title: str
    ) -> Optional[int]:
        """
        Start up the bot. Send a single message. And end it.
        """

        @self.client.event
        async def on_ready():
            try:
                await self._send_message(channel_id, message, title)
            except Exception:
                self.logger.error(f"{traceback.format_exc()}")
                exit(1)

        return self._run()

    def run_update_messages_periodically(
        self, messages: MessageUpdater, period: int = 5
    ):
        @self.client.event
        async def on_ready():
            try:
                await self._update_messages_periodically(messages, period)
            except Exception:
                self.logger.error(f"{traceback.format_exc()}")
                exit(1)

        self._run()

    def _run(self):
        self.client.run(self.token, log_formatter=ColoredFormatter())
        return self.result

    async def _send_message(
        self, channel_id: int, message: list[Listing], title: str
    ):
        channel = self.client.get_channel(channel_id)
        if channel is None:
            self.logger.error(f"Channel with ID {channel_id} not found.")
            await self.client.close()
            return None

        self.logger.debug("Create message...")
        message = await channel.send(embed=self._create_embed(message, title))

        self.result = message.id
        await self.client.close()

    async def _update_messages_periodically(
        self, messages: MessageUpdater, period: int
    ):
        self.logger.debug("Update messages...")
        while True:
            messages.update()
            for info in messages.messages():
                self.logger.debug(f"Handling: {info}")
                channel = self.client.get_channel(info.channel_id)
                if channel is None:
                    self.logger.warning(
                        f"Channel with ID {info.channel_id} not found."
                    )
                    continue

                try:
                    message = await channel.fetch_message(info.message_id)
                except discord.NotFound:
                    self.logger.warning(
                        f"Message with ID {info.message_id} not found."
                    )
                    continue
                self.logger.info(
                    f"Modifying message with ID: {info.message_id}"
                )

                await message.edit(
                    embed=self._create_embed(info.content, info.title)
                )

            await asyncio.sleep(period)

    def _create_embed(
        self, listings: list[Listing], title: str
    ) -> discord.Embed:
        if not listings:
            return discord.Embed(
                title=title,
                color=0xB7406A,
                description="No party finders! Please, open one! 😡",
            )

        embed = discord.Embed(title=title, color=0xB7406A)

        for i, listing in enumerate(
            sorted(listings, reverse=True, key=lambda x: x.expires)
        ):
            # Max of 25 fields, but we only have multiples of 3
            if embed.fields and len(embed.fields) == 24:
                break

            party = self._emojify_party(listing.party)
            tags, desc = self._extract_description_tags(listing.description)

            embed.add_field(name=listing.creator, value=party, inline=True)
            embed.add_field(name=tags, value=desc, inline=True)
            embed.add_field(name=listing.updated, value=listing.expires)

            if len(embed) > 6000:
                embed.remove_field(-1)
                embed.remove_field(-1)
                embed.remove_field(-1)
                break

        remaining = len(listings) - i - 1
        if remaining:
            embed.set_footer(
                text=f"And {remaining // 3} more party finders that didn't fit"
            )
            if len(embed) > 5999:
                remaining += 1
                embed.remove_field(-1)
                embed.remove_field(-1)
                embed.remove_field(-1)
                embed.set_footer(
                    text=f"And {remaining // 3} more party finders that didn't fit"
                )

        return embed

    def _extract_description_tags(
        self, full_description: str
    ) -> tuple[str, str]:
        last_bracket_pos = full_description.rfind("]")
        tags = full_description[: last_bracket_pos + 1].strip()
        desc = full_description[last_bracket_pos + 1 :].strip()
        return tags, desc

    def _emojify_party(self, party: list[PartySlot]) -> str:
        return "".join(self._get_emoji_by_party_slot(slot) for slot in party)

    def _get_emoji_by_party_slot(self, slot: PartySlot) -> str:
        if slot.state == SlotState.FILLED:
            if len(slot.roles) == 0:
                self.logger.warn(
                    "No roles for a filled slot? Will use slot type instead."
                )
                return self._get_emoji_by_slot_type(slot.slot_type, slot.roles)
            if len(slot.roles) > 1:
                self.logger.warn(
                    "More than one role for a filled slot? Will use first role"
                )
            return self._get_emoji_by_role(slot.roles[0])
        elif slot.state == SlotState.OPEN:
            return self._get_emoji_by_slot_type(slot.slot_type, slot.roles)

    def _get_emoji_by_slot_type(
        self, slot_type: SlotType, roles: list[Role]
    ) -> str:
        if slot_type == SlotType.DPS:
            return "❤️"
        elif slot_type == SlotType.HEALER:
            return "💚"
        elif slot_type == SlotType.TANK:
            return "💙"
        else:
            return "🩶"

    def _get_emoji_by_role(self, role: Role) -> str:
        return "💖"


def main() -> int:
    @dataclass
    class MockedListing:
        creator: str
        party: list[PartySlot]
        description: str
        updated: str
        expires: str

    mocked_party = [
        PartySlot(
            state=SlotState.FILLED,
            slot_type=SlotType.DPS,
            roles=[Role.MCH],
        ),
        PartySlot(
            state=SlotState.FILLED,
            slot_type=SlotType.HEALER,
            roles=[Role.AST],
        ),
        PartySlot(
            state=SlotState.FILLED,
            slot_type=SlotType.TANK,
            roles=[Role.GNB],
        ),
        PartySlot(
            state=SlotState.OPEN,
            slot_type=SlotType.TANK,
            roles=[Role.PLD, Role.WAR, Role.DRK, Role.GNB],
        ),
        PartySlot(
            state=SlotState.OPEN,
            slot_type=SlotType.HEALER,
            roles=[Role.WHM, Role.SCH, Role.AST, Role.SGE],
        ),
        PartySlot(
            state=SlotState.OPEN,
            slot_type=SlotType.DPS,
            roles=[Role.SAM],
        ),
        PartySlot(
            state=SlotState.OPEN,
            slot_type=SlotType.OTHER,
            roles=[Role.SAM, Role.WHM],
        ),
    ]

    mocked_listing_1 = MockedListing(
        creator="creator 1",
        party=mocked_party,
        description="[Tag][Another Tag] The Description",
        updated="updated 1",
        expires="expires 1",
    )

    mocked_listing_2 = MockedListing(
        creator="creator 2",
        party=mocked_party,
        description="[Tag][Another Tag] The Description",
        updated="updated 2",
        expires="expires 2",
    )

    token = ""
    client = DiscordClient(token)

    message = client.run_send_message(
        946078742357364786,
        [mocked_listing_1, mocked_listing_2],
        "AAC Light-heavyweight M4 (Savage)",
    )
    print(message)

    # class MessageUpdater:
    #     def __init__(self):
    #         self.update_count = 0

    #     def update(self):
    #         self.update_count += 1

    #     def messages(self):
    #         yield MessageUpdate(0, 0, [mocked_listing_1])
    #         yield MessageUpdate(0, 0, [mocked_listing_2])

    # client.run_update_messages_periodically(MessageUpdater())


if __name__ == "__main__":
    exit(main())
