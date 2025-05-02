# Standard Library
import json
from pathlib import Path

# Alliance Auth (External Libs)
from eveuniverse.models import EveMoon, EveType
from eveuniverse.tools.testdata import load_testdata_from_dict


def _load_eveuniverse_from_file():
    with open(Path(__file__).parent / "eveuniverse.json", encoding="utf-8") as fp:
        return json.load(fp)


eveuniverse_testdata = _load_eveuniverse_from_file()


def load_eveuniverse():
    load_testdata_from_dict(eveuniverse_testdata)
