"""Populate the catalogue, build SCAD, and render the exploded motion preview."""

import working


def main(**kwargs):
    kwargs.setdefault("render_animation", True)
    working.run(
        run_oomp_populate=True,
        run_oomp=True,
        run_scad=True,
        generate_stl=False,
        **kwargs,
    )


if __name__ == "__main__":
    main()
