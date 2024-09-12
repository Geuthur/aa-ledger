# Ledger module for AllianceAuth.<a name="aa-ledger"></a>

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Geuthur/aa-ledger/master.svg)](https://results.pre-commit.ci/latest/github/Geuthur/aa-ledger/master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://github.com/Geuthur/aa-ledger/actions/workflows/autotester.yml/badge.svg)](https://github.com/Geuthur/aa-ledger/actions/workflows/autotester.yml)
[![codecov](https://codecov.io/gh/Geuthur/aa-ledger/graph/badge.svg?token=5CWREOQKGZ)](https://codecov.io/gh/Geuthur/aa-ledger)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/W7W810Q5J4)

Character and Corporation statistics, including detailed information on ESS, Ratting, Trading, Mining, and other activities.

______________________________________________________________________

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

- Statistics
  - Graphical Statistics
  - Yearly, Monthly, Daily, Hourly
  - Current Day
- Character Ledger
  - Graphical Overview for each Character
    - Graphical Statistics
  - Ratting
  - Encounter Surveillance System Payouts
  - Mining
  - Trading
  - Costs
- Corporation Ledger
  - Graphical Overview for each Member
  - Ratting Tax
  - Encounter Surveillance System Tax
- Alliance Ledger
  - Graphical Overview for each Corporation
  - Ratting
  - Encounter Surveillance System Tax
- Planetary Ledger
  - Graphical Overview for each Planet
  - Notification if Extractor expire
  - Switchable Notification for each Planet
  - Products Overview (not include amount)
- Events Calender

## Upcoming<a name="upcoming"></a>

- Bug Fixing, Performance Optimation

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

> \[!IMPORTANT\]
> Character, Corporation, Alliance Ledger only show Data from User has access to
> `advanced_access` give User access to see own Corporations he is in

| ID                         | Description                                |                                                        |
| :------------------------- | :----------------------------------------- | :----------------------------------------------------- |
| `basic_access`             | Can access the Ledger module               | All Members with the Permission can access the Ledger. |
| `advanced_access`          | Can access Corporation and Alliance Ledger | Can see Corporation & Alliance Ledger.                 |
| `admin_access`             | Can access the Administration tools        | Can Add Corporations, Alliances.                       |
| `char_audit_manager`       | Has Access to all characters for own Corp  | Can see all Chars from Corps he is in.                 |
| `char_audit_admin_manager` | Has Access to all Characters               | Can see all Chars.                                     |
| `corp_audit_admin_manager` | Has Access to all Corporations             | Can see all Corps.                                     |

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

![Screenshot 2024-08-30 220656](https://github.com/user-attachments/assets/c6ca5564-fb5f-407b-bcd2-e8400ce40763)

![Screenshot 2024-09-03 232900](https://github.com/user-attachments/assets/32f7b77e-4a5f-4fa7-9082-1ad2760131d9)

> \[!NOTE\]
> Contributing
> You want to improve the project?
> Just Make a [Pull Request](https://github.com/Geuthur/aa-ledger/pulls) with the Guidelines.
> We Using pre-commit
