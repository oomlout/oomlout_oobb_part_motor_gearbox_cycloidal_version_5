# Native OOBB nut patterns

`cut(design, pitch=..., count=..., z=..., phase=..., rotation=...)` expands the
shared OOBB `oobb_nut` with `overhang=True`, then replays each exact polygon/roof
prism as an expression-driven circular sketch pattern. `count`, pitch, phase and
placement remain native expressions. Native parameter edits require no Python.

The optional `selector` is a caller-guarded 0/1 M3/M6 catalogue choice. Counts
must be valid native pattern counts. General subtraction and arbitrary catalogue
rotations are rejected rather than silently approximated. This component adds
no new hardware dimensions: the original catalogue supplies all five prisms.

The gearbox V8 proof changes six M3 nuts to four M6 nuts, checks native health,
and saves the resulting native document. Gearbox isolated proofs additionally
exercise changing guide counts and deleting standoffs via native parameters.
