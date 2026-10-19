# Source Passports: research feed

Research files for the Source Passports register kept by MPMONITOR (Media and Journalism Research Center).

- `feed.json` lists the files the register imports automatically (once each, by checksum). The register's setting "Research feed address" points at the raw URL of this file.
- `batches/` holds the research CSV files, one per batch. Rows match passports by name and country; every fact carries a source and comes in as *Pending check* until an MJRC researcher verifies it.
- `FORMAT.md` describes the columns and the accuracy rules.

Data licence: CC BY-SA 4.0. Register: https://mpmonitor.org/passports/

- `mirror/passports-latest.json.gz` is a daily copy of the register's public open-data snapshot (gzip-compressed JSON; open it with any unzip tool or `gunzip`), kept here by a GitHub Action as the continuity safeguard (a complete copy outside the web server).
