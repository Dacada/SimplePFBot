from typing import Optional
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
import traceback
import discord
import asyncio
import logging
from scrape import Listing, PartySlot, SlotState, SlotType, RoleType, Role
from config import EmbedCustomization


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
    def __init__(self, token: str, embed_custom: EmbedCustomization):
        intents = discord.Intents.default()
        self.client = discord.Client(intents=intents)
        self.token = token
        self.embed_custom = embed_custom
        self.logger = logging.getLogger("bot")
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
        self.client.run(self.token, log_handler=None)
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
                color=self.embed_custom.color,
                description=self.embed_custom.no_party_finders_message,
            )

        embed = discord.Embed(title=title, color=self.embed_custom.color)

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
            embed.add_field(
                name=f"{self.embed_custom.updated_emoji} {listing.updated}",
                value=f"{self.embed_custom.expires_emoji} {listing.expires}",
            )

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
        return " ".join(self._get_emoji_by_party_slot(slot) for slot in party)

    def _get_emoji_by_party_slot(self, slot: PartySlot) -> str:
        if slot.state == SlotState.FILLED:
            if len(slot.roles) == 0:
                self.logger.warn(
                    "No roles for a filled slot? Will use slot type instead."
                )
                return self._get_emoji_filled_by_slot_type(slot.slot_type)
            if len(slot.roles) > 1:
                self.logger.warn(
                    "More than one role for a filled slot? Will use first role"
                )
            return self._get_emoji_filled(slot.roles[0])
        elif slot.state == SlotState.OPEN:
            return self._get_emoji_open(slot.roles)

    def _get_emoji_open(self, roles: list[Role]) -> str:
        if not roles:
            return self.embed_custom.free_slots.other

        emoji = self._get_emoji_open_from_single_role(roles)
        if emoji is not None:
            return emoji

        emoji = self._get_emoji_open_from_role_types(roles)
        if emoji is not None:
            return emoji

        emoji = self._get_emoji_open_from_slot_types(roles)
        if emoji is not None:
            return emoji

        # fallback
        self.logger.warning(
            f"Cannot identify emoji for role combination: {roles}"
        )
        return self.embed_custom.free_slots.other

    def _get_emoji_open_from_single_role(self, roles: list[Role]) -> Optional[str]:
        if len(roles) == 1:
            return getattr(self.embed_custom.free_slots, roles[0].value.lower(), None)
        return None

    def _get_emoji_open_from_role_types(self, roles: list[Role]) -> Optional[str]:
        role_types = set(x.get_role_type() for x in roles)

        if RoleType.OTHER in role_types:
            return self.embed_custom.free_slots.other

        if len(role_types) == 1:
            emoji = getattr(
                self.embed_custom.free_slots,
                next(iter(role_types)).value.lower(),
                None,
            )
            return emoji

        return None

    def _get_emoji_open_from_slot_types(self, roles: list[Role]) -> Optional[str]:
        slot_types = set(x.get_slot_type() for x in roles)

        if SlotType.OTHER in slot_types:
            return self.embed_custom.free_slots.other

        if len(slot_types) == 1:
            emoji = getattr(
                self.embed_custom.free_slots,
                next(iter(slot_types)).value.lower(),
                None,
            )
            if emoji is not None:
                return emoji

        if len(slot_types) == 2:
            if SlotType.DPS in slot_types:
                if SlotType.HEALER in slot_types:
                    return self.embed_custom.free_slots.dps_healer
                if SlotType.TANK in slot_types:
                    return self.embed_custom.free_slots.dps_tank
            if (
                SlotType.HEALER in slot_types
                and SlotType.TANK in slot_types
            ):
                return self.embed_custom.free_slots.healer_tank

        if len(slot_types) == 3:
            return self.embed_custom.free_slots.dps_healer_tank

        return None

    def _get_emoji_filled_by_slot_type(self, slot_type: SlotType) -> str:
        if slot_type == SlotType.DPS:
            return self._get_emoji_filled(Role.MNK)
        if slot_type == SlotType.HEALER:
            return self._get_emoji_filled(Role.WHM)
        if slot_type == SlotType.TANK:
            return self._get_emoji_filled(Role.PLD)
        return self.embed_custom.filled_slots.other

    def _get_emoji_filled(self, role: Role) -> str:
        return getattr(
            self.embed_custom.filled_slots,
            role.value.lower(),
            self.embed_custom.filled_slots.other,
        )


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
    exit(main())
