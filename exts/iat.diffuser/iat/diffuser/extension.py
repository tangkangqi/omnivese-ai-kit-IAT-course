import omni.ext
import omni.ui as ui
from pathlib import Path
import omni.kit.viewport.utility as vp_utils
from PIL import Image
import omni.kit.notification_manager as notifier
from pxr import UsdGeom, UsdShade, UsdLux, Vt, Gf, Sdf, Usd, UsdUtils, Tf
import asyncio
import requests
import numpy as np
import shutil
import os
SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

import random
import string

import logging
logger = logging.getLogger(__name__)
logger.info("123")
logger.warning("456")

# import omni.kit.pipapi
# omni.kit.pipapi.install("requests")

# Functions and vars are available to other extension as usual in python: `example.python_ext.some_public_function(x)`
def some_public_function(x: int):
    print("[iat.diffuser] some_public_function was called with x: ", x)
    return x ** x


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class IatDiffuserExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.

    def __init__(self) -> None:
        super().__init__()
        self._name = 'IATDiffuser'
        self._path = omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__)
        self.outdir = Path(self._path) / '_output_images'
        self.outdir.mkdir(exist_ok=True, parents=True)
        self.cachedir = Path(self._path) / '_model_cache'
        self.cachedir.mkdir(exist_ok=True, parents=True)
        self.model_id = ''

        self.prev_imgpath = Path(self._path) / "data/dummy.png"
        self.imgpath = Path(self._path) / "data/dummy.png"
        self._image_shape = (512, 512)
        self.prev_texture_image = None
        self.texture_batch = []
        self.texture_image = self._load_image_from_file(self.imgpath)
        self.texture_mask = None
        self.diffuser_pipe = None
        self._seamless = True
        self._loaded_scene = False
        # self._loaded_scene = True
        self._logged_in = False
        self._image_provider = ui.ByteImageProvider()

        self.i2i_strength = 0.5

        self.batch_size = 4

        self.mini_image_providers = [ui.ByteImageProvider() for _ in range(self.batch_size)]
        self.imgpath_batch = ['' for _ in range(self.batch_size)]

        self._usd_context = omni.usd.get_context()
        self._stage_event_sub = self._usd_context.get_stage_event_stream().create_subscription_to_pop(
            self._on_stage_event
        )

    def on_startup(self, ext_id):
        # ext_id is the current extension id. It can be used with the extension manager to query additional information,
        # such as where this extension is located in the filesystem.
        print(f"{self} startup", flush=True)
        self._window = ui.Window(self._name, width=500, height=500)
        self.build_ui()

    
    def on_shutdown(self):
        print("[iat.diffuser] iat diffuser shutdown")
    
    def build_ui(self):
        with self._window.frame:
            with ui.VStack():
                with ui.Frame(height=50):
                    with ui.VStack():
                        self.text_box = ui.StringField(style={'font_size': 30})
                        self.text_box.model.set_value('an old tree bark')

                        with ui.HStack():
                            generate_button = ui.Button('Text to Image', height=40)
                            generate_button.set_clicked_fn(self.inference)
                            i2i_button = ui.Button('Image to Image', height=40)
                            i2i_button.set_clicked_fn(self.i2i_inference)
                            undo_button = ui.Button('Undo', height=40)
                            undo_button.set_clicked_fn(self._on_undo_click)

                        with ui.HStack():
                            ui.Label("diffusion service url:", style={'font_size': 15})
                            self.url_box = ui.StringField(style={'font_size': 20}, width=450)
                            self.url_box.model.set_value('http://127.0.0.1:8000')

                        ui.Spacer(height=5)
                        with ui.HStack():
                            ui.Label('Scale')
                            ui.Spacer(width=5)
                            ui.Label('Strength')
                            ui.Spacer(width=5)
                            ui.Label('Batch size')

                with ui.Frame(height=50):
                    with ui.VStack():
                        # ui.Spacer(height=10)
                        with ui.HStack():
                            model_button = ui.Button(f"Load models", height=40)
                            model_button.set_clicked_fn(self._load_model)
                            ui.Spacer(width=10)
                            image_button = ui.Button(f"Select image", height=40)
                            image_button.set_clicked_fn(self._on_select_image_click)
                        with ui.Frame(height=450):
                            with ui.VStack():
                                image_provider = ui.ImageWithProvider(self._image_provider) #, fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT)
                self.set_image_provider(self.texture_image)



    ### STAGE & USD ###
    def _on_stage_event(self, evt):
        if evt.type == int(omni.usd.StageEventType.OPENED):
            print(f"{self} Stage opened")
            self._on_stage_opened()
        elif evt.type == int(omni.usd.StageEventType.ASSETS_LOADED):
            self._hide_stage_defaults()

    def _on_stage_opened(self):
        self._load_scene()

    def _load_scene(self):
        if self._loaded_scene:
            return

        self._usd_context = omni.usd.get_context()
        stage = self._usd_context.get_stage()

        preset_path = str(Path(self._path) / "data/scene.usd")
        root_layer = stage.GetRootLayer()
        root_layer.subLayerPaths = [preset_path]

        # HACK: move prims to /World (default prim) from /Environment to allow changes to visibility
        cube = stage.GetPrimAtPath("/Environment/Cube")
        if cube:
            omni.kit.commands.execute("MovePrimCommand", path_from="/Environment/Cube", path_to="/World/Cube")
            cube = stage.GetPrimAtPath("/World/Cube")
            cube.GetAttribute("visibility").Set("inherited")

        sphere = stage.GetPrimAtPath("/Environment/Sphere")
        if cube:
            omni.kit.commands.execute("MovePrimCommand", path_from="/Environment/Sphere", path_to="/World/Sphere")
            sphere = stage.GetPrimAtPath("/World/Sphere")
            sphere.GetAttribute("visibility").Set("inherited")

        vp = vp_utils.get_active_viewport()
        vp.set_active_camera("/World/Camera")

        self._loaded_scene = True

    def _hide_stage_defaults(self):
        stage = omni.usd.get_context().get_stage()

        ground_plane = stage.GetPrimAtPath("/Environment/GroundPlane")
        if ground_plane:
            print(f"{self} hiding /Environment/GroundPlane")
            ground_plane.GetAttribute("visibility").Set("invisible") # hide ground plane

        ground_plane = stage.GetPrimAtPath("/Environment/Plane")
        if ground_plane:
            print(f"{self} hiding /Environment/Plane")
            ground_plane.GetAttribute("visibility").Set("invisible") # hide ground plane

    ## Update Materials
    def _update_material(self, material_path, params):
        stage = self._usd_context.get_stage()
        # ctx = omni.usd.get_context()
        # stage = ctx.get_stage()
        # selection = ctx.get_selection().get_selected_prim_paths()

        material = stage.GetPrimAtPath(material_path)
        logger.warn((f"{self} material: {material}"))
        shader = UsdShade.Shader(omni.usd.get_shader_from_material(material.GetPrim(), True))
        logger.warn(f"{self} shader: {shader}")
        # For each parameter, write to material
        for param, value in params.items():
            logger.warn(f"{self} creating & getting input: {param}")
            shader.CreateInput(param, Sdf.ValueTypeNames.Asset)
            shader.GetInput(param).Set(value)

    ## Click select image
    def _on_select_image_click(self):
        """Show filepicker after load image is clicked"""
        self._filepicker = omni.kit.window.filepicker.FilePickerDialog(
            f"{self}/Select Image",
            click_apply_handler=lambda f, d: asyncio.ensure_future(self._on_image_selection(f, d)),
        )
        try:
            self._filepicker.navigate_to(os.path.expanduser("~/"))
        except Exception:
            print(f"could not find {os.path.expanduser('~')}")
        self._filepicker.refresh_current_directory()
        omni.kit.window.filepicker

    def _on_undo_click(self):
        print(self.imgpath)
        print(self.prev_imgpath)
        self.imgpath = self.prev_imgpath
        self.texture_image = self._load_image_from_file(self.imgpath)
        self.set_image_provider(self.texture_image)
        self._update_material('/Environment/Looks/OmniPBR', {"diffuse_texture": str(self.imgpath) })

    def _on_model_select_click(self):
        pass

    async def _on_image_selection(self, filename, dirname):
        """Load the selected image."""
        selections = self._filepicker.get_current_selections()
        if os.path.isfile(selections[0]):
            self.imgpath = selections[0]
        else:
            print('Select a valid image file.')
            return

        print(f"{self} Loading image from: {self.imgpath}")
        self.texture_image = self._load_image_from_file(self.imgpath)
        self.set_image_provider(self.texture_image)
        self._update_material('/Environment/Looks/OmniPBR', {"diffuse_texture": str(self.imgpath) })
        self._filepicker.hide()
        self._window.frame.rebuild()

    def _load_image_from_file(self, imgpath):
        img = Image.open(imgpath)
        # w, h = img.size
        # min_size = min(w, h)
        img = img.resize(self._image_shape)
        return img
    
    def refresh_image(self):
        self.image_box.set_style({'image_url': str(self.imgpath)})

    ### MODEL ###
    def _load_model(self, new_model_id=None, new_model_inpaint_id=None):
        pass

    def i2i_inference(self):
        pass

    def generate(self, prompt):
        base_url = self.url_box.model.get_value_as_string()
        url = "%s/txt2img/%s"%(base_url, prompt)
        # res = {'file_name': 'res.jpg', 'prompt': 'how are you', 'time': 11.930987119674683}
        res = requests.get(url).json()
        print(res)

        im_url = "%s/download/%s"%(base_url, res["file_name"])
        r = requests.get(im_url)
        open(os.path.join(SCRIPT_PATH, "data", "res.jpg"), "wb").write(r.content)
        # shutil.copy(os.path.join(SCRIPT_PATH, "data", "res.jpg"), os.path.join(self.outdir, res["file_name"]))
        # random_name_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        image_num = len(os.listdir(self.outdir))
        fpath = os.path.join(self.outdir, "%04d-%s"%(image_num, res["file_name"]))
        shutil.copy(os.path.join(SCRIPT_PATH, "data", "res.jpg"), fpath)
        return r.content
    
    def inference(self):
    
        prompt = self.text_box.model.get_value_as_string()
        print(f"{self} {prompt}")
        # self.texture_batch = self.diffuser_pipe([prompt]*self.batch_size).images
        self.texture_batch = self.generate(prompt=prompt)
        # texture update
        self.prev_imgpath = self.imgpath
        self.imgpath = os.path.join(SCRIPT_PATH, "data", "res.jpg")
        self.texture_image = self._load_image_from_file(os.path.join(SCRIPT_PATH, "data", "res.jpg"))

        logger.warn("diffusion images: %s"%(self.imgpath))

        self._load_scene()
        self._update_material('/Environment/Looks/OmniPBR', {"diffuse_texture": str(self.imgpath) })
        self.set_image_provider(self.texture_image)

    def set_image_provider(self, img):
        if isinstance(img, Image.Image):
            img = np.asarray(img, dtype=np.uint8)
        elif isinstance(img, np.ndarray):
            pass
        else:
            print('Unknown image format.')
        # Create alpha channel since ImageProvider expects a 4-channel image
        alpha_channel = np.ones_like(img[:,:,[0]], dtype=np.uint8) * 255

        if img.shape[2] == 3 :
            img = np.concatenate([img, alpha_channel], axis=2)

        print('updating image provider')
        self._image_provider.set_data_array(img, (img.shape[0], img.shape[1]))