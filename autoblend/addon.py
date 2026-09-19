"""User interface and rig builder for the Autoblend Blender add-on."""

import math
import bpy
from mathutils import Vector
from bpy.props import BoolProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup

RIG_NAME = "Autoblend_Rig"


def _object_center(obj):
    # Evaluated world-space bounding-box center; dimensions remain useful for meshes
    # whose origins have been moved away from the visible geometry.
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return sum(corners, Vector()) / 8.0


def _object_height(obj):
    return max((obj.matrix_world @ Vector(c)).z for c in obj.bound_box) - min(
        (obj.matrix_world @ Vector(c)).z for c in obj.bound_box
    )


def _part_center(part, fallback):
    return _object_center(part) if part else Vector(fallback)


def _make_bone(armature, name, head, tail, parent=None, use_connect=False):
    bone = armature.edit_bones.new(name)
    bone.head = head
    bone.tail = tail if (tail - head).length > 0.001 else head + Vector((0, 0, 0.1))
    if parent:
        bone.parent = parent
        bone.use_connect = use_connect
    return bone


def _build_rig(parts):
    old = bpy.data.objects.get(RIG_NAME)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

    arm_data = bpy.data.armatures.new(RIG_NAME)
    arm_obj = bpy.data.objects.new(RIG_NAME, arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    arm_data.display_type = "BBONE"
    arm_obj.show_in_front = True

    bpy.ops.object.mode_set(mode="EDIT")
    torso = parts.torso
    torso_center = _part_center(torso, (0, 0, 1.2))
    torso_height = max(_object_height(torso), 1.0) if torso else 2.0
    # Use the torso's center as the horizontal reference and keep a stable scale
    # for primitive/blockout models.
    x, y = torso_center.x, torso_center.y
    bottom = torso_center.z - torso_height * 0.5
    top = torso_center.z + torso_height * 0.5
    pelvis_z = bottom + torso_height * 0.15
    chest_z = bottom + torso_height * 0.68
    neck_z = top - torso_height * 0.08
    head = parts.head
    head_center = _part_center(head, (x, y, top + torso_height * 0.18))
    head_height = max(_object_height(head), torso_height * 0.18) if head else torso_height * 0.22

    root = _make_bone(arm_data, "root", (x, y, bottom - torso_height * 0.08), (x, y, pelvis_z))
    pelvis = _make_bone(arm_data, "pelvis", (x, y, pelvis_z), (x, y, chest_z - torso_height * 0.16), root)
    spine = _make_bone(arm_data, "spine", (x, y, chest_z - torso_height * 0.16), (x, y, chest_z), pelvis, True)
    neck = _make_bone(arm_data, "neck", (x, y, chest_z), (x, y, neck_z), spine, True)
    _make_bone(arm_data, "head", (x, y, neck_z), (head_center.x, head_center.y, head_center.z + head_height * 0.35), neck, True)

    shoulder_z = chest_z - torso_height * 0.02
    shoulder_width = torso_height * 0.22
    if torso:
        shoulder_width = max(torso.dimensions.x * 0.5, shoulder_width)
    hip_width = max(torso_height * 0.14, shoulder_width * 0.48)
    arm_length = torso_height * 0.34
    leg_length = torso_height * 0.52

    def limb(side, sign, arm_part, leg_part):
        shoulder = _part_center(arm_part, (x + sign * shoulder_width, y, shoulder_z))
        wrist = _part_center(arm_part, (x + sign * (shoulder_width + arm_length), y, shoulder_z - torso_height * 0.06))
        elbow = shoulder.lerp(wrist, 0.5) + Vector((0, 0, -torso_height * 0.04))
        clavicle = _make_bone(arm_data, f"{side}_clavicle", (x, y, shoulder_z), shoulder, spine)
        upper = _make_bone(arm_data, f"{side}_upper_arm", shoulder, elbow, clavicle, True)
        _make_bone(arm_data, f"{side}_forearm", elbow, wrist, upper, True)
        _make_bone(arm_data, f"{side}_hand", wrist, wrist + (wrist - elbow).normalized() * torso_height * 0.10, arm_data.edit_bones[f"{side}_forearm"], True)
        hip = _part_center(leg_part, (x + sign * hip_width, y, pelvis_z - torso_height * 0.12))
        foot = _part_center(leg_part, (x + sign * hip_width, y - torso_height * 0.05, bottom - torso_height * 0.04))
        knee = hip.lerp(foot, 0.5)
        thigh = _make_bone(arm_data, f"{side}_thigh", hip, knee, pelvis)
        shin = _make_bone(arm_data, f"{side}_shin", knee, foot, thigh, True)
        _make_bone(arm_data, f"{side}_foot", foot, foot + Vector((0, -torso_height * 0.14, 0)), shin, True)

    limb("left", -1, parts.left_arm, parts.left_leg)
    limb("right", 1, parts.right_arm, parts.right_leg)
    bpy.ops.object.mode_set(mode="OBJECT")
    arm_obj.select_set(False)
    return arm_obj


def _parent_with_weights(arm_obj, parts):
    meshes = {getattr(parts, name) for name in ("torso", "head", "left_arm", "right_arm", "left_leg", "right_leg") if getattr(parts, name)}
    meshes = {obj for obj in meshes if obj.type == "MESH" and obj != arm_obj}
    if not meshes:
        return []
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    failed = []
    for obj in meshes:
        try:
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        except RuntimeError:
            failed.append(obj.name)
            obj.select_set(False)
    bpy.ops.object.select_all(action="DESELECT")
    arm_obj.select_set(True)
    return failed


class AutoblendParts(PropertyGroup):
    torso: PointerProperty(name="Torso", type=bpy.types.Object, poll=lambda s, o: o.type == "MESH")
    head: PointerProperty(name="Head", type=bpy.types.Object, poll=lambda s, o: o.type == "MESH")
    left_arm: PointerProperty(name="Left Arm", type=bpy.types.Object, poll=lambda s, o: o.type == "MESH")
    right_arm: PointerProperty(name="Right Arm", type=bpy.types.Object, poll=lambda s, o: o.type == "MESH")
    left_leg: PointerProperty(name="Left Leg", type=bpy.types.Object, poll=lambda s, o: o.type == "MESH")
    right_leg: PointerProperty(name="Right Leg", type=bpy.types.Object, poll=lambda s, o: o.type == "MESH")
    automatic_weights: BoolProperty(name="Parent with Automatic Weights", default=True)


class AUTOBLEND_OT_generate(Operator):
    bl_idname = "autoblend.generate"
    bl_label = "Generate Rig"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.autoblend_parts.torso is not None

    def execute(self, context):
        parts = context.scene.autoblend_parts
        arm_obj = _build_rig(parts)
        failed = _parent_with_weights(arm_obj, parts) if parts.automatic_weights else []
        message = "Autoblend rig generated"
        if failed:
            message += f"; weights skipped for {', '.join(failed)}"
        self.report({"WARNING" if failed else "INFO"}, message)
        return {"FINISHED"}


class AUTOBLEND_OT_clear(Operator):
    bl_idname = "autoblend.clear_parts"
    bl_label = "Clear Part Assignments"

    def execute(self, context):
        context.scene.autoblend_parts = AutoblendParts()
        return {"FINISHED"}


class AUTOBLEND_PT_panel(Panel):
    bl_label = "Autoblend"
    bl_idname = "AUTOBLEND_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Autoblend"

    def draw(self, context):
        layout = self.layout
        parts = context.scene.autoblend_parts
        layout.label(text="Assign your model parts", icon="ARMATURE_DATA")
        for prop in ("torso", "head", "left_arm", "right_arm", "left_leg", "right_leg"):
            layout.prop(parts, prop)
        layout.separator()
        layout.prop(parts, "automatic_weights")
        row = layout.row(align=True)
        row.operator("autoblend.generate", icon="ARMATURE_DATA")
        row.operator("autoblend.clear_parts", text="", icon="X")
        if not parts.torso:
            layout.label(text="A torso is required", icon="INFO")


classes = (AutoblendParts, AUTOBLEND_OT_generate, AUTOBLEND_OT_clear, AUTOBLEND_PT_panel)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.autoblend_parts = PointerProperty(type=AutoblendParts)


def unregister():
    del bpy.types.Scene.autoblend_parts
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
