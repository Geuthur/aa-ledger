# Ledger module for AllianceAuth.<a name="aa-ledger"></a>

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Geuthur/aa-ledger/master.svg)](https://results.pre-commit.ci/latest/github/Geuthur/aa-ledger/master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://github.com/Geuthur/aa-ledger/actions/workflows/autotester.yml/badge.svg)](https://github.com/Geuthur/aa-ledger/actions/workflows/autotester.yml)
[![codecov](https://codecov.io/gh/Geuthur/aa-ledger/graph/badge.svg?token=5CWREOQKGZ)](https://codecov.io/gh/Geuthur/aa-ledger)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/W7W810Q5J4)

Character/Corporation Ledger see Statistics for Ratting, Mining, ESS Payout

## -

- [AA Ledger](#aa-ledger)
  - [Features](#features)
  - [Upcoming](#upcoming)
  - [Installation](#features)
    - [Step 1 - Install the Package](#step1)
    - [Step 2 - Configure Alliance Auth](#step2)
    - [Step 3 - Add the Scheduled Tasks and Settings](#step3)
    - [Step 4 - Migration to AA](#step4)
    - [Step 5 - Setting up Permissions](#step5)
    - [Step 6 - (Optional) Setting up Compatibilies](#step6)
  - [Highlights](#highlights)

## Features<a name="features"></a>

- Graphical Overview
- Ratting, Mining, Trading, Costs, etc.
- Character Ledger
- Corporation Ledger
- Planetary Ledger with Notification System
- Events Calender

## Upcoming<a name="upcoming"></a>

- Alliance Overview

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
    "schedule": crontab(minute=0, hour="*/1"),
}
CELERYBEAT_SCHEDULE["ledger_corporation_audit_update_all"] = {
    "task": "ledger.tasks.update_all_corps",
    "schedule": crontab(minute=0, hour="*/1"),
}
CELERYBEAT_SCHEDULE["ledger_check_planetary_alarms"] = {
    "task": "ledger.tasks.check_planetary_alarms",
    "schedule": crontab(minute=0, hour="*/3"),
}
```

> \[!NOTE\]
> If you have Member Audit installed add this to Fetch Member Audit Chars and Sync with Ledger

```python
CELERYBEAT_SCHEDULE["ledger_character_member_audit_fetch"] = {
    "task": "ledger.tasks.create_member_audit",
    "schedule": crontab(minute=0, hour="*/1"),
}
```

### Step 4 - Migration to AA<a name="step4"></a>

```shell
python manage.py collectstatic
python manage.py migrate
```

### Step 5 - Setting up Permissions<a name="step5"></a>

With the Following IDs you can set up the permissions for the Ledger

| ID                         | Description                               |                                                        |
| :------------------------- | :---------------------------------------- | :----------------------------------------------------- |
| `basic_access`             | Can access the Ledger module              | All Members with the Permission can access the Ledger. |
| `admin_access`             | Can access the Administration tools       | Can Add Memberaudit Chars & Add Corporations.          |
| `char_audit_manager`       | Has Access to all characters for own Corp | Can see all Chars from Corps he is in.                 |
| `corp_audit_manager`       | Has Access to own Corporation             | Can see all Corps he is in.                            |
| `char_audit_admin_manager` | Has Access to all Characters              | Can see all Chars.                                     |
| `corp_audit_admin_manager` | Has Access to all Corporations            | Can see all Corps.                                     |

### Step 6 - (Optional) Setting up Compatibilies<a name="step6"></a>

The Following Settings can be setting up in the `local.py`

- LEDGER_APP_NAME:          `"YOURNAME"`     - Set the name of the APP

- LEDGER_CORP_TAX:          `15`             - Set Tax Value for ESS Payout Calculation

- LEDGER_LOGGER_USE:        `True / False`   - Set to use own Logger File

- LEDGER_CORPSTATS_TWO:     `True / False`   - Set to use Corp Stats Two Application for fetching member data

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
