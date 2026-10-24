"""Build a labeled, clickable human anatomy scene in Blender.

Run:  blender -b -P build_anatomy.py -- [--out anatomy.blend] [--frames DIR]
NOTE: written without Blender available; not executed.

- One collection per organ system (toggle in Outliner or the Anatomy panel).
- N-panel > Anatomy > "Enable Click Labels": click an organ to show its name.
- "Turntable" empty is keyframed 0..360 deg, looping (frames 1-120).
- --frames DIR renders a PNG sequence for use in a Hyperframes composition.
"""
import sys, math
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default

OUT = arg("--out", "/workspace/anatomy.blend")
FRAMES = arg("--frames")

BONE = (0.9, 0.88, 0.8, 1)
# (name, system, kind, location, scale, rgba)
ORGANS = [
    ("Skull", "Skeletal", "sphere", (0, 0, 1.72), (0.11, 0.13, 0.13), BONE),
    ("Spine", "Skeletal", "cyl", (0, 0.05, 1.15), (0.03, 0.03, 0.55), BONE),
    ("Ribcage", "Skeletal", "sphere", (0, 0, 1.25), (0.2, 0.12, 0.2), BONE),
    ("Pelvis", "Skeletal", "sphere", (0, 0, 0.85), (0.17, 0.09, 0.08), BONE),
    ("Femur L", "Skeletal", "cyl", (0.09, 0, 0.5), (0.035, 0.035, 0.3), BONE),
    ("Femur R", "Skeletal", "cyl", (-0.09, 0, 0.5), (0.035, 0.035, 0.3), BONE),
    ("Brain", "Nervous", "sphere", (0, 0, 1.75), (0.09, 0.1, 0.08), (0.95, 0.7, 0.75, 1)),
    ("Spinal Cord", "Nervous", "cyl", (0, 0.04, 1.3), (0.012, 0.012, 0.35), (0.95, 0.9, 0.5, 1)),
    ("Heart", "Circulatory", "sphere", (0.04, -0.05, 1.3), (0.05, 0.045, 0.06), (0.8, 0.05, 0.08, 1)),
    ("Aorta", "Circulatory", "cyl", (-0.01, 0, 1.2), (0.015, 0.015, 0.25), (0.7, 0.0, 0.05, 1)),
    ("Lung L", "Respiratory", "sphere", (0.1, -0.01, 1.32), (0.07, 0.06, 0.13), (0.9, 0.55, 0.6, 1)),
    ("Lung R", "Respiratory", "sphere", (-0.1, -0.01, 1.32), (0.07, 0.06, 0.13), (0.9, 0.55, 0.6, 1)),
    ("Trachea", "Respiratory", "cyl", (0, -0.02, 1.52), (0.015, 0.015, 0.12), (0.7, 0.8, 0.9, 1)),
    ("Stomach", "Digestive", "sphere", (0.08, -0.05, 1.05), (0.07, 0.05, 0.06), (0.9, 0.5, 0.35, 1)),
    ("Liver", "Digestive", "sphere", (-0.09, -0.05, 1.08), (0.1, 0.06, 0.05), (0.45, 0.15, 0.1, 1)),
    ("Intestines", "Digestive", "sphere", (0, -0.05, 0.93), (0.12, 0.06, 0.08), (0.9, 0.65, 0.5, 1)),
    ("Kidney L", "Urinary", "sphere", (0.07, 0.03, 1.0), (0.03, 0.025, 0.045), (0.55, 0.15, 0.15, 1)),
    ("Kidney R", "Urinary", "sphere", (-0.07, 0.03, 1.0), (0.03, 0.025, 0.045), (0.55, 0.15, 0.15, 1)),
    ("Bladder", "Urinary", "sphere", (0, -0.04, 0.8), (0.04, 0.04, 0.04), (0.9, 0.8, 0.3, 1)),
]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT" if bpy.app.version >= (4, 2, 0) else "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
scene.frame_start, scene.frame_end = 1, 120
scene.render.fps = 24

world = bpy.data.worlds.new("World"); world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.04, 0.08, 1)
scene.world = world

root = bpy.data.objects.new("Turntable", None)
scene.collection.objects.link(root)

def mat(name, rgba):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Roughness"].default_value = 0.45
    return m

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1.0))
body = bpy.context.object; body.name = "Body Shell"
body.scale = (0.28, 0.16, 1.0); body.parent = root
body.data.materials.append(mat("Shell", (0.5, 0.7, 0.9, 1)))
body.display_type = "WIRE"; body.hide_select = True
body.hide_render = True

systems = {}
def to_coll(o, coll):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)

for name, system, kind, loc, sc, rgba in ORGANS:
    if kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc, segments=48, ring_count=24)
    else:
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=loc, vertices=32)
    o = bpy.context.object
    o.name = name; o.scale = sc; o.parent = root
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat(name, rgba))
    o["system"] = system; o["label"] = name
    coll = systems.get(system)
    if coll is None:
        coll = systems[system] = bpy.data.collections.new(system)
        scene.collection.children.link(coll)
    to_coll(o, coll)

    side = 0.35 if loc[0] >= 0 else -0.35
    bpy.ops.object.text_add(location=(side, -0.2, loc[2]), rotation=(math.radians(90), 0, 0))
    t = bpy.context.object; t.name = "Label " + name
    t.data.body = name; t.data.size = 0.04
    t.data.align_x = "LEFT" if side > 0 else "RIGHT"
    t.data.materials.append(mat("Label", (1, 1, 1, 1)))
    t.parent = root; t.hide_select = True
    to_coll(t, coll)

    cu = bpy.data.curves.new("Line " + name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = 0.0012
    sp = cu.splines.new("POLY"); sp.points.add(1)
    sp.points[0].co = (loc[0], loc[1], loc[2], 1)
    sp.points[1].co = (side, -0.2, loc[2], 1)
    ln = bpy.data.objects.new("Line " + name, cu)
    ln.data.materials.append(mat("Line", (0.6, 0.85, 1, 1)))
    ln.parent = root; ln.hide_select = True
    coll.objects.link(ln)

cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Camera", cam_d)
scene.collection.objects.link(cam)
cam.location = (0, -4.2, 1.0); cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam
for n, loc, e in (("Key", (2, -3, 3), 400), ("Fill", (-3, -2, 1), 150)):
    l = bpy.data.lights.new(n, "AREA"); l.energy = e; l.size = 3
    lo = bpy.data.objects.new(n, l); lo.location = loc
    scene.collection.objects.link(lo)

root.rotation_euler = (0, 0, 0); root.keyframe_insert("rotation_euler", frame=1)
root.rotation_euler = (0, 0, math.radians(360)); root.keyframe_insert("rotation_euler", frame=121)
for fc in root.animation_data.action.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"

PICKER = '''import bpy
class ANATOMY_OT_pick(bpy.types.Operator):
    bl_idname = "anatomy.pick"; bl_label = "Click Labels"
    def modal(self, ctx, ev):
        if ev.type == "LEFTMOUSE" and ev.value == "RELEASE":
            o = ctx.view_layer.objects.active
            if o and "system" in o and o.select_get():
                ctx.scene["picked"] = o["label"] + " (" + o["system"] + " system)"
                for a in ctx.screen.areas: a.tag_redraw()
        if ev.type in {"ESC"}:
            return {"CANCELLED"}
        return {"PASS_THROUGH"}
    def invoke(self, ctx, ev):
        ctx.window_manager.modal_handler_add(self); return {"RUNNING_MODAL"}
class ANATOMY_PT_panel(bpy.types.Panel):
    bl_label = "Anatomy"; bl_space_type = "VIEW_3D"; bl_region_type = "UI"; bl_category = "Anatomy"
    def draw(self, ctx):
        l = self.layout
        l.operator("anatomy.pick", text="Enable Click Labels (Esc stops)")
        l.label(text="Selected: " + ctx.scene.get("picked", "-"))
        for c in ctx.scene.collection.children:
            lc = ctx.view_layer.layer_collection.children.get(c.name)
            if lc: l.prop(lc, "exclude", text=c.name, invert_checkbox=True)
def register():
    bpy.utils.register_class(ANATOMY_OT_pick); bpy.utils.register_class(ANATOMY_PT_panel)
register()
'''
ROTATE = '''"""Run from Text editor: spin the model by SPEED degrees about Z."""
import bpy, math
SPEED = 3.0
bpy.data.objects["Turntable"].rotation_euler.z += math.radians(SPEED)
'''
t = bpy.data.texts.new("anatomy_picker.py"); t.write(PICKER); t.use_module = True
t = bpy.data.texts.new("rotate.py"); t.write(ROTATE)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("Saved", OUT)
if FRAMES:
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = FRAMES.rstrip("/") + "/frame_"
    bpy.ops.render.render(animation=True)
