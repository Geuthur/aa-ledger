# Changelog

### Added

- Average Hourly Tick calculated with
  - Example: 100000 ISK - July 16
  - 100000 / 16 / 24 / 3
  - This month you make avg 87 ISK per Tick
- Current Day Tick
  - Example: 100000 ISK - July 16
  - 100000 / 3
  - You make 33333 ISK per Tick this Day
- Error Handler for Template Modal
- Loading Animation on Data Load
- Admin Overview for Corporation & Character Ledger
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
