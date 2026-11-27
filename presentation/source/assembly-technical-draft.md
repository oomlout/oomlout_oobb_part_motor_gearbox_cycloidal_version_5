# Layered assembly with the screws standing upward

Start with the **socket-cap end facing down** and build upward over the screw shanks. This is the opposite direction to the previous guide. The parts named `upper` in SolidCraft are the starting end on the bench; the parts named `lower` become the finishing end above it.

[Layers 1–6](assembly_lower.png) · [Layers 7–12](assembly_upper.png) · [Full illustrated sequence](render_installation.png) · [Named parts](render_exploded.png)

The small yellow E journal for the centred 6704 and the larger black inner carrier for the 6810 go in the **same first layer**, alongside the outside cylinder. Both bearings follow in the next layer. The plate, inner carrier core and N then form the next concentric layer.

Continuous insertion checks cover the parts lowered over the standing screws, the temporary shaft screw, its withdrawal and reversed reinsertion, and the connected-ring option. These checks use nominal CAD geometry. Support the loose layers by hand and check the printed fits as you go.

## Before stacking

Assemble both cycloids on the bench. Capture a 6704 between each disc's screw half and nut half. Load three M3 nuts and fit three M3 × 6 countersunk screws per disc, seating the heads flush. Their straight hex-key paths are blocked once the casing bearings are fitted.

For this upside-down build, **B goes on first with its screw heads down**, and **A goes on second with its screw heads up**. Both discs' indexed clamp screws must face the same wide guide gap. Keep the two C halves of each cam aligned, with the second cam's eccentric offset 180° opposite the first.

Set aside eight M3 mounting nuts for each carrier core and up to four attachment nuts for each N. These load into their split faces before those faces close.

## 1. First layer — three concentric pieces and 28 standing screws

Prepare these three pieces together, outside flanges toward the bench and narrow journals pointing upward.

| Starting piece | CAD name | Screws standing upward |
|---|---|---|
| Outside cylinder | `output_cap_cylinder` | Twenty M3 × 30 socket caps |
| Large 6810 inner carrier cap | `carrier_top_cap` | Six M3 × 35 guide socket caps |
| Small centred 6704 inner journal E | `shaft_end_upper` | Two M3 × 35 shaft socket caps |

Insert the screws through the pieces from underneath before setting them concentrically. Their heads remain at the starting face and their shanks point upward. The two bearing journals help locate the following layers.

Put one shaft screw in E's **round socket recess**. Put the other in E's **empty hex nut pocket** as a temporary guide. Its round head fits that pocket in the checked model. Leave this hex pocket free of its nut for now.

Leave the temporary screw loosely seated. The screw in the round recess stays in this direction. The screw in the hex pocket is the one you will withdraw and reverse at the end.

## 2. Bearing layer — both bearings together

Lower the 6810 over the large black journal and into the outside cylinder. Lower the centred 6704 over the small yellow E journal and into the centre of the carrier cap. Both bearings approach from above, over the standing screws.

Seat each bearing against its intended shoulder. The three outside end faces have different recess depths; let the bearing seats locate the pieces.

## 3. Closing layer — plate, carrier core and N

Load eight mounting nuts into the starting carrier core's split face. Load the optional four attachment nuts into the starting N. Their pocket openings face downward toward the cap and E, so retain the nuts while lowering the pieces.

Lower the flat OOBB plate, carrier core and N over their respective screw circles. These are one concentric layer. The core closes the bearing races against the carrier cap, and N closes the centred bearing's inner race against E.

Once this layer is seated, support the OOBB plate on blocks with **at least 50 mm of access underneath the starting face**. You will need that space to reach the screw heads and pull one complete shaft screw out later.

## 4. Sleeve layer — lower all spacers over the screws

Slide six inner guide sleeves onto the six M3 × 35 screws and seat them in the carrier sockets. Slide twenty outer contact sleeves onto the twenty M3 × 30 screws.

You can use the connected outer contact ring at this same stage. It lowers over the twenty standing screws as one piece. The six inner sleeves are still required.

The following discs fit axially inside this contact arrangement at the checked reference position. Keep the plate and sleeve pattern aligned while lowering them.

## 5. First cam and first cycloid — B

Slide B's first C half onto the two shaft screws, narrow journal pointing up. This is `shaft_cam_b_outer`.

Lower the complete Disc B over the two shaft screws, the open eccentric journal and the six guide sleeves, inside the outer contacts. Its screw heads face down toward the starting end.

Point B's indexed clamp screw toward the wide gap between the guides. The bearing seats on the first C shoulder. Keep the second C half off until the bearing has reached that seat.

## 6. Centre layer — close B and start A

Lower `shaft_cam_b_inner` over the two shaft screws with its narrow journal pointing down into B's bearing.

Then lower `shaft_cam_a_inner`, narrow journal up, with its eccentric offset opposite B's. These two touching C shoulders form the centre layer. Both screw axes stay aligned through the stack.

## 7. Second cycloid — A — and its closing C

Lower Disc A onto the open A journal, over the standing screws and six guide sleeves. Its screw heads face up.

Keep A's indexed clamp screw facing the same wide guide gap as B's. Fit `shaft_cam_a_outer` last, narrow journal down into the seated bearing. Both C pairs now capture their bearings.

## 8. Finishing inner layer — plate, carrier core and N

Load the eight finishing-core mounting nuts and the optional four finishing-N attachment nuts. Here the pocket openings face upward, toward the finishing cap and E.

Lower the finishing flat OOBB plate over the twenty outer screws, the finishing carrier core over the six guides, and finishing N over the two shaft screws. The sleeves seat in the core's shallow sockets. These three parts form another concentric layer.

Use `output_nut_plate`, `carrier_bottom` and `shaft_mount_lower` at this end. Either OOBB plate outline uses the same bearing and screw interface.

## 9. Finishing bearing layer

Lower the second 6810 onto the flat plate and the large inner carrier shoulder. Lower the second centred 6704 onto N and the carrier's central retaining face.

Both bearings go on from above while the screw shanks continue to guide the stack. Keep them seated squarely before adding the caps.

## 10. Finishing cap layer — three pieces together

Lower the finishing outside cylinder, large 6810 inner carrier cap and small E journal onto their bearings and screw axes as one concentric layer. Their outside flanges face upward and their narrow journals point down.

Use `output_nut_cylinder`, `carrier_bottom_cap` and `shaft_end_lower`. The guide and outer-ring nut pockets are now on the accessible finishing face.

Orient finishing E so its hex pocket lies over the shaft screw whose head is in the starting E's round recess. Its round socket lies over the temporary screw. The standing screw axes help keep this alignment.

## 11. Secure the layers, then reverse one shaft screw

1. Fit the finishing-face M3 shaft nut onto the correctly directed screw. Hold the layers seated and gently snug that screw using its head under the starting face.
2. Start the six guide nuts and twenty outer-ring nuts on the finishing face. They hold the concentric layers while you handle the temporary shaft screw.
3. Withdraw the temporary screw **downward through the starting face**, pulling its head out of the hex pocket. If the head is flush, push the screw tip from the finishing round socket to expose the head underneath, then withdraw it. The other shaft screw stays installed.
4. Load the vacated starting-face hex pocket with its M3 nut.
5. Turn the same withdrawn screw end-for-end and insert it **downward from the finishing face**, through the finishing E's round socket. Engage the nut you just loaded underneath.

You now have two opposed M3 × 35 shaft screws, with one head at each end. The twenty ring screws and six guide screws all retain their original direction.

## 12. Snug evenly and check movement

Snug the opposed shaft ties evenly, then the six guide fasteners, then the twenty outer-ring fasteners in opposing positions. Check movement after each group.

Hold the stationary carrier and turn E through a full revolution by hand. The two discs should orbit freely and the output casing should turn. If something catches, loosen the last fastener group and check that the bearings, sleeves and captive nuts are seated, the disc indexes match, and the cam offsets oppose each other.

Use a 2.5 mm hex key for the socket caps and a 2 mm key for the bench-assembled rotor clamps. The straight key paths for the finished assembly were checked. The E screw seats have a thin web beside the centre passage, so seat their heads gently.

The E drive face is recessed 0.8 mm behind the stationary carrier. Fit an attachment with a central boss or spacing that reaches E and clears the carrier. The centre passage is Ø6.50 mm.

## Layer order at a glance

| Build layer, bottom to top | Outside → centre |
|---|---|
| Starting face | Outside cylinder → 6810 inner carrier cap → 6704 E journal; all 28 screws point up |
| Starting bearings | 6810 → centred 6704 |
| Starting inner faces | OOBB plate → carrier core with eight nuts → N with attachment nuts |
| Spacers | Twenty outer contacts → six guide sleeves |
| First rotor | First C → complete B → closing C |
| Second rotor | Opposite C → complete A → closing C |
| Finishing inner faces | OOBB plate → carrier core with eight nuts → N with attachment nuts |
| Finishing bearings | 6810 → centred 6704 |
| Finishing face | Outside cylinder → 6810 inner carrier cap → 6704 E journal |
| Fasteners | Start finishing nuts, secure one shaft tie, withdraw and reverse the temporary tie |

[Layered insertion and screw-reversal checks](layered_assembly_verification.json) · [Final hardware and tool-access checks](assembly_sequence_verification.json) · [Bearing retention and operating clearances](fit_verification.json)
