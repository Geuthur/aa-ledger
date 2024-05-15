# Ledger module for AllianceAuth.

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Geuthur/aa-ledger/master.svg)](https://results.pre-commit.ci/latest/github/Geuthur/aa-ledger/master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://github.com/Geuthur/aa-ledger/actions/workflows/autotester.yml/badge.svg)](https://github.com/Geuthur/aa-ledger/actions/workflows/autotester.yml)

## Includes

- Graphical Overview
- Ratting,Mining,Trading
- Character Ledger
- Corporation Ledger

## Upcoming

- Corp Tax
- Events Calender

## Installation

### Step 1 - Install the Package

Make sure you're in your virtual environment (venv) of your Alliance Auth then install the pakage.

```shell
pip install aa-ledger
```

### Step 2 - Configure Alliance Auth

- Add `'ledger',` to your `INSTALLED_APPS` in your projects `local.py`

### Step 3 - Add the Scheduled Tasks

To set up the Scheduled Tasks add following code to your `local.py`

```python
CELERYBEAT_SCHEDULE["ledger_character_audit_update_all"] = {
    "task": "ledger.tasks.update_all_characters",
    "schedule": crontab(hour="*/1"),
}
CELERYBEAT_SCHEDULE["ledger_corporation_audit_update_all"] = {
    "task": "ledger.tasks.update_all_corps",
    "schedule": crontab(hour="*/1"),
}
```

Optional you can set own Logger for the Ledger\
You need to set up `LOGGER_USE = True` in `local.py` and add the following code same as above

```python
LOGGING_LEDGER = {
    "handlers": {
        "ledger_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "log/ledger.log"),
            "formatter": "verbose",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
        },
    },
    "loggers": {
        "ledger": {
            "handlers": ["ledger_file", "console"],
            "level": "DEBUG",
        },
    },
}
LOGGING["handlers"].update(LOGGING_LEDGER["handlers"])
LOGGING["loggers"].update(LOGGING_LEDGER["loggers"])
```

### Step 4 - Migration to AA

```shell
python manage.py collectstatic
python manage.py migrate
```

## Highlights

![Screenshot 2024-05-14 121014](https://github.com/Geuthur/aa-ledger/assets/761682/d0604260-b672-4bf5-a16a-d1b90557744d)

![Screenshot 2024-05-14 121025](https://github.com/Geuthur/aa-ledger/assets/761682/f8f20e6a-d37d-4a50-a1aa-8615c0f8e88b)

![Screenshot 2024-05-14 120944](https://github.com/Geuthur/aa-ledger/assets/761682/2d695369-1331-4be9-8adf-9c6dabf80dda)

![Screenshot 2024-05-14 121001](https://github.com/Geuthur/aa-ledger/assets/761682/463b9921-150c-42c1-8c3e-eee0f5cfc2bb)

> \[!CAUTION\]
> Contributing
> Make sure you have signed the License Agreement by logging in at https://developers.eveonline.com before submitting any pull requests. All bug fixes or features must not include extra superfluous formatting changes.
