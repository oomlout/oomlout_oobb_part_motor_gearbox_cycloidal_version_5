# Cycloidal V5 explorer

Open **cycloidal-explorer.html** directly in a browser. It is a single offline file:
CSS, JavaScript, SVG geometry, and the five-page example PDF are embedded.
There is no server, installation, or internet requirement. The NSK source link
is optional and opens an external bearing reference.

- Adjust ratio, contact/lobe radius, eccentricity, clearance, wall, disc thickness and gap.
- Set both body radius and centre-to-centre position radius for the three standoffs
  and six static guide screws. The moving orbit-hole sizes update automatically.
- Choose the reference bearing from 6700–6711 or 6800–6812; it defaults to 6810.
  It appears below the diagrams and optionally as a ghost underneath each cycloid.
  This is a scale reference; it does not alter the retained 6810 casing interfaces.
- Choose top and bottom cycloid centre bearings independently (default 6703),
  or select None. Both cycloids are shown in separate plan views.
- Pink highlights show the intersecting regions of holes, bearing seats and
  interfering hardware at the displayed input angle. Animate to inspect motion.
  Thin webs and axial bearing retention are checked separately below the drawing.
- Turn automatic pitch sizing off to set the pitch radius yourself.
- Automatic sizing follows the reduction and all current radial settings. Set
  **Extra radius buffer** to add millimetres above the calculated minimum; the
  same buffer remains in place when you change the reduction. Presets reset it
  to zero. The summary shows minimum + applied buffer = selected pitch radius,
  plus the limiting feature. This is a radius allowance (diameter grows by twice it).
- The minimum is the first 0.05 mm pitch step satisfying the existing V5 lower
  radius rules: 0.90 profile coefficient, 2 mm feature webs, contact spacing and
  analytic undercut. Automatic radius is this minimum plus buffer, rounded up
  to 0.05 mm. Fixed internal clashes cannot be cured just by increasing radius;
  too much buffer can also violate the retained 6810 lip's upper size limit.
  The buffer is disabled and not applied in manual-radius mode.
- Animate the casing-output mechanism, or move the input-angle slider.
- **Check full motion** samples both cycloids every 1° over a complete input turn,
  with progress and cancellation. Identical contacts permute after each input
  revolution, so this covers the repeated geometry throughout a casing turn.
  The result reports the smallest signed gap, the feature pair, disc and input
  angle. **Jump to worst position** displays that sample. Geometry edits clear
  the old result; phase changes and the amber threshold do not.
- Motion screening includes contact/disc clearance, fixed hardware in its orbit
  holes, bearing/hardware clearance, hardware pairs, casing/hardware gaps, hole
  webs and hole breakouts. The reference bearing and separate axial planes stay
  excluded. Negative gaps indicate overlap. This is sampled 2D screening, not a
  proof of continuous or 3D clearance; profile chord tolerance is 0.0005 mm.
- **Amber below (mm)** sets the small-gap threshold (default 0.10 mm). Dashed
  amber outlines identify affected features at the displayed angle; pink keeps
  marking overlap. These outlines are included in exported SVGs.
- **Saved designs & comparison** stores up to 50 named snapshots, including
  completed motion results. Compare casing diameter, disc thickness, component
  stack, bearings, ratio, sampled minimum gap and screening status. Each save
  adds a snapshot; Load restores it. Edit its name then click Rename (or Enter).
  Remove deletes a snapshot from the library.
- The library uses browser storage for this file/location, with a session-only
  fallback if storage is blocked. **Export library** saves portable JSON;
  **Import library** validates and appends designs without replacing existing
  ones. Moving the HTML or using another browser does not transfer storage.
  Stored results are labelled as stored until rerun. Export a backup to retain
  the library independently of browser storage.
- Save a dimensioned SVG with both cycloids and pink highlights, or save/copy the parameters.
- Use **Print / save PDF** for the current design via the browser print dialog.
- Use **Download example book** for the embedded examples, also available separately
  as `dist/cycloidal-examples.pdf`.

The example PDF contains current V5, 12:1, 30:1 and smaller-contact 20:1 studies,
followed by the project's undercut lesson. Its diagrams are 1:1 on A4 when printed
at **100% / Actual size**. Check the 50 mm calibration bar. The browser's current-
design print layout is fit to page and is not a 1:1 manufacturing template.

The current 20:1 design has **20 casing contacts and 19 disc lobes**. This is a
rotating-casing architecture, with the output turning in the input direction.
The default 6810 reference is **50 mm bore × 65 mm OD × 7 mm wide**, shown at the
same scale beneath the mechanism. Actual end bearings occupy a different axial plane.
The reference and the separate cycloid planes are not compared against one another
for collisions. Hole intersections indicate lost separating material; hardware
intersections indicate interference. This is a 2D check, not a full 3D fit analysis.

Nominal catalogue dimensions are sourced from ENRO (6700–6706), Yongnuo
(6700-series table), NSK's Bearing and Linear Replacement Guide (B-15, 6800 series),
and JTEKT's open 6700 specification. Links are in the page. 6700 is offered as
both 10 × 15 × 4 and the distinct JTEKT open 10 × 15 × 3 variant; match the part
you have. All catalogue data is bundled into the standalone HTML.

The profile and adaptive sampling match `gearbox_native/cycloid_equation.py` and
`gearbox_native/lobe.py` to 0.0005 mm chord tolerance. Radial rules come from the
current V5 recipe and interfaces. Automatic sizing also checks analytic undercut;
this supplements the project's envelope-based pitch selection. Eleven screening
checks are shown; passing does not establish complete assembly fit or load capacity.
Changing parameters does not change the project's existing CAD or recipe files.
Exported parameters are an explicit-radius study; run the native project's full
validation before using them for manufacture.
The native recipe uses one shared eccentric-bearing choice and locks M3 guides.
Independent centre bearings, absent bearings or changed screw sizes require CAD
recipe changes; the JSON export includes these limitations and all explorer values.

The current V5 baseline is Ø72.3 mm and 32 mm tall above the motor face. Height
is not extrapolated to modified designs. The calculated bearing/disc stack is
only two 7 mm bearings, two discs and their gap, excluding other axial features.

## Rebuild

From this directory, with Node, Python, ReportLab, pypdf and Shapely available:

```powershell
node export_data.js
node test_controls.js
node test_radius_buffer.js
node test_studies.js
python test_geometry.py
python make_pdf.py
python build_standalone.py
python verify_artifacts.py
```

`dist/index.html`, `dist/style.css`, `dist/geometry.js`, `dist/studies.js`, `dist/diagram.js` and `dist/app.js` are the
editable source. Rebuild the standalone file after changing them. The standalone
build removes the source page's optional web-font import for offline use.

Verification: all four examples match the native adaptive profiles, form valid
polygons, retain 2 mm hole webs, and maintain 0.20 mm contact clearance within
0.0005 mm sampling tolerance through sampled motion of both opposed discs.
The historic R=30.15, e=1.4, r=3 undercut case is rejected. PDF pages were rendered
and visually checked. Presets, animation and undercut rejection were exercised
in a browser using the single-file build over an isolated local HTTP preview.
Additional tests cover both radius controls, independent centre bearings, all
reference-bearing choices, width-dependent retention, circle intersection,
seat and orbit-hole breakout, and exclusion of separate axial planes.
The example book remains the original four V5 studies; print the current design
from the page to capture new bearing and support choices.
