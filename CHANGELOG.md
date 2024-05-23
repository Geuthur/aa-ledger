# Changelog

## \[0.5.0a1\] - 2024-xx-xx

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

https://github.com/geuthur/aa-ledger/compare/v0.4.2...v0.5.0

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
