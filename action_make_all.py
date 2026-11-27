"""Build every populated gearbox from its native SolidCraft master."""
from action_export_native import main as export_native


def main(**kwargs):
    args = ["--populate"]
    if kwargs.get("style"):
        args.extend(["--style", kwargs["style"]])
    code = export_native(args)
    if code:
        raise SystemExit(code)


if __name__ == "__main__":
    main()
