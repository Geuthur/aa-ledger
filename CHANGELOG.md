# Changelog

## [0.9.0] - 2025-07-29

### Fixed

- Corporation Overview not show all corps from own Characters
- Planetary Switch Alarm path error
- Total Mining Amount only count 1 Character
- Update Status Stale Error
- Corporation Wallet Journal not Updating until ETag expire

### Added

- Update Information in Character View
- `corp_audit_manager` permission
- `character_mining_manager` added EveSolarSystem if not exist

### Changed

- Ref Type System

  - Create all in one Ref Type Manager

- Refactor Character Ledger

  - Character View Paths
    - Date Path instead of API
  - CharacterAudit
    - `character` changed to `eve_character`
  - Removed API

- Refactor Corporation Ledger

  - Alliance View Paths
    - Date Path instead of API
  - Removed API

- Refactor Alliance Ledger

  - Alliance View Paths
    - Date Path instead of API
  - Removed API

- ESI Overload Prevention

  - Decreased Update Interval
  - Task Schedule from crontab to every `1800` seconds (30 minutes)
  - `update_subset_characters` updated
    - max run limit increased from `200` to `500`
    - min run limit increased from `10` to `50`
  - `update_subset_corporations` updated
    - min run limit increased from `10` to `20`

- Billboard Overflow System limited from `10` to `25`

- Billboard Chord added Miscellaneous. Data

- Renamed `admin_access` to `manage_access`

- Optimized Corporation Administration CSS

- Optimized Single View CSS

- Optimized Table CSS

- Optimized Billboard Visual Optic

- Optimized Details Template System

### Removed

- `character.js`, `corporation.js`, `alliance.js`, `ledger-common.js`
- `Aggregator System`
- `ìnformation_helper`
- Character, Corporation, Alliance Ledger API Endpoint
- Details API Endpoint

## [0.8.5] - 2025-07-22

> [!NOTE]
> For Managing Stuff you need to add the new `manage_access` permission
> `corp_audit_manager` Permission will show own corporations in Administration instead of `manage_access` (old `admin_access`)

### Fixed

- Corporation Overview not show all corps from own Characters
- missing Migration hint [#129](https://github.com/Geuthur/aa-ledger/issues/129)

### Added

- `corp_audit_manager` permission

### Changed

- Renamed `admin_access` to `manage_access`
- Permissions & Section

## [0.8.4] - 2025-07-19

### Removed

- 0011 Migration (created now by `calc_update_needed`)

### Fixed

- New Sections not included to Updates
- Wallet Balance not updating correctly

### Added

- Force Update Option for Django Administration

# [0.8.3] - 2025-07-15

### Added

- Character ESS Calculation to Billboard

# [0.8.2] - 2025-07-14

### Added

- Estimated ESS Payout for Characters

### Changed

- Updated amCharts5 to v5.13.3
- Optimized templates

### Removed

- amChart5 local static files
- Character ESS Calculation
- Old ESS Stolen Calculation
- Event System
- Daily Calculation for Character (Will be added again later)

# [0.8.1] - 2025-07-11

## Added

- `django-esi` dependency

## Changed

- Use `django-esi` new User Agent Guidelines

## Removed

- Unused templatetags

# [0.8.0] - 2025-07-05

## Added

- Update Section System - Inspired by @\[[Eric Kalkoken](https://gitlab.com/ErikKalkoken/)\]
  - TokenError Handler
  - HTTPInternalServerError, HTTPGatewayTimeoutError Handler
  - Update Section retrieves information between Etag System (Not Updating if NotModified)
  - Disable Update on Token Error
  - Update Information
  - Update Issues Badge
- Admin Menu (superuser only)
- Subset Task for Corporations
- Delete Option in Administration
- Add Corporation Actions for Corporation Ledger to Administration
- Disable Characters with no Owner

## Fixed

- CSS Issue with Modals
- ETag System Error Catch (HTTPGatewayTimeout, NotModifiedError)

## Changed

- Task System
  - Use Django Manager for Updates
  - Refactor `update_character` Task
- Use one navigation menu for Ledger
- Use app_utils `LoggerAddTag` Logger System
- Make `README` logger settings optional
- Optimized Url Paths
- AA min. requirements from 4.6.0 to 4.8.0

## Removed

- Cache Busting by [@ppfeufer](https://github.com/ppfeufer)
- `calculate_ess_stolen`, `calculate_ess_stolen_amount` function
- `_storage_key`, `get_cache_stale`, `set_cache`, `delete_cache` function

## [0.7.6] - 2025-05-02

### Added

- dependbot
- Discord Notification System

### Changed

- Update Pre-Commit
- Fix Pre-Commit Issues

### Fixed

- Tox Issue

## [0.7.5] - 2025-04-16

### Added

- Costs to Corporation/Alliance Ledger

### Changed

- General
  - Refactor Ledger, Information System
  - Refactor JS
  - Optimized CSS
  - Moved Common Ledger Scripts to `ledger-common.js`
- Planetary Ledger
  - Moved Progressbar Process from Java to Python
  - Planetary Notification All from `Switch All` to `Turn On/Off All Notification`
  - Notification Switch now reload interactive instead of reloading page
  - Optimized Planetary Confirm Modal

### Fixed

- Planetary Notification Issue [#94](https://github.com/Geuthur/aa-ledger/issues/94)
- Planeteray Progress Bar Widght [#95](https://github.com/Geuthur/aa-ledger/issues/95)

### Removed

- Donut Chart
- Workflow Chart
- ESS Stolen Calculation makes the code too heavy and confusing

## [0.7.4.3] - 2025-03-31

### Fixed

- Fix Planetary Update Issue [#90](https://github.com/Geuthur/aa-ledger/issues/90)

### Changed

- Optimized Error Handler & Removed Disabling the Overview Button

## [0.7.4.2] - 2025-03-28

### Fixed

- Alliance Ledger has Multiple Objects error

### Changed

- Update ETag System

## [0.7.4.1] - 2025-03-26

### Fixed

- Planetary Ledger Permission Issue
- Corporation View No Data Error

## [0.7.4] - 2025-03-26

### Added

- Application Tests
- Task Subset for Character Updates
- Character Administration
- Corporation Administration
- Alliance Administration

### Changed

- AA min. requirements from 4.0.0 to 4.6.0
- Refactor Corpjournal Manager
- Refactor Template System
- Refactor Django Templates
- Refactor Tests
- Alliance Ledger show Corporations instead of Characters
- Renamed template to information
- Logger System
- ETAG System use log timing instead of own timing log
- cards css
- renamed `custom.css` to `ledger.css`

### Removed

- Unnecessary Code
- Multicorp view

## [0.7.3] - 2025-02-27

### Added

- `event_admin_access` permission for Events
- Code of Conduct
- Contributing
- Bug Report Template
- Suggestion Template

### Removed

- Info Logger in Billboard Helper

## [0.7.2] - 2025-02-26

### Added

- RefType
  - `contract_collateral_refund`
  - `contract_deposit_refund`
  - `contract_sales_tax`
  - `contract_brokers_fee`
- INCOME & COST Translation

### Changed

- Chart System
  - renamed INCOME & COST to (income) & (cost) and added to django translation system

### Fixed

- In some cases the Contracts shown wrong
- In some cases Donations not shown correctly and missing
- Events can be views without `supersuser` [#56](https://github.com/Geuthur/aa-ledger/issues/56)
- Charts not disposing if data is empty [#55](https://github.com/Geuthur/aa-ledger/issues/55)

## [0.7.1] - 2025-02-04

### Added

- Planetary Manager
- Planetary Facility Overview
- Corporation Ledger
  - Industry Taxes
- `daily_goal_reward` Ref-Type to Char Ledger
- `annotate_billboard` for Corporation Ledger
- Python 3.13 Support
- SRI integrity
- Cache Busting by [@ppfeufer](https://github.com/ppfeufer)
- AmChart5 JS
  - Corporation Ledger show now Activitys to each Corporation
  - Ratting Chart can now be zoom'd
  - Daily Chart

### Removed

- MemberAudit Support - `Char Link` is the new Linking System
- Billboard JS

### Changed

- Optimized API Endpoints
- Renamed CharLink Hook Names
- Moved Corp Project Ref Type to Milestone Reward cause it not seems to be Corp Projects
- Create Missing Character changed to Create Missing Entity
- JS Portrait Handler
- JS Optimation Ledger
- Renamed `annotate_ledger` to `generate_ledger`
- Refactor `generate_ledger` queryfilter
- Refactor `generate_template` queryfilter
- Refactor Character Helper
- Corporation Billboard now use `annotate_billboard` from Corp Journal
- Template Helper use Standardized `generate_ledger` Queryset
- Standardized Ledger Backend Process
- All Amounts are Decimal now
- Dependencies updated
  - AA 4.6.1
- Minimum Requirments
  - AA 4.6.0
- Use `django-sri` for sri hash
- Refactor Chart System
- API Endpoint addressing
- MiningMiningLedger - `DateField` to `DateTimeField`
- Refactor Planetary Interaction System
- Refactor Modal System

### Fixed

- A Case that a Character become Income if he accept a Contract with Corp
- Long loading times on Corporation Ledger & Character Ledger
- Billboard doesn't work in different languages
- Float Error instead of Decimal in Ledger
- Corp Tax Event Filter filtered all instead of ESS only
- Billboard member to member contracts transactions are calculated wrong
- Corp Ledger Unknown entities are not displayed
- No decimal Rounding in Ledger View
- Modal Loading Animation
- Modal Error Handler

## [0.6.6] - 2024-11-16

### Added

- Char Link integration

## [0.6.5] - 2024-10-18

### Added

- Corporation Projects Filter to Ledger
- Corporation Template Filter System
- Ref Type Worktree
- `corporate_reward_payout` Ref-Type to Char & Corp Ledger named `Incursion`
- `daily_goal_reward` Ref-Type to Corp Ledger
- `milestone_reward_payment` Ref-Type to Character Ledger

### Changed

- Added `jump_clone_installation_fee` Ref-Type to Travling Filter
- Added `contract_reward_refund` Ref-Type to Contract Trade Filter

### Fixed

- Market Escrow missing on Market Trade Filter
- Character not Displayed if only Costs are displaying on Corp Intern Trades
- Contracts from Member to Member not working correctly
- Character Information Sheet show empty Template when Main is not in Corporation on Single Corporation Lookup
- Characters not included in some cases in Corp Ledger
- Bounty double taxing
- Current Day show on different months

### Update

- Translation

## [0.6.4] - 2024-10-04

### Update

- Translation for Planetary Interaction
- Character Ratting Amount now calculate with tax
- Planetary JS

### Added

- Planetary Interaction Image on Single Lookup
- Planetary Interaction ressource levels

### Fixed

- Current Day amount show on Year Infomation Sheet
- Tooltip not shown on Single Lookup

## [0.6.3] - 2024-10-03

### Added

- More strings translatable
- BS5 Tooltip to Corp & Ally Ledger
- Generating Information Sheet and Billboard handled now by QuerySet Manager
- Global Filtering for easier modifying^
- Translations System

### Changed

- JS Ledger
- Use Bootstrap Class for color changes

### Remove

- Unnecessary JS Variable
- Memberaudit dependencies (Memberaudit Task Adaption still works)
- Corp UTils dependencies (optional Corp Stats Two dependencies)
- Filters from Core Manager now handled by QuerySet Manager

### Fixed

- BS5 Tooltip & Popover not disappear
- Wrong naming in Overviews
- CSS Design Settings

## [0.6.2] - 2024-09-04

### Changed

- Character Ledger
  - CSS Update
- Corporation Ledger
  - CSS Update
- Planetary Ledger
  - CSS Update
- Character Information
  - CSS Update

### Fixed

- Character Information
  - Current Day - ESS Amount
- Month Table Footer display data on year change if empty

## [0.6.1] - 2024-09-04

### Changed

- Character Ledger
  - Javascript Optimation
- Corporation Ledger
  - Javascript Optimation
- Planetary Ledger
  - Javascript Optimation
- Permission System
  - Added advanced_access
    - Access to Corporation Ledger & Alliance Ledger
- Ledger Guide
  - More Information how it works
- `basic_access` has no longer access to Corporation & Alliance Ledger

### Added

> [!NOTE]
> Only Show Corporations that added in Ledger System

- Alliance System
  - Alliance Overview
  - Alliance Ledger
  - Alliance Billboard
- `advanced_access` can access Corporation & Alliance Ledger
  - Gives permission to see Corporations they are in

### Moved

- Overview Link to each Ledger

### Removed

- All Overview Links from Menu
- Add Char / Corporation on Ledger View
- `char_audit_manager` Permission now handled by `advanced_access`

### Fixed

- Permission Denied if no Data exists
- Loading Animation url wrong app name
- Table show on Loading Animation

## [0.6.0.1] - 2024-09-04 - Hotfix

### Fixed

- Character Information:
  - On Administration Overview Overall Information not work for Character

## [0.6.0] - 2024-09-04

### Added

- Planetary Interaction System

  - Planetary Admin Overview
    - List only show Mains with all their Alts Planets
  - Planets API
  - Planets Details API
  - Planets Overview
  - Alarm System for Expired Heads
    - Alarm Notification for each Planet
    - Switchable Notification
  - Graphical Details
    - Progress Bar
    - Item Type
    - Planets
    - Status
  - Progression Display
  - Extractor Information Modal

- Character Audit Model

  - last_update_planetary field

- app settings LEDGER_UPDATE_INTERVAL

### Moved

- get_token function to core_helpers

### Changed

- Character Audit
  - Added Planetary ESI Scope
- Tasks
  - Added Planetary Update Task to Character Update Task
- Character Overview
  - List now only show Mains and combine calculation with optional single lookup

### Fixed

- Unknown Character not working on Corporation Ledger
- Included Characters not shown on Corporation Ledger

### Removed

- Add Member Audit Chars Button (Handled by Task)

## [0.5.9] - 2024-08-29

> [!WARNING]
> Member Audit support has been dropped, Please Read README

### Fixed

- Billboard Wallet Donut Calculation

### Added

- Corporation Manager
- Character Manager
- Billboard API
- Character Journal Manager
- Corporation Journal Manager

### Changed

- Moved Billboard System from Ledger to own function
- Reduced loading times significant from Database Querys, Calculation
- log_timing decorator
- Core Manager

### Removed

- Ledger Manager
- Member Audit integration

## [0.5.8] - 2024-08-22

### Fixed

- Character/Corporation Ledger: Tick Amount not showing correct

### Added

- Character/Corporation Ledger: Current Day Tick
- Character/Corporation Ledger: Current Day Summary

### Changed

- Menu System
- Character Update Time from 2 hours to 1
- Character/Corporation Ledger: Daily, Hourly Summary renamed to Avg. Summary

## [0.5.7.1] - 2024-08-13

### Fixed

- Character Information: Insurance Current Day Calculation
- Character Ledger: ESS Stolen

## [0.5.7] - 2024-08-13

### Added

- Corporation Ledger: Portrait mouseover now displays included alts
- Character/Corporation Ledger: Stolen ESS (Amount that stolen from you)
- Information Template: Yellow Coloring for Info amounts only
- Day HTML template for Current Day Statistics

### Changed

- PyPi Description
- Corporation Ledger: Changed Naming 'Ratting' to 'TAX'
- Update README
- Update Ledger FAQ
- Optimized Character Information Template
- Optimized Corporation Information Template
- Information Template: Formatting
- Information Template: Moved Current Day to Top in Daily Tab
- Calculate ESS Stolen function

## [0.5.6] - 2024-08-07

### Added

- RefType:

  - researching_time_productivity,
  - researching_material_productivity,
  - copying,
  - contract_reward_deposited,
  - contract_collateral,
  - structure_gate_jump
  - asset_safety_recovery_tax
  - planetary_import_tax
  - planetary_export_tax
  - planetary_construction
  - insurance
  - skill_purchase
  - reaction
  - reprocessing_tax
  - jump_clone_activation_fee

- New Statistics to Information Template

  - Contract Cost
  - Asset Safety Cost
  - Traveling Cost
  - Skillbook Purchase Cost
  - Insurance Cost
  - Planetary Cost
  - Insurance

- Single Costs for each Character now displaying in Character Ledger

### Fixed

- Character Information: Current Day was Static and not updated on next day.

### Changed

- Optimized Information Template
- Refactor Template,Ledger Manager

## [0.5.5] - 2024-08-02

### Fixed

- Billboard: On Single Lookup Bounty calculated as in char ledger

### Removed

- 3.8, 3.9 Python Support

## [0.5.4] - 2024-07-23

### Added

- Billboard: Dark Theme & Flatly Theme
- Billboard: Tick Value [#26](https://github.com/Geuthur/aa-ledger/issues/26)
- Billboard: Hourly Statistics [#26](https://github.com/Geuthur/aa-ledger/issues/26)
- Billboard: RattingBar Size Handler
- add_info_to_context: Theme Check cause NIGHT_MODE won't work with AA v4
- Create Missing Char Task for alts and mains function
- Character Ledger: Create Graphical Overview for Single Lookup
- Character Ledger: Look Up button for each Character

### Changed

- Refactor Billboard Manager
- Billboard: Bar Overlapping disabled
- Billboard: Char Ledger Charts Legend disabled

### Fixed

- Character/Corp Ledger: Button Sorting
- Both Admin Overview: Sorting wrong Col
- Character/Corp Ledger: CSS Issues with Table
- Billboard: Padding Issue on Year Tab
- add_info_to_context didn't work on each temnplate
- Character Ledger: Wrong Donations Calculation on Single Lookup (Not Exclude Alts)
- etag_handler: Fix NotModified Error (Testing)
- Corporation Overview: No Data Error on DoesNotExist error
- Add Char Button shown if memberaudit is active
- Char/Corp Ledger Footer Amount changes wrong if sorting.
- Billboard: Calculation Issue
- Character Information: Summary not show red if negative

## [0.5.3] - 2024-07-13

### Added

- Added Mission Rewards to Calculation [#26](https://github.com/Geuthur/aa-ledger/issues/26) - Point 5 Suggestion Added
- Average Hourly Tick calculated with [#26](https://github.com/Geuthur/aa-ledger/issues/26) - Point 4 Suggestion Added
  - Example: 100000 ISK - July 16
  - 100000 / 16 / 24 / 3
  - This month you make avg 87 ISK per Tick
- Current Day Tick [#26](https://github.com/Geuthur/aa-ledger/issues/26) - Point 4 Suggestion Added
  - Example: 100000 ISK - July 16
  - 100000 / 3
  - You make 33333 ISK per Tick this Day
- Error Handler for Template Modal
- Loading Animation on Data Load
- Admin Overview for Corporation & Character Ledger [#26](https://github.com/Geuthur/aa-ledger/issues/26) - Point 3 Suggestion Added with Point 1 included except Daily Graph
- Create EveCharacter if Corp Member not exist

### Changed

- Permissions more information in README
- Character Ledger & Corporation Ledger Path
- Refactor Char, Corp JS
- Optimized get_all_mains_alts function
- Optimized Billboard Calculation (Performance)
- Optimized Template Calculation (Performance) on Corporation side
- Add Memberaudit Chars to CharacterAudit permission changed from

### Fixed

- In some cases the Billboard has Lazy Rendering
- Error on Template if no data found
- Wrong Calculations on Character Ledger 30 Days (ESS Payout)
- Characters not visible in Character Ledger
- Error from DataTable if No Data found (403 Error)

### Removed

- Caching after Performance Optimation not needed anymore

### Known Issues

- To fast Tab changing calls error on console

## [0.5.2a2] - 2024-06-19

### Added

- Costs to Character Ledger Table
- Many Tests
- Year Selection on Ledger
- Ledger Caching

### Fixed

- Market Cost not shown if Transaction is empty on Detailed. Information
- Market Escrow RefType wasn't shown on Detailed Information
- Billboard Limiter Sorted before enumerate
- Curent Day Row shown on different months,years.
- Date not shown correctly on Month Change
- Date Range Calculation on Billboard Manager

### Changed

- Corp & Character Ledger Template Update
- Corp, Char Ledger JS to Bootstrap Dropdown
- Caching Function

## [0.5.1] - 2024-06-14

### Added

- Create Tests
- Added Events System to Ledger
- New Permission `audit_manager` have access to own Corporation, Character Information (API)

### Removed

- Removed Corp Tax (Will be Released later)
- Removed Moderator Permission
- Removed Ledger from Auth Hook Naming now it only show the APP NAME

### Fixed

- Character Jorunal not working correctly

### Changed

- API Adressing from journal api and ledger api
- Corporation and Character Ledger access update

## [0.5.0] - 2024-06-01

### Added

- Create Function for ESS Payout Calculation on CharacterLedger
- Create Core Manager to Handling Ledger Stuff
- Create FilterClass for all Filters and removed old ones
- Create Tests for different Szenarios more come later

### Fixed

- Summary on Character Ledger not include Mining Amount
- Donations on Memberside not added to Detailed Information
- Value Error on Billboard
- Mining Amount not display on Detailed Information

### Changed

- Moved Billboard Manager to own py

https://github.com/geuthur/aa-ledger/compare/v0.4.2...v0.5.0

## [0.5.0b1] - 2024-05-27

### Fixed

- Summary on Character Ledger not include Mining Amount
- Donations on Memberside not added to Detailed Information

## Full Changelog

https://github.com/geuthur/aa-ledger/compare/v0.5.0a1...v0.5.0b1

## [0.5.0a1] - 2024-05-25

### Added

- Create Function for ESS Payout Calculation on CharacterLedger
- Create Core Manager to Handling Ledger Stuff
- Create FilterClass for all Filters and removed old ones

### Fixed

- Mining Amount not display on Detailed Information

### Changed

- Moved Billboard Manager to own py

### Removed

- reset_values function in LedgerTotal class

## Full Changelog

https://github.com/geuthur/aa-ledger/compare/v0.4.2...v0.5.0a1

## [0.4.2] - 2024-05-23

### Fixed

- Memberaudit Table Join was wrong

## Full Changelog

https://github.com/geuthur/aa-ledger/compare/v0.4.1...v0.4.2

## [0.4.1] - 2024-05-23

### Fixed

- Current Day Display on Year Tab
- Detailed Informationen show Empty Fields
- LEDGER_MEMBER_AUDIT Error if not set in local.py
- ESS Payout not calcluate Tax on Character Ledger
- Wallet Charts not shown correctly
- Create Test View for Settings

## Full Changelog

https://github.com/geuthur/aa-ledger/compare/v0.4.0...v0.4.1

## [0.4.0] - 2024-05-22

### Added

- Import Error Checker on Memberaudit use
- Translation Addon for Month Selection (Maybe more Translation later?)
- Own ModelClass for LedgerProcess

### Changed

- Templatetags format values now use AA tags

### Fixed

- ESS Payout not shown on Character Ledger Billboard
- Missed Corp Tax Setting on Readme
- Add Char Button displayed when `LEDGER_MEMBERAUDIT_USE = True`
- Path for ledger/ledger

### Performance Fix

- Changed Data fetch function reduce loading time more then 1-2 sec on larger Data Fetch

### Removed

- Order By in Querys

## [0.3.8] - 2024-05-22

### Fixed Critical

- TemplateTag Missing

## [0.3.0-0.3.7] - 2024-05-20

### Added

- Initial public release

### Fixed

- Corporation Ledger JS not working correctly on Years Tab
- Fixed Permissions aren't create on migrate
