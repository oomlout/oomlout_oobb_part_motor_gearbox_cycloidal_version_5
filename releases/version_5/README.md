# Version 5 — sealed

Approved 28 October 2026. This preserves the eight-piece 20:1 gearbox with
3 mm lobe radius, 1.4 mm eccentricity, 6810 casing bearings, 5 mm cycloids,
and split output casing with full-length, three-unit OOBB tabs. Four M3x6
countersunk screws use the tabs' M3 holes; captive nuts use overhang=True.

version_5.zip contains source, tests, native true/3dpr documents, STEP/STL
exports, linked print layouts, fit samples, animation and successful native
build evidence. Referenced helper sources are included under dependencies/.
The evidence/ folder also exposes immutable JSON/text build records.

Original absolute paths remain in historical evidence and linked layouts.
Restore the original paths or rebase links when extracting elsewhere.
Do not regenerate sealed catalogue folders. Development continues in V6.

Verified: 16 targeted tests, 16 native part documents, two layouts, nine fit
samples and 143 sampled motion poses without detected collisions. Physical
printing/loading remains untested; this is not a continuous-motion proof.
The prior full test suite had nine unrelated failures, recorded in the
archived validation summary. Acceptance policy and earlier releases remain intact.

All archived files and live sealed catalogue files have SHA-256 hashes in release.json.
