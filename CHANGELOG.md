# Changelog

## \[0.4.1\] - 2024-05-23

### Fixed

- LEDGER_MEMBER_AUDIT Error if not set in local.py
- ESS Payout not calcluate Tax on Character Ledger
- Wallet Charts not shown correctly
- Create Test View for Settings

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
