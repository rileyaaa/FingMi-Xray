"""Shared immutable pins for the reconstructed Libass build chain.

The extractor pin is the deterministic output of build-libass-extractor.py after
all current player overlays have been applied. The candidate pin is the final
Libass compatibility AAR consumed by current/publish workflows.
"""

LIBASS_EXTRACTOR_AAR_SHA256 = "f4667540c598416895cae5c4201fbe1c0e30c88d2673395a23db91b1b107278b"
LIBASS_CANDIDATE_AAR_SHA256 = "f047f8ad84be08aeddb0672500e9b263cafd6f2a009812392554dc55b2019861"
