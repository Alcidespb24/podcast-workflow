---
phase: 02-audio-processing-and-distribution
plan: 02
subsystem: audio
tags: [pydub, ffmpeg, mutagen, easyid3, crossfade, rms-normalization, mp3, id3]

# Dependency graph
requires:
  - phase: 02-audio-processing-and-distribution
    plan: 01
    provides: "Episode model, Settings with crossfade_ms/target_dbfs, EncodingError exception, pydub/mutagen installed"
provides:
  - "rms_normalize() for RMS-based volume normalization"
  - "process_audio() for PCM-to-AudioSegment crossfade pipeline"
  - "export_tagged_mp3() for CBR 128kbps mono MP3 with ID3 tags"
  - "imageio-ffmpeg fallback when system ffmpeg not on PATH"
affects: [02-03, 02-04, 03-automation]

# Tech tracking
tech-stack:
  added: [imageio-ffmpeg]
  patterns: [pydub AudioSegment from raw PCM, crossfade clamping, mutagen EasyID3 tagging]

key-files:
  created:
    - tests/test_audio_processing.py
  modified:
    - src/infrastructure/audio.py

key-decisions:
  - "imageio-ffmpeg used as fallback when system ffmpeg not on PATH -- avoids requiring users to install ffmpeg separately"
  - "Crossfade clamped to min(crossfade_ms, len(seg1), len(seg2)) to prevent ValueError on short segments"
  - "Silent/zero-RMS segments returned unchanged without normalization to avoid division-by-zero in dBFS"

patterns-established:
  - "RMS normalization via gain = target_dbfs - seg.dBFS (not peak-based)"
  - "ID3 tagging via mutagen EasyID3 with ID3NoHeaderError fallback"
  - "ffmpeg auto-configuration at module import time"

requirements-completed: [AUDIO-01, AUDIO-02, AUDIO-03, AUDIO-04]

# Metrics
duration: 3min
completed: 2026-03-08
---

# Phase 2 Plan 2: Audio Processing Pipeline Summary

**pydub-based crossfade and RMS normalization pipeline with CBR 128kbps mono MP3 export and mutagen ID3 tagging**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-08T06:14:43Z
- **Completed:** 2026-03-08T06:17:43Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 2

## Accomplishments
- rms_normalize() adjusts audio segments to configurable target dBFS, safely handling silent/zero-RMS input
- process_audio() converts raw PCM byte chunks to a single crossfaded, RMS-normalized AudioSegment
- export_tagged_mp3() produces CBR 128kbps mono MP3 files with ID3 title/artist/tracknumber tags
- Crossfade clamping prevents ValueError when segments are shorter than requested crossfade duration
- imageio-ffmpeg fallback ensures MP3 export works without system-level ffmpeg installation
- 10 new tests, 118 total tests passing (excluding pre-existing google-genai import issue)

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for audio processing** - `2f8592c` (test)
2. **Task 1 GREEN: Audio processing pipeline implementation** - `51cadc2` (feat)

## Files Created/Modified
- `src/infrastructure/audio.py` - Complete audio processing module with rms_normalize, process_audio, export_tagged_mp3, and legacy write_wav
- `tests/test_audio_processing.py` - 10 tests covering normalization, crossfade, MP3 export, ID3 tags, error handling, backward compatibility

## Decisions Made
- imageio-ffmpeg used as fallback when system ffmpeg not on PATH -- bundles a static ffmpeg binary via pip, no system install needed
- Crossfade clamped to min(crossfade_ms, len(seg1), len(seg2)) -- prevents ValueError on short segments without requiring caller to check lengths
- Silent/zero-RMS segments returned unchanged -- avoids division-by-zero in dBFS calculation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] imageio-ffmpeg fallback for missing system ffmpeg**
- **Found during:** Task 1 (GREEN phase, pre-implementation check)
- **Issue:** ffmpeg not on system PATH; pydub MP3 export would fail silently or error
- **Fix:** Added _configure_ffmpeg() at module load that sets AudioSegment.converter to imageio-ffmpeg binary when system ffmpeg is missing; updated test skip marker to detect both sources
- **Files modified:** src/infrastructure/audio.py, tests/test_audio_processing.py
- **Verification:** All 10 tests pass including MP3 export, ID3 tagging, mono/bitrate verification
- **Committed in:** 51cadc2 (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Auto-fix necessary for ffmpeg availability. No scope creep -- imageio-ffmpeg was already an installed dependency.

## Issues Encountered
- pydub and mutagen packages were not installed in the active Python environment despite being in pyproject.toml -- installed via pip before proceeding (pre-existing environment issue, not plan-related)

## User Setup Required
None - imageio-ffmpeg bundles ffmpeg binary. No external service configuration required.

## Next Phase Readiness
- Audio processing pipeline ready for RSS feed generation (02-03) and distribution (02-04)
- process_audio() accepts PCM chunks from TTS pipeline and produces broadcast-ready AudioSegment
- export_tagged_mp3() creates tagged MP3 files suitable for podcast distribution
- write_wav() still available for backward compatibility with earlier pipeline stages

## Self-Check: PASSED

All 2 key files verified present. All 2 task commits (2f8592c, 51cadc2) verified in git log.

---
*Phase: 02-audio-processing-and-distribution*
*Completed: 2026-03-08*
