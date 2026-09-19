"""Autoblend - one-click humanoid rig generation for Blender."""

bl_info = {
    "name": "Autoblend",
    "author": "Stubbyfare",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Autoblend",
    "description": "Create a humanoid rig from selected model parts in a few clicks",
    "category": "Rigging",
}

from . import addon


def register():
    addon.register()


def unregister():
    addon.unregister()
