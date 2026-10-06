# Ledger module for AllianceAuth.<a name="ledger-module-for-allianceauth"></a>

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

<!-- mdformat-toc start --slug=github --maxlevel=6 --minlevel=1 -->

- [Ledger module for AllianceAuth.](#ledger-module-for-allianceauth)
  - [Features](#features)
  - [Highlights](#highlights)
  - [Installation](#installation)
    - [Step 1 - Install the Package](#step-1---install-the-package)
    - [Step 2 - Configure Alliance Auth](#step-2---configure-alliance-auth)
    - [Step 3 - Add the Scheduled Tasks](#step-3---add-the-scheduled-tasks)
    - [Step 3.1 - (Optional) Add own Logger File](#step-31---optional-add-own-logger-file)
    - [Step 4 - Migrate & Preload EVE SDE Data](#step-4---migrate--preload-eve-sde-data)
    - [Step 4.1 - Migrate App and collect static](#step-41---migrate-app-and-collect-static)
    - [Step 5 - Setting up Permissions](#step-5---setting-up-permissions)
    - [Step 6 - (Optional) Settings](#step-6---optional-settings)
  - [Translations](#translations)
  - [Contributing](#contributing)

<!-- mdformat-toc end -->

## Features<a name="features"></a>

- Statistics
  - Graphical Statistics
  - Yearly, Monthly, Daily, Hourly
  - Current Day
  - Shareable links: year, month, day, division and opened details are part of the URL
- Administration
  - Registered and missing characters, corporations and alliances
  - Per user setting to disable all notifications
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
- Status Update System for each Section
- Costs for Corporation Ledger

## Highlights<a name="highlights"></a>

![Image: character]
![Image: corporation]
![Image: corporation-details]
![Image: planetary]
![Image: planetary-details]

## Installation<a name="installation"></a>

> [!NOTE]
> AA Ledger needs at least Alliance Auth v5
> Please make sure to update your Alliance Auth before you install this APP

### Step 1 - Install the Package<a name="step-1---install-the-package"></a>

Make sure you're in your virtual environment (venv) of your Alliance Auth then install the pakage.

```shell
pip install aa-ledger
```

### Step 2 - Configure Alliance Auth<a name="step-2---configure-alliance-auth"></a>

Configure your Alliance Auth settings (`local.py`) as follows:

```python
INSTALLED_APPS = [
    # other apps
    "eve_sde",  # only if it not already existing
    "ledger",
    # other apps?
]

# This line is right below the `INSTALLED_APPS` list, if not already exist!
INSTALLED_APPS = ["modeltranslation"] + INSTALLED_APPS
```

### Step 3 - Add the Scheduled Tasks<a name="step-3---add-the-scheduled-tasks"></a>

To set up the Scheduled Tasks add following code to your `local.py`

```python
if "ledger" in INSTALLED_APPS:
    CELERYBEAT_SCHEDULE["AA Ledger :: Update Subset Characters"] = {
        "task": "ledger.tasks.update_subset_characters",
        "schedule": 1800,
    }
    CELERYBEAT_SCHEDULE["AA Ledger :: Update Subset Corporations"] = {
        "task": "ledger.tasks.update_subset_corporations",
        "schedule": 1800,
    }
    CELERYBEAT_SCHEDULE["AA Ledger :: Check Planetary Notification"] = {
        "task": "ledger.tasks.check_planetary_alarms",
        "schedule": 10800,
    }
```

This also only need to be added if it is not already!

```python
if "eve_sde" in INSTALLED_APPS:
    # Run at 12:00 UTC each day
    CELERYBEAT_SCHEDULE["EVE SDE :: Check for SDE Updates"] = {
        "task": "eve_sde.tasks.check_for_sde_updates",
        "schedule": crontab(minute="0", hour="12"),
    }
```

### Step 3.1 - (Optional) Add own Logger File<a name="step-31---optional-add-own-logger-file"></a>

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

### Step 4 - Migrate & Preload EVE SDE Data<a name="step-4---migrate--preload-eve-sde-data"></a>

AA Ledger uses EVE SDE data to map IDs to names for EveTypes. You will need to preload some data from SDE once.

```shell
python manage.py migrate eve_sde
python manage.py esde_load_sde
```

### Step 4.1 - Migrate App and collect static<a name="step-41---migrate-app-and-collect-static"></a>

Migrate the app and collect static.

```shell
python manage.py migrate ledger
python manage.py collectstatic --noinput
```

### Step 5 - Setting up Permissions<a name="step-5---setting-up-permissions"></a>

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

### Step 6 - (Optional) Settings<a name="step-6---optional-settings"></a>

The Following Settings can be setting up in the `local.py`

- LEDGER_APP_NAME: `"YOURNAME"` - Set the name of the APP
- LEDGER_TASKS_TIME_LIMIT: `7200` - Defines the time (in seconds) a task will timeout
- LEDGER_USE_COMPRESSED: `True` - Defines if Mining Ledger use Compressed Price or Raw
- LEDGER_PRICE_PERCENTAGE: `0.9`- Defines Mining Price multiplier
- LEDGER_BULK_BATCH_SIZE: `500` - Maximum database batch size per operation. Reduce (e.g., 250) if encountering 'max_allowed_packet' errors, increase for better performance if MySQL is configured with higher limits

Advanced Settings: Stale Status for Each Section

- LEDGER_STALE_TYPES = `{     "wallet_journal": 30,     "wallet_division": 30,     "mining_ledger": 30,     "planets": 30,     "planets_details": 30, }` - Defines the stale status duration (in minutes) for each section.

## Translations<a name="translations"></a>

[![Translations](https://weblate.geuthur.de/widget/allianceauth/aa-ledger/multi-auto.svg)](https://weblate.geuthur.de/engage/allianceauth/)

Help us translate this app into your language or improve existing translations. Join our team!"

## Contributing<a name="contributing"></a>

You want to improve the project?
Please ensure you read the [contribution guidelines](https://github.com/Geuthur/aa-ledger/blob/master/CONTRIBUTING.md)

[image: character]: https://raw.githubusercontent.com/geuthur/aa-ledger/master/docs/images/character.png "Character Dashboard"
[image: corporation]: https://raw.githubusercontent.com/geuthur/aa-ledger/master/docs/images/corporation.png "Corporation Dashboard"
[image: corporation-details]: https://raw.githubusercontent.com/geuthur/aa-ledger/master/docs/images/corporation-details.png "Corporation Details"
[image: planetary]: https://raw.githubusercontent.com/geuthur/aa-ledger/master/docs/images/planetary.png "Planetary Dashboard"
[image: planetary-details]: https://raw.githubusercontent.com/geuthur/aa-ledger/master/docs/images/planetary-details.png "Planetary Details"
