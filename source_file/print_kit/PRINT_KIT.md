# Printing the gearbox

Open [the editable P1S project]({kit}) as a project in Bambu Studio. Print each plate once for one complete square-flange gearbox. All {count} pieces are individually selectable under **Prepare → Objects**. Each plate uses one PLA colour. Confirm the physical spool assigned to each slot before printing.

| Plate | Contents | Filament slot | Pieces |
| --- | --- | ---: | ---: |
{table}

Use the P1S 0.4 mm nozzle and textured PEI plate from the OOBB starter. The filament presets are Black 10101, Turquoise 10605 and Sunflower Yellow 10402. The fourth starter slot is unused. The kit uses loose contact sleeves. The alternative meshes (`{excluded}`) are available in [native_parts](native_parts/) for substitutions. See the [gearbox assembly notes](README.md) for hardware and installation order.

## Rebuilding this kit

Run `python working_3mf.py --part "parts/{part_id}"` from the project root after publishing the native STLs. The native publisher runs this stage automatically. The writer uses Python, NumPy, trimesh and Pillow. To slice-check all plates, add `--slice-to PATH` with a new scratch directory. Review the Bambu result and plate G-code there.

## Adapting the print layout

1. Copy [the plate recipe](../../source_file/print_kit/{recipe}) beside it under a new recipe name. Set the filename, plate names and one-based filament slots. Use the assembly BOM and print-oriented native body stems. Declare optional alternatives explicitly under `exclude`.
2. Give each group a centre `start` in local bed millimetres. Use `parts` for distinct bodies, or `series` and `count` for numbered copies. Set `step` for the spacing and optionally `columns` for a grid. Keep each plate single-colour.
3. Run `python working_3mf.py --part "parts/NEW_PART_ID" --recipe "source_file/print_kit/NEW_RECIPE.json" --slice-to "NEW_SCRATCH_DIR"`. In its native publisher call `working_3mf.publish(part, recipe_path)` after individual meshes are available.
4. Check the slice for every plate. On a disposable copy in Bambu Studio, change one repeated object's filament, save, reopen and slice. Check its neighbours retain their assignments. Distribute the original editable project.

The [generator](../../working_3mf.py) uses the vendored OOBB editable-copy helper and SHA-checked [P1S template](../../source_file/print_kit/default.3mf). It checks the full BOM, watertight volumes, 3 mm plate clearances, cutter exclusion, independent object IDs, dimensions and filament assignments after reopening the package.
