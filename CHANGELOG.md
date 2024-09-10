# Changelog

## \[0.6.1\] - 2024-09-04

### Changed

- Character Ledger
  - Javascript Optimation
- Corporation Ledger
  - Javascript Optimation
- Planetary Ledger
  - Javascript Optimation

### Added

- Alliance System
  - Alliance Overview
  - Alliance Ledger
  - Alliance Billboard

### Moved

- Overview Link to each Ledger

### Removed

- All Overview Links from Menu
- Add Char / Corporation on Ledger View

### Fixed

- Permission Denied if no Data exists
- Loading Animation url wrong app name
- Table show on Loading Animation

## \[0.6.0.1\] - 2024-09-04 - Hotfix

### Fixed

- Character Information:
  - On Administration Overview Overall Information not work for Character

## \[0.6.0\] - 2024-09-04

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

## \[0.5.9\] - 2024-08-29

> \[!WARNING\]
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

## \[0.5.8\] - 2024-08-22

### Fixed

- Character/Corporation Ledger: Tick Amount not showing correct

### Added

- Character/Corporation Ledger: Current Day Tick
- Character/Corporation Ledger: Current Day Summary

### Changed

- Menu System
- Character Update Time from 2 hours to 1
- Character/Corporation Ledger: Daily, Hourly Summary renamed to Avg. Summary

## \[0.5.7.1\] - 2024-08-13

### Fixed

- Character Information: Insurance Current Day Calculation
- Character Ledger: ESS Stolen

## \[0.5.7\] - 2024-08-13

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

## \[0.5.6\] - 2024-08-07

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

## \[0.5.5\] - 2024-08-02

### Fixed

- Billboard: On Single Lookup Bounty calculated as in char ledger

### Removed

- 3.8, 3.9 Python Support

## \[0.5.4\] - 2024-07-23

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

## \[0.5.3\] - 2024-07-13

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

## \[0.5.2a2\] - 2024-06-19

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

## \[0.5.1\] - 2024-06-14

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

## \[0.5.0\] - 2024-06-01

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

## \[0.5.0b1\] - 2024-05-27

### Fixed

- Summary on Character Ledger not include Mining Amount
- Donations on Memberside not added to Detailed Information

## Full Changelog

https://github.com/geuthur/aa-ledger/compare/v0.5.0a1...v0.5.0b1

## \[0.5.0a1\] - 2024-05-25

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

## \[0.4.2\] - 2024-05-23

### Fixed

- Memberaudit Table Join was wrong

## Full Changelog

https://github.com/geuthur/aa-ledger/compare/v0.4.1...v0.4.2

## \[0.4.1\] - 2024-05-23

### Fixed

- Current Day Display on Year Tab
- Detailed Informationen show Empty Fields
- LEDGER_MEMBER_AUDIT Error if not set in local.py
- ESS Payout not calcluate Tax on Character Ledger
- Wallet Charts not shown correctly
- Create Test View for Settings

## Full Changelog

https://github.com/geuthur/aa-ledger/compare/v0.4.0...v0.4.1

## \[0.4.0\] - 2024-05-22

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

## \[0.3.8\] - 2024-05-22

### Fixed Critical

- TemplateTag Missing

## \[0.3.0-0.3.7\] - 2024-05-20

### Added

- Initial public release

### Fixed

- Corporation Ledger JS not working correctly on Years Tab
- Fixed Permissions aren't create on migrate
