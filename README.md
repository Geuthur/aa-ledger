# Ledger module for AllianceAuth.<a name="aa-ledger"></a>

![Release](https://img.shields.io/pypi/v/aa-ledger?label=release)
![Licence](https://img.shields.io/github/license/geuthur/aa-ledger)
![Python](https://img.shields.io/pypi/pyversions/aa-ledger)
![Django](https://img.shields.io/pypi/frameworkversions/django/aa-ledger.svg?label=django)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Geuthur/aa-ledger/master.svg)](https://results.pre-commit.ci/latest/github/Geuthur/aa-ledger/master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checks](https://github.com/Geuthur/aa-ledger/actions/workflows/autotester.yml/badge.svg)](https://github.com/Geuthur/aa-ledger/actions/workflows/autotester.yml)
[![codecov](https://codecov.io/gh/Geuthur/aa-ledger/graph/badge.svg?token=5CWREOQKGZ)](https://codecov.io/gh/Geuthur/aa-ledger)
[![Translation status](https://weblate.geuthur.de/widget/allianceauth/aa-ledger/svg-badge.svg)](https://weblate.geuthur.de/engage/allianceauth/)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/W7W810Q5J4)

Character and Corporation PvE statistics, including detailed information on ESS, Ratting, Trading, Mining, and other activities.

______________________________________________________________________

- [AA Ledger](#aa-ledger)
  - [Features](#features)
  - [Upcoming](#upcoming)
  - [Installation](#features)
    - [Step 0 - Check dependencies are installed](#step0)
    - [Step 1 - Install the Package](#step1)
    - [Step 2 - Configure Alliance Auth](#step2)
    - [Step 3 - Add the Scheduled Tasks and Settings](#step3)
    - [Step 4 - Migration to AA](#step4)
    - [Step 5 - Setting up Permissions](#step5)
    - [Step 6 - (Optional) Settings](#step6)
  - [Highlights](#highlights)
  - [Translations](#translations)
  - [Contributing](#contributing)

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
    - Graphical Statistics
  - Ratting Tax
  - Encounter Surveillance System Tax
  - Industry Tax
- Alliance Ledger
  - Graphical Overview for each Corporation
  - Ratting Tax
  - Encounter Surveillance System Tax
- Planetary Ledger
  - Graphical Overview for each Planet
    - Graphical Statistics
  - Notification if Extractor expire
  - Switchable Notification for each Planet
  - Products Overview
- Events Calender

## Upcoming<a name="upcoming"></a>

- Corporation Administration
- Status Update System for each Section
- Costs for Corporation Ledger

## Installation<a name="installation"></a>

> [!NOTE]
> AA Ledger needs at least Alliance Auth v4.6.0
> Please make sure to update your Alliance Auth before you install this APP

### Step 0 - Check dependencies are installed<a name="step0"></a>

- Ledger needs the app [django-eveuniverse](https://apps.allianceauth.org/apps/detail/django-eveuniverse) to function. Please make sure it is installed.

### Step 1 - Install the Package<a name="step1"></a>

Make sure you're in your virtual environment (venv) of your Alliance Auth then install the pakage.

```shell
pip install aa-ledger
```

### Step 2 - Configure Alliance Auth<a name="step2"></a>

Configure your Alliance Auth settings (`local.py`) as follows:

- Add `'ledger',` to `INSTALLED_APPS`

### Step 3 - Add the Scheduled Tasks<a name="step3"></a>

To set up the Scheduled Tasks add following code to your `local.py`

```python
CELERYBEAT_SCHEDULE["ledger_character_audit_update_subset_characters"] = {
    "task": "ledger.tasks.update_subset_characters",
    "schedule": 1800,
}
CELERYBEAT_SCHEDULE["ledger_corporation_audit_update_subset_corporations"] = {
    "task": "ledger.tasks.update_subset_corporations",
    "schedule": 1800,
}
CELERYBEAT_SCHEDULE["ledger_check_planetary_alarms"] = {
    "task": "ledger.tasks.check_planetary_alarms",
    "schedule": 10800,
}
```

### Step 3.1 - (Optional) Add own Logger File

To set up the Logger add following code to your `local.py`
Ensure that you have writing permission in logs folder.

```python
LOGGING["handlers"]["ledger_file"] = {
    "level": "INFO",
    "class": "logging.handlers.RotatingFileHandler",
    "filename": os.path.join(BASE_DIR, "log/ledger.log"),
    "formatter": "verbose",
    "maxBytes": 1024 * 1024 * 5,
    "backupCount": 5,
}
LOGGING["loggers"]["extensions.ledger"] = {
    "handlers": ["ledger_file"],
    "level": "DEBUG",
}
```

### Step 4 - Migration to AA<a name="step4"></a>

```shell
python manage.py collectstatic
python manage.py migrate
```

### Step 5 - Setting up Permissions<a name="step5"></a>

With the Following IDs you can set up the permissions for the Ledger

> [!IMPORTANT]
> Character, Corporation, Alliance Ledger only show Data from User has access to
> `advanced_access` give User access to see own Corporations he is in

| ID                         | Description                                |                                                        |
| :------------------------- | :----------------------------------------- | :----------------------------------------------------- |
| `basic_access`             | Can access the Ledger module               | All Members with the Permission can access the Ledger. |
| `advanced_access`          | Can access Corporation and Alliance Ledger | Can see Corporation & Alliance Ledger.                 |
| `manage_access`            | Can Manage Ledger                          | Can add/manage Corporations, Alliances.                |
| `char_audit_manager`       | Has Access to all characters for own Corp  | Can see all Characters from Corps he is                |
| `char_audit_admin_manager` | Has Access to all Characters               | Can see all Characters.                                |
| `corp_audit_manager`       | Has Access to own Corporations             | Can see own Corporations.                              |
| `corp_audit_admin_manager` | Has Access to all Corporations             | Can see all Corporations.                              |

### Step 6 - (Optional) Settings<a name="step6"></a>

The Following Settings can be setting up in the `local.py`

- LEDGER_APP_NAME: `"YOURNAME"` - Set the name of the APP
- LEDGER_TASKS_TIME_LIMIT: `7200` - Defines the time (in seconds) a task will timeout
- LEDGER_USE_COMPRESSED: `True` - Defines if Mining Ledger use Compressed Price or Raw
- LEDGER_PRICE_PERCENTAGE: `0.9`- Defines Mining Price multiplier

Advanced Settings: Stale Status for Each Section

- LEDGER_STALE_TYPES = `{     "wallet_journal": 30,     "wallet_division": 30,     "mining_ledger": 30,     "planets": 30,     "planets_details": 30, }` - Defines the stale status duration (in minutes) for each section.

## Highlights<a name="highlights"></a>

![Ledger](https://raw.githubusercontent.com/geuthur/aa-ledger/master/ledger/docs/images/preview1.png "Ledger")
![Single Character Ledger](https://raw.githubusercontent.com/geuthur/aa-ledger/master/ledger/docs/images/preview2.png "Single Character Ledger")
![Details Modal](https://raw.githubusercontent.com/geuthur/aa-ledger/master/ledger/docs/images/preview3.png "Details Modal")
![Planetary Ledger](https://raw.githubusercontent.com/geuthur/aa-ledger/master/ledger/docs/images/preview4.png "Planetary Ledger")
![Factory Modal](https://raw.githubusercontent.com/geuthur/aa-ledger/master/ledger/docs/images/preview5.png "Factory Modal")
![Extractor Modal](https://raw.githubusercontent.com/geuthur/aa-ledger/master/ledger/docs/images/preview6.png "Extractor Modal")

## Translations<a name="translations"></a>

[![Translations](https://weblate.geuthur.de/widget/allianceauth/aa-ledger/multi-auto.svg)](https://weblate.geuthur.de/engage/allianceauth/)

Help us translate this app into your language or improve existing translations. Join our team!"

## Contributing <a name="contributing"></a>

You want to improve the project?
Please ensure you read the [contribution guidelines](https://github.com/Geuthur/aa-ledger/blob/master/CONTRIBUTING.md)
