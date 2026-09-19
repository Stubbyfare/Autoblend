# Autoblend

Autoblend is a Blender add-on that creates a practical humanoid armature from the model parts you identify in a few clicks.

## Features

- Pick a mesh for the torso, head, left/right arms, and left/right legs from the sidebar.
- Generate a humanoid armature with a root, spine, neck, head, and limbs.
- Optionally parent the selected model parts to the new armature with automatic weights.
- Rebuild safely by replacing the previous Autoblend armature.
- Works with Blender 3.6 LTS and Blender 4.x.

Autoblend uses the locations and dimensions of your chosen objects, so it works with separate body-part meshes as well as rough blockouts. Apply object transforms before generating for the most predictable results.

## Install

1. Download or clone this repository.
2. In Blender, open **Edit → Preferences → Add-ons → Install…**.
3. Select the repository's `autoblend` folder as a zip, or zip the folder first and select that zip.
4. Enable **Rigging: Autoblend**.

## Use

1. Open the 3D View sidebar with **N** and select the **Autoblend** tab.
2. Assign a torso. Head, arm, and leg fields are optional, but assigning them improves bone placement.
3. Click **Generate Rig**. Enable **Parent with Automatic Weights** if the meshes should be skinned immediately.
4. Pose the generated armature in Pose Mode.

The add-on does not overwrite meshes. A generated armature is named `Autoblend_Rig`; generating again replaces only the previous armature with that name.

## Notes

- The add-on is intentionally a deterministic starting rig, not a full motion-capture or topology analysis system.
- Automatic weights can fail on non-manifold or very small meshes; Blender will keep the generated armature and report the affected objects.
- The source is provided under the MIT license.
