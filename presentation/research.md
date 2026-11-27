# Documentation sources and decisions

AI-generated images and instructions. Errors possible.

Reviewed 7 November 2026. The updated local OOBB base instructions are in `C:/gh/oomlout_oobb_version_5/AGENTS.md`, `RENDER_STYLE.md`, and `presentation/{README,STYLE,DATA}.md`. The shared README, thumbnail, manual and validation helpers were adopted from that repository.

| Primary example | Observation | Applied decision |
| --- | --- | --- |
| [Voron Trident README](https://github.com/VoronDesign/Voron-Trident/blob/main/README.md) | Leads with the machine and useful downloads, with a route to its BOM. | Lead with the complete mechanism; keep printable downloads close to the operating description. |
| [Prusa MINI X-axis and extruder assembly](https://help.prusa3d.com/guide/3-x-axis-extruder-assembly_199519) | Breaks assembly into part preparation and specific numbered actions. | Prepare the bearing clamshells first; identify nuts before closing their pockets; show each stacking stage separately. |
| [GitHub README documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) | Supports branch-aware relative links and an automatic heading outline. | Use relative image/download paths and four plain headings, with genuine linked thumbnail files. |

These are documentation references, not evidence that this gearbox has been built. No reference artwork was copied.

## Hardware identity

Six public OOMP `working.yaml` entries were read through the GitHub connector, after discovery in the local OOMP and screw catalogues. The exact IDs, inspected fields, source URLs, catalogue alpha codes and redirect responses are retained in [catalogue-evidence.json](catalogue-evidence.json). Canonical directory URLs and those verified codes are included in the manifest and generated hardware table.

The selected socket-cap records specify M3, 30/35 mm lengths and socket-cap hex drives. The countersunk record specifies M3 x 6 and a hex drive. The nut record is an ordinary M3 hex nut; the two bearing records explicitly identify 50 x 65 x 7 and 20 x 27 x 4 mm envelopes. These identities match the production CAD requirements. No grub screw, button head, low head or OOBB bearing holder was substituted.

The standard model provides nominal head and bearing envelopes rather than supplier-specific production detail. The script checks the seats and axes represented by the saved CAD and existing assembly evidence. Identity verification does not certify a supplier's tolerances.

## Assembly interpretation

The retained production assembly guide specifies building upward from the native `upper` end. That makes Disc B the first disc, heads down, and Disc A second, heads up. Twenty ring screws and six guide screws keep their direction. One of the two shaft screws temporarily uses a hex pocket, is withdrawn underneath after the stack is captured, and is reinserted from the finishing face. This order overrides the old downward-build illustration.

The eight core nuts at each end and four N attachment nuts at each end are all installed in the illustrated configuration. This makes the hardware table complete for one defined gearbox while leaving external drive, frame and load attachment lengths to the actual application. A functional interface view represents use without inventing an external motor or mounting kit.

## Fixed outer ring operation

The user specifies fixing the teal outer ring and using the black middle ring as the output. The hero labels, installation step, manual and hand-rotation instructions follow that arrangement. The earlier fixed-carrier wording is superseded.

The production source `gearbox_native/native_v8.py` patterns each rotor outline `ring_count - 1` times: twenty contacts therefore produce nineteen lobes. [Sumitomo's explanation of fixed-ring cycloidal operation](https://www.cyclo100.com/cyclo-technology) relates the reduction to the disc lobe count and describes output rotation opposite to input. Applying that principle to this geometry gives output/input = -1/19, or a nominal 19:1 reduction. This is a kinematic inference from the CAD counts, not a measured running result.

The saved native parameter `reduction=20`, catalogue filenames and native `output_angle=input_angle/ring_count` describe the existing twenty-contact preset and former fixed-carrier reference. They remain unchanged by this documentation revision. To express the new arrangement in that reference, subtract its ring angle from all group angles: input relative to the fixed ring is 19/20 of the former input, and the carrier rotates by -1/20, giving -1/19 overall.
