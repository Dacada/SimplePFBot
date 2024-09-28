import requests
from bs4 import BeautifulSoup
from enum import Enum
from dataclasses import dataclass
from observability import get_logger


class SlotState(Enum):
    FILLED = "filled"
    OPEN = "open"


class SlotType(Enum):
    DPS = "dps"
    HEALER = "healer"
    TANK = "tank"
    OTHER = "other"


class DutyType(Enum):
    CROSS = "cross"
    LOCAL = "local"


class Role(Enum):
    GLA = "GLA"
    PGL = "PGL"
    MRD = "MRD"
    LNC = "LNC"
    ARC = "ARC"
    CNJ = "CNJ"
    THM = "THM"
    PLD = "PLD"
    MNK = "MNK"
    WAR = "WAR"
    DRG = "DRG"
    BRD = "BRD"
    WHM = "WHM"
    BLM = "BLM"
    ACN = "ACN"
    SMN = "SMN"
    SCH = "SCH"
    ROG = "ROG"
    NIN = "NIN"
    MCH = "MCH"
    DRK = "DRK"
    AST = "AST"
    SAM = "SAM"
    RDM = "RDM"
    BLU = "BLU"
    GNB = "GNB"
    DNC = "DNC"
    RPR = "RPR"
    SGE = "SGE"
    VPR = "VPR"
    PCT = "PCT"
    BTN = "BTN"
    MIN = "MIN"
    FSH = "FSH"
    CRP = "CRP"
    BSM = "BSM"
    ARM = "ARM"
    GSM = "GSM"
    LTW = "LTW"
    WVR = "WVR"
    ALC = "ALC"
    CUL = "CUL"


class DataCentre(Enum):
    CRYSTAL = "Crystal"
    DYNAMIS = "Dynamis"
    LIGHT = "Light"
    MATERIA = "Materia"
    GAIA = "Gaia"
    METEOR = "Meteor"
    CHAOS = "Chaos"
    PRIMAL = "Primal"
    ELEMENTAL = "Elemental"
    MANA = "Mana"
    AETHER = "Aether"


class PfCategory(Enum):
    RAIDS = "Raids"
    DUTY_ROULETTE = "DutyRoulette"
    GATHERING_FORAYS = "GatheringForays"
    NONE = "None"
    DEEP_DUNGEONS = "DeepDungeons"
    FATES = "Fates"
    V_AND_C_DUNGEON_FINDER = "V&C Dungeon Finder"
    DUNGEONS = "Dungeons"
    TREASURE_HUNT = "TreasureHunt"
    THE_HUNT = "TheHunt"
    PVP = "Pvp"
    HIGH_END_DUTY = "HighEndDuty"
    TRIALS = "Trials"
    ADVENTURING_FORAYS = "AdventuringForays"
    GUILDHESTS = "Guildhests"


@dataclass
class PartySlot:
    state: SlotState
    slot_type: SlotType
    roles: list[Role]


@dataclass
class Listing:
    duty_name: str
    duty_type: DutyType
    description: str
    party: list[PartySlot]
    filled: int
    total: int
    item_level: int
    creator: str
    world: str
    expires: str
    updated: str
    data_centre: DataCentre
    pf_category: PfCategory


def filter_listings(
    listings: list[Listing], duty_name: str, data_centre: DataCentre
) -> list[Listing]:
    return [
        listing
        for listing in listings
        if listing.duty_name == duty_name
        and listing.data_centre == data_centre
    ]


def scrape_listings(url: str) -> list[Listing]:
    logger = get_logger("scraper")

    response = requests.get(url)
    try:
        response.raise_for_status()
    except Exception:
        logger.critical(f"Unable to access URL {url}")
        raise
    soup = BeautifulSoup(response.text, "html.parser")

    listings = []

    logger.debug("Parsing listings...")
    for listing_div in soup.find_all("div", class_="listing"):
        data_centre_str = listing_div["data-centre"]
        pf_category_str = listing_div["data-pf-category"]

        if data_centre_str in [
            v.value for v in DataCentre.__members__.values()
        ]:
            data_centre = DataCentre(data_centre_str)
        else:
            logger.error(f"Unexpected Data Centre: {data_centre_str}")
            data_centre = data_centre_str

        if pf_category_str in [
            v.value for v in PfCategory.__members__.values()
        ]:
            pf_category = PfCategory(pf_category_str)
        else:
            logger.error(f"Unexpected PF Category: {pf_category_str}")
            pf_category = pf_category_str

        duty_element = listing_div.find(
            "div", class_=["duty", "cross", "local"]
        )
        if "cross" in duty_element["class"]:
            duty_type = DutyType.CROSS
        else:
            duty_type = DutyType.LOCAL
        duty_name = duty_element.get_text(strip=True)

        description = listing_div.find("div", class_="description").get_text(
            strip=True
        )

        party_slots = []
        filled_count = int(
            listing_div.find("div", class_="total")
            .get_text(strip=True)
            .split("/")[0]
        )
        total_count = int(
            listing_div.find("div", class_="total")
            .get_text(strip=True)
            .split("/")[1]
        )

        for slot_div in listing_div.find("div", class_="party").find_all(
            "div", class_="slot"
        ):
            state = (
                SlotState.FILLED
                if "filled" in slot_div["class"]
                else SlotState.OPEN
            )
            slot_type_text = (
                "dps"
                if "dps" in slot_div["class"]
                else (
                    "healer"
                    if "healer" in slot_div["class"]
                    else "tank" if "tank" in slot_div["class"] else "other"
                )
            )
            slot_type = SlotType[slot_type_text.upper()]

            role_strings = slot_div["title"].split()
            roles = []
            for role_str in role_strings:
                if role_str in Role.__members__:
                    roles.append(Role[role_str])
                else:
                    logger.error(f"Unexpected role found: {role_str}")
                    roles.append(role_str)

            party_slots.append(PartySlot(state, slot_type, roles))

        item_level = int(
            listing_div.find("div", class_="value").get_text(strip=True)
        )
        creator = (
            listing_div.find("div", class_="item creator")
            .find("span", class_="text")
            .get_text(strip=True)
        )
        world = (
            listing_div.find("div", class_="item world")
            .find("span", class_="text")
            .get_text(strip=True)
        )
        expires = (
            listing_div.find("div", class_="item expires")
            .find("span", class_="text")
            .get_text(strip=True)
        )
        updated = listing_div.find("div", class_="item updated").get_text(
            strip=True
        )

        listing = Listing(
            duty_name,
            duty_type,
            description,
            party_slots,
            filled_count,
            total_count,
            item_level,
            creator,
            world,
            expires,
            updated,
            data_centre,
            pf_category,
        )
        listings.append(listing)

    return listings


# Example usage
def main() -> int:
    listings = scrape_listings("https://xivpf.com/listings")

    for listing in listings:
        print(listing)

    return 0


if __name__ == "__main__":
    exit(main())
