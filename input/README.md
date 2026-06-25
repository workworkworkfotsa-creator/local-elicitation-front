# input/ — local data only (not committed)

This folder holds the **real example files** used to exercise the front against a concrete case
(Tier B tests: file reading, cross-reference + bare-coefficient detection).

**Nothing here is committed** except this README — see `.gitignore`. Business/company data must
never enter this public repository. Drop your own reconciliation workbook here locally (any
`.xlsx`) to run the file-reader milestones; the code keeps column **names** and synthesises
values (no PII leaves the machine).
