# Standard Library
import csv
import gc
import tempfile
import zipfile
from abc import ABC, abstractmethod
from decimal import Decimal
from pathlib import Path

# Django
from django.conf import settings
from django.utils import timezone

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Ledger
from ledger import __title__
from ledger.helpers.alliance import AllianceData
from ledger.helpers.corporation import CorporationData
from ledger.models.corporationaudit import (
    CorporationAudit,
    CorporationWalletJournalEntry,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def int_or_none(val) -> int | None:
    """Convert value to int or return None."""
    if val is None or val == "":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def file_to_zip(source_file: Path, destination: Path) -> Path:
    """Create a zip archive from a file."""
    destination.mkdir(parents=True, exist_ok=True)
    zip_file = (destination / source_file.name).with_suffix(".zip")
    with zipfile.ZipFile(
        file=zip_file, mode="w", compression=zipfile.ZIP_DEFLATED
    ) as my_zip:
        my_zip.write(filename=source_file, arcname=source_file.name)
    logger.info("Created export file: %s", zip_file)
    return zip_file


def default_destination() -> Path:
    """Return default destination path."""
    return (
        Path(settings.BASE_DIR) / str(CorporationAudit._meta.app_label) / "data_exports"
    )


def export_ledger_to_archive(
    ledger_type: str, entity_id: int, division_id: int, year: int, month: int
) -> str:
    """Export data for given ledger into a zipped file in destination."""
    exporter = LedgerCSVExporter.create_exporter(
        ledger_type, entity_id, division_id, year, month
    )
    try:
        with tempfile.TemporaryDirectory() as temp_dirname:
            csv_file = exporter.write_to_file(temp_dirname)
            destination = default_destination()
            zip_file_path = file_to_zip(csv_file, destination)
    except ValueError as ve:
        logger.debug("Error exporting ledger to archive: %s", ve)
        return f"{ve}"
    gc.collect()
    return str(zip_file_path)


class LedgerCSVExporter(ABC):
    """CSV exporter for ledger data."""

    def __init__(self):
        # _now is available for subclasses if needed
        self._now = timezone.now()
        if not hasattr(self, "topic"):
            raise NotImplementedError("Subclasses must define 'topic' attribute")

    @property
    def output_basename(self) -> Path:
        """Return the base name for the output file."""
        app_label = str(CorporationAudit._meta.app_label)
        # Try to discover an entity id from known attributes set by exporters
        entity_id = (
            getattr(self, "corporation_id", None)
            or getattr(self, "alliance_id", None)
            or ""
        )
        division_id = getattr(self, "division_id", None) or ""
        year = getattr(self, "year", "") or ""
        month = getattr(self, "month", "") or ""

        export_key = self.encoder(entity_id, division_id, year, month)
        if not export_key:
            raise ValueError("Could not create export key for output basename")
        # pylint: disable=no-member
        return Path(f"{app_label}_{self.topic}_{export_key}")

    @staticmethod
    def encoder(
        entity_id: int, division_id: int = None, year: int = None, month: int = None
    ) -> str | None:
        """Create a compact export key: "<entity_id>:<division_id>:<year>:<month>" encoded as hex"""
        try:
            parts = [
                "" if v is None else str(v)
                for v in (entity_id, division_id, year, month)
            ]
            key = ":".join(parts)
            return key.encode("utf-8").hex()
        # pylint: disable=broad-except
        except Exception:
            return None

    @staticmethod
    def decoder(key: str) -> tuple[int | None, int | None, int | None, int | None]:
        """Decode a compact export key from hex to (entity_id, division_id, year, month).

        Returns ints when values are numeric, otherwise None for missing/empty values.
        """
        try:
            packed = bytes.fromhex(key).decode("utf-8")
            key_parts = packed.split(":")

            entity_id = int_or_none(key_parts[0]) if len(key_parts) > 0 else None
            division_id = int_or_none(key_parts[1]) if len(key_parts) > 1 else None
            year = int_or_none(key_parts[2]) if len(key_parts) > 2 else None
            month = int_or_none(key_parts[3]) if len(key_parts) > 3 else None
            return entity_id, division_id, year, month
        # pylint: disable=broad-except
        except Exception:
            return None, None, None, None

    @abstractmethod
    def create_data_export(self) -> list[dict]:
        """Generate data export."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def has_data(self) -> bool:
        """Check if there is data to export."""
        raise NotImplementedError()

    def output_path(self, destination: str) -> Path:
        """Return output path for this export."""
        return Path(destination) / self.output_basename.with_suffix(".csv")

    def _extract_entity_info(self, item: dict) -> dict:
        """Extract entity information from the data item."""
        entity = item.get("entity")
        if not entity:
            return {"entity_id": "", "entity_name": "", "entity_type": ""}

        return {
            "entity_id": getattr(entity, "entity_id", ""),
            "entity_name": getattr(entity, "entity_name", ""),
            "entity_type": getattr(entity, "type", ""),
        }

    def _clean_decimal_value(self, value) -> str:
        """Clean decimal values from the Decimal() wrapper."""
        if (
            isinstance(value, str)
            and value.startswith('Decimal("')
            and value.endswith('")')
        ):
            # Extract the value from Decimal("value") format
            return value[9:-2]  # Remove 'Decimal("' and '")')
        if isinstance(value, Decimal):
            return str(value)
        return str(value) if value is not None else "0"

    def _extract_ledger_data(self, item: dict) -> dict:
        """Extract ledger financial data from the item."""
        ledger = item.get("ledger", {})

        return {
            "bounty": self._clean_decimal_value(ledger.get("bounty", "0")),
            "ess": self._clean_decimal_value(ledger.get("ess", "0")),
            "miscellaneous": self._clean_decimal_value(
                ledger.get("miscellaneous", "0")
            ),
            "costs": self._clean_decimal_value(ledger.get("costs", "0")),
            "total": self._clean_decimal_value(ledger.get("total", "0")),
            "mining": self._clean_decimal_value(
                ledger.get("mining", "0")
            ),  # Include mining if present
        }

    def write_to_file(self, destination: Path) -> Path:
        """Write ledger data to CSV file."""
        output_file = self.output_path(destination)

        # Define CSV headers
        headers = [
            "entity_id",
            "entity_name",
            "entity_type",
            "bounty",
            "ess",
            "miscellaneous",
            "costs",
            "mining",
            "total",
        ]

        if self.has_data is False:
            raise ValueError("No data to export")

        with output_file.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()

            for item in self.create_data_export():
                if not item:  # Skip empty items
                    continue

                # Extract entity and ledger information
                entity_info = self._extract_entity_info(item)
                ledger_data = self._extract_ledger_data(item)

                # Combine all data into a single row
                row_data = {**entity_info, **ledger_data}

                writer.writerow(row_data)
        logger.info(
            f"Exported {len(self.create_data_export())} ledger entries to {output_file}"
        )
        return output_file

    @classmethod
    # pylint: disable=too-many-positional-arguments
    def create_exporter(
        cls,
        ledger_type: str,
        entity_id: int,
        division_id: int = None,
        year: int = None,
        month: int = None,
    ):
        """Create a LedgerCSVExporter instance."""
        if ledger_type == "corporation":
            if entity_id is None:
                raise ValueError("corporation_id must be provided")
            return CorporationExporter(
                entity_id=entity_id, division_id=division_id, year=year, month=month
            )

        if ledger_type == "alliance":
            if entity_id is None:
                raise ValueError("alliance_id must be provided")
            return AllianceExporter(entity_id=entity_id, year=year, month=month)

        raise ValueError("Invalid ledger_type")

    def gather_export_files(self) -> list[dict]:
        """Gather export files in the destination folder and parse metadata from filenames.
        Expected filename format (without suffix):
            <app_label>_<topic>_<export_key_hex>

        The export_key_hex is a hex encoding of the UTF-8 string
            "<entity_id>:<division_id>:<year>:<month>"
        Only files matching this new format are considered.

        This is an instance method and will filter files for the exporter instance
        by using the instance's corporation_id or alliance_id attribute.
        """
        # Determine the entity id for this exporter instance. Exporter subclasses
        instance_entity_id = getattr(self, "corporation_id", None) or getattr(
            self, "alliance_id", None
        )
        if instance_entity_id is None:
            raise ValueError(
                "Exporter instance must have 'corporation_id' or 'alliance_id' to gather files"
            )

        destination_folder = default_destination()
        results: list[dict] = []

        # If destination folder doesn't exist, return empty
        if not destination_folder.exists():
            return results

        existing_files = list(
            destination_folder.glob(f"{str(CorporationAudit._meta.app_label)}_*.zip")
        )

        if not existing_files:
            return results

        for file in existing_files:
            name = file.with_suffix("").name
            parts = name.split("_")
            topic = parts[1] if len(parts) > 1 else ""

            # Only attempt to parse the export hex key (third segment).
            if len(parts) <= 2:
                continue

            key = parts[2]
            entity_id, division_id, year, month = LedgerCSVExporter.decoder(key)

            # Only include files matching the requested entity id and topic
            if entity_id is None or entity_id != instance_entity_id:
                continue

            # Also filter by exporter topic so we don't mix corporation/alliance exports
            if topic != getattr(self, "topic", ""):
                continue

            try:
                last_updated = timezone.datetime.fromtimestamp(
                    file.stat().st_mtime, tz=timezone.utc
                )
            # pylint: disable=broad-except
            except Exception:
                logger.debug("Could not get last modified time for file %s", file)
                last_updated = None

            results.append(
                {
                    "topic": topic,
                    "entity_id": entity_id,
                    "division_id": (
                        division_id if division_id is not None else "All Divisions"
                    ),
                    "year": year,
                    "month": month if month is not None else "All Months",
                    "last_updated": last_updated,
                    "hash": key,
                }
            )

        return results


class CorporationExporter(LedgerCSVExporter):
    """CSV Exporter for Corporation Ledger Data."""

    topic = "corporation-ledger"

    def __init__(
        self,
        entity_id: int,
        division_id: int = None,
        year: int = None,
        month: int = None,
    ):
        super().__init__()
        self.corporation_id = entity_id
        self.division_id = division_id
        self.year = year
        self.month = month

    @property
    def has_data(self) -> bool:
        """Check if there is data to export."""
        return CorporationWalletJournalEntry.objects.filter(
            division__corporation__corporation__corporation_id=self.corporation_id
        ).exists()

    def create_data_export(
        self,
        corporation_id: int = None,
        division_id: int = None,
        year: int = None,
        month: int = None,
    ) -> list[dict]:
        """Generate data export for corporation ledger."""
        report_corporation_id = (
            corporation_id if corporation_id is not None else self.corporation_id
        )
        report_division_id = (
            division_id if division_id is not None else self.division_id
        )
        report_year = year if year is not None else self.year
        report_month = month if month is not None else self.month

        try:
            corporation = CorporationAudit.objects.get(
                corporation__corporation_id=report_corporation_id
            )
            # Create CorporationData inside the task
            ledger_data = CorporationData(
                corporation=corporation,
                division_id=report_division_id,
                year=report_year,
                month=report_month,
            )
            return ledger_data.generate_data_export()
        except CorporationAudit.DoesNotExist as exc:
            raise ValueError("Corporation not found") from exc


class AllianceExporter(LedgerCSVExporter):
    """CSV Exporter for Alliance Ledger Data."""

    topic = "alliance-ledger"

    def __init__(self, entity_id: int, year: int = None, month: int = None):
        super().__init__()
        self.alliance_id = entity_id
        self.year = year
        self.month = month

    @property
    def has_data(self) -> bool:
        """Check if there is data to export."""
        corporations = CorporationAudit.objects.filter(
            corporation__alliance__alliance_id=self.alliance_id
        ).values_list("corporation__corporation_id", flat=True)

        if not corporations:
            return False

        return CorporationWalletJournalEntry.objects.filter(
            division__corporation__corporation__corporation_id__in=corporations
        ).exists()

    def create_data_export(
        self, alliance_id: int = None, year: int = None, month: int = None
    ) -> list[dict]:
        """Generate data export for alliance ledger."""
        report_alliance_id = (
            alliance_id if alliance_id is not None else self.alliance_id
        )
        report_year = year if year is not None else self.year
        report_month = month if month is not None else self.month

        try:
            alliance = EveAllianceInfo.objects.get(alliance_id=report_alliance_id)
            ledger_data = AllianceData(
                alliance=alliance,
                year=report_year,
                month=report_month,
                request=None,
            )
            return ledger_data.generate_data_export()
        except EveAllianceInfo.DoesNotExist as exc:
            raise ValueError("Alliance not found") from exc
