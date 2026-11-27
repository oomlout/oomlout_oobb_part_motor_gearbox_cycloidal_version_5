"""Render the working_scad animation snapshot with a fixed camera and true timing."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def view_settings(c):
    explode = c.get("animation_explode", 20)
    height = c["gap"] + 2 * c["thickness_outer_rotor"] + 20.5 * explode + 20
    size = c.get("animation_size", [960, 1600])
    return {
        "explode": explode,
        "target": [
            0,
            0,
            (c["motor_face_z"] + c["housing_depth"] - c["motor_body_depth"]) / 2,
        ],
        "rotation": c.get("animation_camera_rotation", [65, 0, 25]),
        "distance": c.get(
            "animation_camera_distance",
            max(height * 4.8 * size[0] / size[1], c["pitch_radius"] * 9),
        ),
    }


def render_animation(folder, **kwargs):
    folder = Path(folder).resolve()
    if (folder / "SEALED.json").exists():
        raise ValueError(f"Sealed release cannot be rendered in place: {folder}")
    openscad = shutil.which("openscad.com") or shutil.which("openscad")
    ffmpeg = shutil.which("ffmpeg")
    if not openscad or not ffmpeg:
        raise RuntimeError("Animation rendering requires OpenSCAD and ffmpeg on PATH")
    frames = kwargs.get("animation_frames", 192)
    fps = kwargs.get("animation_fps", 12)
    workers = kwargs.get("animation_workers", 3)
    size = kwargs.get("animation_size", [960, 1600])
    if not isinstance(frames, int) or frames < 2 or fps <= 0 or workers < 1:
        raise ValueError("Animation needs >=2 integer frames, positive FPS and workers")
    if len(size) != 2 or any(not isinstance(x, int) or x < 2 or x % 2 for x in size):
        raise ValueError(
            "animation_size must contain two positive even pixel dimensions"
        )
    view = view_settings(kwargs)
    camera = [*view["target"], *view["rotation"], view["distance"]]
    report_path = folder / "animation_render.json"
    report_path.write_text(json.dumps({"status": "running"}) + "\n")

    def run(args):
        result = subprocess.run(args, capture_output=True, text=True)
        log = result.stdout + result.stderr
        if result.returncode or "WARNING:" in log or "ERROR:" in log:
            raise RuntimeError(log)

    try:
        with tempfile.TemporaryDirectory(prefix="gearbox-animation-") as temporary:
            temporary = Path(temporary)

            def frame(i):
                run(
                    [
                        openscad,
                        "--backend=Manifold",
                        "--render",
                        "--projection=ortho",
                        "--imgsize=" + ",".join(map(str, size)),
                        "--camera=" + ",".join(map(str, camera)),
                        "-D",
                        f"input_turns={kwargs['reduction'] * i / frames:.12f}",
                        "-o",
                        str(temporary / f"frame_{i:04d}.png"),
                        str(folder / "animation.scad"),
                    ]
                )
                return (
                    i,
                    hashlib.sha256(
                        (temporary / f"frame_{i:04d}.png").read_bytes()
                    ).hexdigest(),
                )

            frame_hashes = set()
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for i, digest in pool.map(frame, range(frames)):
                    frame_hashes.add(digest)
                    if (i + 1) % 24 == 0 or i == frames - 1:
                        print(f"Animation rendered {i + 1}/{frames} frames", flush=True)
            if len(frame_hashes) < 2:
                raise RuntimeError(
                    "Animation frames are identical; check the input motion controls"
                )
            video = temporary / "animation.mp4"
            gif = temporary / "animation.gif"
            run(
                [
                    ffmpeg,
                    "-y",
                    "-loglevel",
                    "error",
                    "-framerate",
                    str(fps),
                    "-i",
                    str(temporary / "frame_%04d.png"),
                    "-c:v",
                    "libx264",
                    "-crf",
                    "20",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    str(video),
                ]
            )
            run(
                [
                    ffmpeg,
                    "-y",
                    "-loglevel",
                    "error",
                    "-framerate",
                    str(fps),
                    "-i",
                    str(temporary / "frame_%04d.png"),
                    "-filter_complex",
                    "split[a][b];[a]palettegen[p];[b][p]paletteuse=dither=sierra2_4a",
                    "-loop",
                    "0",
                    str(gif),
                ]
            )
            for output in (video, gif):
                shutil.copy2(output, folder / output.name)
            shutil.copy2(temporary / "frame_0000.png", folder / "animation.png")
        report = {
            "status": "passed",
            "frames": frames,
            "fps": fps,
            "duration_seconds": frames / fps,
            "input_turns": kwargs["reduction"],
            "output_turns": 1,
            "unique_frames": len(frame_hashes),
            "camera": view,
            "size": size,
            "scad_sha256": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(folder.glob("*.scad"))
            },
        }
        report_path.write_text(json.dumps(report, indent=2) + "\n")
    except Exception as error:
        report_path.write_text(
            json.dumps({"status": "failed", "error": str(error)}) + "\n"
        )
        raise
