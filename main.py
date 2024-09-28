import argparse
import os
from observability import get_logger
from bot import DiscordClient, MessageUpdater, MessageUpdate
from scrape import filter_listings, scrape_listings
from config import (
    save_config,
    load_config,
    default_config,
    Config,
    ListingConfig,
)


logger = get_logger("main")


class PfMessageUpdater(MessageUpdater):
    def __init__(self, config: Config):
        self.config = config
        self.listings = {}

    def update(self):
        logger.info("Updating listings")
        fetched_listings = scrape_listings(self.config.url)
        self.listings = {}
        for configured_listing in self.config.listings:
            filtered_fetched_listings = filter_listings(
                fetched_listings,
                configured_listing.duty_name,
                configured_listing.data_centre,
            )
            self.listings[configured_listing.name] = filtered_fetched_listings

    def messages(self):
        for configured_listing in self.config.listings:
            update = MessageUpdate(
                configured_listing.channel_id,
                configured_listing.message_id,
                self.listings[configured_listing.name],
                configured_listing.duty_name,
            )
            yield update


def create_default_config(config_path: str):
    config = default_config()
    save_config(config, config_path)


def create_listing_message(config_path: str, config: Config):
    name = input(
        "Enter a name for the listing (unique, not visible) (e.g. ChaosM4S): "
    )

    duty_name = input(
        "Enter duty name to filter by "
        "(e.g. AAC Light-heavyweight M4 (Savage)): "
    )

    data_centre = input("Enter the data center to filter by (e,g. Chaos): ")

    channel_id = input(
        "Enter the id of the channel where the message will live: "
    )

    logger.info("Validating...")
    try:
        configured_listing = ListingConfig(
            name=name,
            duty_name=duty_name,
            data_centre=data_centre,
            channel_id=int(channel_id),
            message_id=0,
        )
    except Exception:
        logger.error("Validation failed!! No changes made!")
        raise

    logger.info(
        "Will try to send a test message with the retrieved"
        f" filter to channel {channel_id}"
    )

    pf_data = scrape_listings(config.url)
    listings = filter_listings(
        pf_data, configured_listing.duty_name, configured_listing.data_centre
    )

    client = DiscordClient(config.token)
    message_id = client.run_send_message(
        configured_listing.channel_id, listings, duty_name
    )
    if message_id is not None:
        logger.info(f"Successfully created message {message_id}")
    else:
        logger.critical("Failed to send a message! Aborting! No changes made!")
        raise RuntimeError("Failed to send a message to given channel id")

    logger.info("All looks good. Adding listing to configuration.")
    configured_listing.message_id = message_id
    config.listings.append(configured_listing)
    save_config(config, config_path)


def run_bot(config: Config):
    updater = PfMessageUpdater(config)
    client = DiscordClient(config.token)
    client.run_update_messages_periodically(updater, config.period)


def main() -> int:
    parser = argparse.ArgumentParser(
        description='"Simple" party finder discord bot'
    )

    parser.add_argument("config_path", help="Path to the configuration file")
    parser.add_argument(
        "--setup-message",
        action="store_true",
        help=(
            "Run the bot once, sending a single message and "
            "updating the config to track it."
        ),
    )
    parser.add_argument(
        "--setup-config",
        action="store_true",
        help=(
            "Don't run the bot. Instead, create a default "
            "config for the user to fill out."
        ),
    )

    args = parser.parse_args()

    if args.setup_config:
        logger.info(f"Creating a default config on {args.config_path}")
        create_default_config(args.config_path)
        return 0

    if not os.path.exists(args.config_path):
        logger.critical(f"Config file {args.config_path} does not exist.")
        return 1
    config = load_config(args.config_path)

    if args.setup_message:
        logger.info(
            f"Creating a new message. This will update {args.config_path}"
        )
        create_listing_message(args.config_path, config)
        return 0

    logger.info(
        "Running regular bot. Will monitor pf listings and update messages."
    )
    run_bot(config)
    return 0


if __name__ == "__main__":
    exit(main())
