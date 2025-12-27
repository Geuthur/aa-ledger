"""Generate AllianceAuth test objects from allianceauth.json."""

# Standard Library
import json
from pathlib import Path


def _load_planetary_data():
    with open(Path(__file__).parent / "planetary.json", encoding="utf-8") as fp:
        return json.load(fp)


_planetary_data = _load_planetary_data()
