import json
from pydantic import BaseModel
from typing import List
from enum import Enum
from scrape import DataCentre
from observability import get_logger

logger = get_logger("config")


class ListingConfig(BaseModel):
    name: str
    duty_name: str
    data_centre: DataCentre
    channel_id: int
    message_id: int


class Config(BaseModel):
    url: str
    token: str
    period: int
    listings: List[ListingConfig]


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
        url="https://xivpf.com/listings",
        token="ENTER THE BOT TOKEN HERE",
        period=30,
        listings=[],
    )


if __name__ == "__main__":
    example_config = Config(
        url="https://example.com",
        token="super_secret_token",
        period=60,
        listings=[
            ListingConfig(
                name="a",
                duty_name="Raid",
                data_centre=DataCentre.CRYSTAL,
                channel_id=12345,
                message_id=67890,
            ),
            ListingConfig(
                name="b",
                duty_name="Dungeon",
                data_centre=DataCentre.AETHER,
                channel_id=98765,
                message_id=54321,
            ),
        ],
    )

    save_config(example_config, "/tmp/config.json")
    loaded_config = load_config("/tmp/config.json")

    print(loaded_config)
