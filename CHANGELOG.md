# Changelog

All notable changes to this project will be documented in this file.

The format loosely follows Keep a Changelog.
This project does not promise semantic versioning, but breaking changes are noted clearly.

---

## v1.0.1 – Stable Release

### Added
- Full automation for adding `.torrent` files to qBittorrent
- Automatic detection of **Movies vs TV Shows**
- Strict Jellyfin/Plex-compatible folder structures
- Support for:
  - Movies
  - TV Shows
  - Anime (treated as TV)
- Forced folder creation for single-file torrents
- Subtitle renaming with language and variant support:
  - Languages: `en`, `hi`, `ja`, `fr`, `es`
  - Variants: `forced`, `sdh`, `cc`
- Category-aware downloads:
  - Uses Movies / TV categories if present
  - Falls back to configured paths if not
- Per-torrent download and upload speed limits
- Safe re-runs using processed torrent hash tracking
- Failure logging with automatic cleanup

### Fixed
- Race condition when detecting newly added torrents
- Incorrect TV detection for `1x01` patterns
- Silent corruption when movie year was missing
- Regex issues and redundant escapes
- Potential crashes from uninitialized torrent references

### Behavior Guarantees
- Folder → File → Subtitles order is always enforced
- Only the main video file and subtitles are downloaded
- All other torrent contents are ignored
- Resulting structure works reliably with:
  - Jellyfin
  - Plex
  - Emby

### Notes
- This release is considered stable.
- Future changes should prioritize correctness over flexibility.
