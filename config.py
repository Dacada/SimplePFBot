import json
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from scrape import DataCentre
import logging
from observability import LogLevel

logger = logging.getLogger("config")


class FilledSlotEmojiCollection(BaseModel):
    gla: str
    pgl: str
    mrd: str
    lnc: str
    arc: str
    cnj: str
    thm: str
    pld: str
    mnk: str
    war: str
    drg: str
    brd: str
    whm: str
    blm: str
    acn: str
    smn: str
    sch: str
    rog: str
    nin: str
    mch: str
    drk: str
    ast: str
    sam: str
    rdm: str
    blu: str
    gnb: str
    dnc: str
    rpr: str
    sge: str
    vpr: str
    pct: str
    other: str


class FreeSlotEmojiCollection(BaseModel):
    tank: str
    gla: Optional[str]
    mrd: Optional[str]
    pld: Optional[str]
    war: Optional[str]
    drk: Optional[str]
    gnb: Optional[str]

    healer: str
    regen_healer: Optional[str]
    cnj: Optional[str]
    whm: Optional[str]
    ast: Optional[str]
    shield_healer: Optional[str]
    sch: Optional[str]
    sge: Optional[str]

    dps: str
    melee_dps: Optional[str]
    pgl: Optional[str]
    lnc: Optional[str]
    mnk: Optional[str]
    drg: Optional[str]
    rog: Optional[str]
    nin: Optional[str]
    sam: Optional[str]
    rpr: Optional[str]
    vpr: Optional[str]
    ranged_dps: Optional[str]
    arc: Optional[str]
    brd: Optional[str]
    mch: Optional[str]
    dnc: Optional[str]
    magical_dps: Optional[str]
    thm: Optional[str]
    blm: Optional[str]
    acn: Optional[str]
    smn: Optional[str]
    rdm: Optional[str]
    blu: Optional[str]
    pct: Optional[str]

    dps_healer: str
    dps_tank: str
    healer_tank: str
    dps_healer_tank: str

    other: str


class EmbedCustomization(BaseModel):
    filled_slots: FilledSlotEmojiCollection
    free_slots: FreeSlotEmojiCollection
    no_party_finders_message: str
    color: int
    updated_emoji: str
    expires_emoji: str


class ListingConfig(BaseModel):
    name: str
    duty_name: str
    data_centre: DataCentre
    channel_id: int
    message_id: int


class LoggingConfig(BaseModel):
    level: LogLevel
    file: Optional[str]


class Config(BaseModel):
    url: str
    token: str
    period: int
    listings: list[ListingConfig]
    embed_custom: EmbedCustomization
    logging: LoggingConfig


def _enum_encoder(obj):
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def save_config(config: Config, file_path: str):
    with open(file_path, "w") as f:
        json.dump(config.dict(), f, indent=4, default=_enum_encoder)
    logger.info(f"Config saved to {file_path}")


def load_config(file_path: str) -> Config:
    with open(file_path, "r") as f:
        data = json.load(f)

    res = Config(**data)
    logger.info(f"Config loaded from {file_path}")
    return res


def default_config() -> Config:
    return Config(
        logging=LoggingConfig(
            level=LogLevel.INFO,
            file="bot.log",
        ),
        url="https://xivpf.com/listings",
        token="ENTER THE BOT TOKEN HERE",
        period=30,
        listings=[],
        embed_custom=EmbedCustomization(
            updated_emoji="⏱️",
            expires_emoji="⏳",
            color=0xB7406A,
            no_party_finders_message="No party finders! Please, open one! 😡",
            filled_slots=FilledSlotEmojiCollection(
                gla="🟦",
                mrd="🟦",
                pld="🟦",
                war="🟦",
                drk="🟦",
                gnb="🟦",
                cnj="🟩",
                whm="🟩",
                ast="🟩",
                sch="🟩",
                sge="🟩",
                pgl="🟥",
                mnk="🟥",
                lnc="🟥",
                drg="🟥",
                rog="🟥",
                nin="🟥",
                sam="🟥",
                rpr="🟥",
                vpr="🟥",
                arc="🟥",
                brd="🟥",
                mch="🟥",
                dnc="🟥",
                thm="🟥",
                blm="🟥",
                acn="🟥",
                smn="🟥",
                rdm="🟥",
                blu="🟥",
                pct="🟥",
                other="⬛",
            ),
            free_slots=FreeSlotEmojiCollection(
                tank="💙",
                gla="💙",
                mrd="💙",
                pld="💙",
                war="💙",
                drk="💙",
                gnb="💙",
                healer="💚",
                regen_healer="💚",
                cnj="💚",
                whm="💚",
                ast="💚",
                shield_healer="💚",
                sch="💚",
                sge="💚",
                dps="❤️",
                melee_dps="❤️",
                pgl="❤️",
                mnk="❤️",
                lnc="❤️",
                drg="❤️",
                rog="❤️",
                nin="❤️",
                sam="❤️",
                rpr="❤️",
                vpr="❤️",
                ranged_dps="❤️",
                arc="❤️",
                brd="❤️",
                mch="❤️",
                dnc="❤️",
                magical_dps="❤️",
                thm="❤️",
                blm="❤️",
                acn="❤️",
                smn="❤️",
                rdm="❤️",
                blu="❤️",
                pct="❤️",
                dps_healer="💛",
                dps_tank="💜",
                healer_tank="🩵",
                dps_healer_tank="🤍",
                other="🖤",
            ),
        ),
    )
