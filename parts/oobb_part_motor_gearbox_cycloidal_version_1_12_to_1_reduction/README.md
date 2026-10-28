# 12:1 cycloidal gearbox

Generated through working_oomp_populate -> working_oomp -> working_scad.
Edit source inputs/builders and regenerate. SCAD files here are portable snapshots.

- `3dpr.scad`: all printable pieces, z=0, with required quantities.
- Named SCAD/STL files: each individual printable piece (print housing_spacer four times).
- `assembly.scad`: assembled view.
- `animation.scad`: exploded working assembly with covers, carriers, bearings, retainers, joining screws, nuts and shaft washers; View > Animate, FPS 12, Steps 192. Set `explode=0` for the assembled pose.
- `animation.gif` / `animation.mp4`: rendered by `python action_make_animation.py` in the project root; 12 input revolutions give one reverse output revolution.
- `exploded.scad`: assembly order; `section.scad`: section through the bearings.
- `fit_check.scad`: intersections only; a successful clearance check is empty.
- `gearbox.json`: resolved dimensions, quantities, layout, hardware lengths.

Hardware dimensions and fastening notes are in the project README. No bearing,
metal rod or fastener is included in the print plate. Physical printer fits and
loaded performance still need a prototype; the digital checks do not establish them.
