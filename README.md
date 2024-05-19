# Ledger module for AllianceAuth.<a name="aa-ledger"></a>

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Geuthur/aa-ledger/master.svg)](https://results.pre-commit.ci/latest/github/Geuthur/aa-ledger/master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://github.com/Geuthur/aa-ledger/actions/workflows/autotester.yml/badge.svg)](https://github.com/Geuthur/aa-ledger/actions/workflows/autotester.yml)

- [AA Ledger](#aa-ledger)
  - [Features](#features)
  - [Upcoming](#upcoming)
  - [Installation](#features)
    - [Step 1 - Install the Package](#step1)
    - [Step 2 - Configure Alliance Auth](#step2)
    - [Step 3 - Add the Scheduled Tasks](#step3)
    - [Step 4 - Migration to AA](#step4)
    - [Step 5 - Setting up Permissions](#step5)
    - [Step 6 - (Optional) Setting up Compatibilies](#step6)
  - [Highlights](#highlights)

## Features<a name="features"></a>

- Graphical Overview
- Ratting,Mining,Trading
- Character Ledger
- Corporation Ledger

## Upcoming<a name="upcoming"></a>

- Corp Tax System (Tracks specific amount that transfer'd to specific division)
- Events Calender

## Installation<a name="installation"></a>

> \[!NOTE\]
> AA Ledger needs at least Alliance Auth v4.0.0
> Please make sure to update your Alliance Auth before you install this APP

### Step 1 - Install the Package<a name="step1"></a>

Make sure you're in your virtual environment (venv) of your Alliance Auth then install the pakage.

```shell
pip install aa-ledger
```

### Step 2 - Configure Alliance Auth<a name="step2"></a>

Configure your Alliance Auth settings (`local.py`) as follows:

- Add `'allianceauth.corputils',` to `INSTALLED_APPS`
- Add `'eveuniverse',` to `INSTALLED_APPS`
- Add `'ledger',` to `INSTALLED_APPS`

### Step 3 - Add the Scheduled Tasks<a name="step3"></a>

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

### Step 4 - Migration to AA<a name="step4"></a>

```shell
python manage.py collectstatic
python manage.py migrate
```

### Step 5 - Setting up Permissions<a name="step5"></a>

With the Following IDs you can set up the permissions for the Ledger

| ID                        | Description                            |                                                                                         |
| :------------------------ | :------------------------------------- | :-------------------------------------------------------------------------------------- |
| `basic_access`            | Can access the Ledger module           | All Members with the Permission can access the Ledger.                                  |
| `moderator_access`        | Has access to moderation tools         | Not Implemented yet.                                                                    |
| `admin_access`            | Has access to all Administration tools | Not Implemented yet.                                                                    |
| `char_audit_admin_access` | Can Manage Character Audit Module      | Can Manage Character Audit Module, Like Add Memeberaudit Chars, View Character Journals |
| `corp_audit_admin_access` | Can Manage Corporation Audit Module    | Can Manage Corporation Audit Module, Like Add Corp, View Corporation Journals           |

### Step 6 - (Optional) Setting up Compatibilies<a name="step6"></a>

The Following Settings can be setting up in the `local.py`

- LEDGER_APP_NAME:          `"YOURNAME"`   - Set the name of the APP

- LEDGER_LOGGER_USE:        `True / False` - Set to use own Logger File

- LEDGER_MEMBERAUDIT_USE:   `True / False` - Set to use the Memberaudit Journal to Fetch Statistics

- LEDGER_CORPSTATS_TWO:     `True / False` - Set to use Corp Stats Two APP to Fetch Members that are not registred

If you set up LEDGER_LOGGER_USE to `True` you need to add the following code below:

```python
LOGGING_LEDGER = {
    "handlers": {
        "ledger_file": {
            "level": "INFO",
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
            "level": "INFO",
        },
    },
}
LOGGING["handlers"].update(LOGGING_LEDGER["handlers"])
LOGGING["loggers"].update(LOGGING_LEDGER["loggers"])
```

## Highlights<a name="highlights"></a>

![Screenshot 2024-05-14 121014](https://github.com/Geuthur/aa-ledger/assets/761682/d0604260-b672-4bf5-a16a-d1b90557744d)

![Screenshot 2024-05-14 121025](https://github.com/Geuthur/aa-ledger/assets/761682/f8f20e6a-d37d-4a50-a1aa-8615c0f8e88b)

![Screenshot 2024-05-14 120944](https://github.com/Geuthur/aa-ledger/assets/761682/2d695369-1331-4be9-8adf-9c6dabf80dda)

![Screenshot 2024-05-14 121001](https://github.com/Geuthur/aa-ledger/assets/761682/463b9921-150c-42c1-8c3e-eee0f5cfc2bb)

> \[!NOTE\]
> Contributing
> You want to improve the project?
> Just Make a [Pull Request](https://github.com/Geuthur/aa-ledger/pulls) with the Guidelines.
> We Using pre-commit
