import bpy
import sys
import subprocess
from collections import namedtuple
from bpy.props import (
    PointerProperty,
    StringProperty,
    BoolProperty,
    IntProperty
)

from . splt_panel import *
from . splt_ops import *
from bpy.app.handlers import persistent

bl_info = {
    "name": "WikiImageGenerator",
    "author": "Radiator Syrup",
    "description": "An addon to automate the rendering of game models into 2d images",
    "blender": (2, 80, 0),
    "version": (2, 2, 0),
    "location": "",
    "warning": "",
    "category": "Generic"
}

Dependency = namedtuple("Dependency", ["module", "package", "name"])

dependencies = (Dependency(module="PIL", package="Pillow", name=None),
                Dependency(module="numpy", package=None, name=None))


def add_blender_python_paths():
    import os
    import bpy

    blender_python_path = os.path.join(bpy.utils.script_path(), "modules")
    if blender_python_path not in sys.path:
        sys.path.append(blender_python_path)

    python_lib_path = os.path.join(bpy.app.binary_path_python, "lib")
    if python_lib_path not in sys.path:
        sys.path.append(python_lib_path)


def import_module(module_name, global_name=None):
    import importlib

    if global_name is None:
        global_name = module_name

    try:
        globals()[global_name] = importlib.import_module(module_name)
    except ImportError as e:
        print(f"Error importing {module_name}: {e}")


def set_game_type(self, context):
    if not self:
        self = context.window_manager
    context.scene.render.game_type = self.game_type


class SPLT_OT_install_dependencies(bpy.types.Operator):
    bl_idname = "wiki.install_dependencies"
    bl_label = "Install dependencies"
    bl_description = ("Downloads and installs the required python packages for this add-on. "
                      "Internet connection is required. Blender may have to be started with "
                      "elevated permissions in order to install the package")
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(self, context):
        return not context.window_manager.dependencies_installed

    def execute(self, context):
        print(sys.executable)
        try:
            add_blender_python_paths()
            for dependency in dependencies:
                import_module(module_name=dependency.module,
                              global_name=dependency.name)
        except ImportError as err:
            self.report({"ERROR"}, f"Error importing: {err}")
            return {"CANCELLED"}

        context.window_manager.dependencies_installed = True
        return {"FINISHED"}


class SPLT_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    game_type: bpy.props.EnumProperty(
        name="Game",
        items=[
            ('noGame', 'Without preferences', 'No game-specific preferences apply'),
            ('acnh', 'Animal Crossing: New Horizons', 'For Animal Crossing Enciclopedia'),
            ('acnl', '(experimental) Animal Crossing: New Leaf', 'For Animal Crossing Enciclopedia'),
            ('splat2', 'Splatoon 2', 'For Inkipedia, Inkipedia ES and Inkipédia'),
            ('splat3', 'Splatoon 3', 'For Inkipedia, Inkipedia ES and Inkipédia'),
        ],
        default='noGame',
        update=set_game_type
    )

    wiki_language: bpy.props.EnumProperty(
        name="Category languaje",
        items=[
            ('en', 'English', 'Category will be added in English'),
            ('es', 'Spanish', 'Category will be added in Spanish'),
            ('fr', 'French', 'Category will be added in French'),
        ],
        default=None,
    )

    delete_tmp: bpy.props.BoolProperty(
        name="Save temporary files",
        default=False
    )

    delete_preview: bpy.props.BoolProperty(
        name="Save preview image",
        default=False
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "game_type")
        layout.prop(self, "wiki_language")
        layout.prop(self, "delete_tmp")
        layout.prop(self, "delete_preview")
        layout.operator(
            SPLT_OT_install_dependencies.bl_idname, icon="CONSOLE")


preference_classes = (SPLT_PT_warning_panel,
                      SPLT_OT_install_dependencies,
                      SPLT_preferences)
classes = (RotateAndScale, PositionCamera,
           PositionModel, FixFaces, AddHDRI, FixLights, RenderWiki, CheckRotateModel,
           SPLT_PT_Panel_1, SPLT_PT_Panel_2, SPLT_PT_Panel_2_1, SPLT_PT_Panel_2_2, SPLT_PT_Panel_3, SPLT_PT_Panel_4, SPLT_PT_Panel_5, SPLT_PT_Panel_5_1, SPLT_PT_Panel_6)

dependencies_installed = False


def set_x_resolution(self, context):
    if not self:
        self = context.window_manager
    context.scene.render.resolution_x = self.x_resolution


def set_y_resolution(self, context):
    if not self:
        self = context.window_manager
    context.scene.render.resolution_y = self.y_resolution

@persistent
def load_handler(dummy):
    pass


def register():
    global dependencies_installed
    dependencies_installed = False

    for cls in preference_classes:
        bpy.utils.register_class(cls)

    try:
        for dependency in dependencies:
            import_module(module_name=dependency.module,
                          global_name=dependency.name)
        dependencies_installed = True
    except ModuleNotFoundError as e:
        print(e)
        pass

    if dependencies_installed:
        for cls in classes:
            bpy.utils.register_class(cls)

    bpy.app.handlers.load_post.append(load_handler)


    mode_options = [
            ("JPEG", "JPEG", '', 'JPEG', 0),
            ("PNG", "PNG", '', 'PNG', 1),

        ]

    bpy.types.WindowManager.output_format = bpy.props.EnumProperty(
        items=mode_options,
        description="File format",
        default=1,
    )

    bpy.types.WindowManager.objectselection_props = PointerProperty(
        type=bpy.types.Object
    )
    
    bpy.types.WindowManager.x_rotations = IntProperty(
        name="X",
        default=36,
        min=2
    )
    
    bpy.types.WindowManager.y_rotations = IntProperty(
        name="Y",
        min=1,
        default=1
    )
    
    bpy.types.WindowManager.x_resolution = IntProperty(
        name="X",
        default=296,
        min=1,
        update=set_x_resolution
    )
    
    bpy.types.WindowManager.y_resolution = IntProperty(
        name="Y",
        default=228,
        min=1,
        update=set_y_resolution
    )
    
    bpy.types.WindowManager.delete_tmp = BoolProperty(
        name="Save temporary files",
        default=bpy.context.preferences.addons[__name__].preferences.delete_tmp,
    )
    
    bpy.types.WindowManager.delete_preview = BoolProperty(
        name="Save preview image",
        default=bpy.context.preferences.addons[__name__].preferences.delete_preview,
    )
    
    bpy.types.WindowManager.overwrite_files = BoolProperty(
        name="Overwrite files with number",
        default=False
    )

    bpy.types.WindowManager.dependencies_installed = BoolProperty(
        name="Dependencies installed",
        default=dependencies_installed
    )
    
    bpy.types.WindowManager.number_overwrite = IntProperty(
        name="Number",
        default=1,
        min=1
    )
    
    bpy.types.WindowManager.game_type = bpy.props.EnumProperty(
    items=[
        ('noGame', 'Without preferences', 'No game-specific preferences apply'),
        ('acnh', 'Animal Crossing: New Horizons', 'For Animal Crossing Enciclopedia'),
        ('acnl', '(experimental) Animal Crossing: New Leaf', 'For Animal Crossing Enciclopedia'),
        ('splat2', 'Splatoon 2', 'For Inkipedia, Inkipedia ES and Inkipédia'),
        ('splat3', 'Splatoon 3', 'For Inkipedia, Inkipedia ES and Inkipédia'),
    ],
    default=bpy.context.preferences.addons[__name__].preferences.game_type,
    update=set_game_type
    )
    
    bpy.types.WindowManager.wiki_language = bpy.props.EnumProperty(
    items=[
        ('en', 'English', 'Category will be added in English'),
        ('es', 'Spanish', 'Category will be added in Spanish'),
        ('fr', 'French', 'Category will be added in French'),
    ],
    default=bpy.context.preferences.addons[__name__].preferences.wiki_language,
    )
    
    bpy.types.WindowManager.output_folder = StringProperty(
        name="Output Folder",
        description="Path to Directory",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
    )
    
    bpy.app.handlers.load_post.append(load_handler)

    bpy.types.WindowManager.loop_rotation = bpy.props.BoolProperty(
        name="Loop Rotation",
        description="Continuously loop the rotation animation",
        default=False
    )
    
    bpy.types.WindowManager.rotation_speed = bpy.props.EnumProperty(
        items=[
            ('0.25', 'x0.25', 'Quarter speed'),
            ('0.5', 'x0.5', 'Half speed'),
            ('1', 'x1', 'Normal speed'),
            ('2', 'x2', 'Double speed'),
            ('5', 'x5', 'Five times speed'),
        ],
        name="Speed",
        description="Set the speed of rotation",
        default='1'
    )


def unregister():
    try:
        for cls in preference_classes:
            bpy.utils.unregister_class(cls)

        if dependencies_installed:
            for cls in classes:
                bpy.utils.unregister_class(cls)
    except RuntimeError:
        pass

    del bpy.types.WindowManager.objectselection_props
    del bpy.types.WindowManager.x_rotations
    del bpy.types.WindowManager.output_folder
    del bpy.types.WindowManager.x_resolution
    del bpy.types.WindowManager.y_resolution
    del bpy.types.WindowManager.dependencies_installed
    del bpy.types.WindowManager.loop_rotation
    bpy.app.handlers.load_post.remove(load_handler)
