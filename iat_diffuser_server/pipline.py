from fastapi import FastAPI
from fastapi import File, UploadFile
from fastapi.responses import FileResponse
import time
import shutil
import torch
from diffusers import DiffusionPipeline

app = FastAPI()

def load_lcm_pipe():
    pipe = DiffusionPipeline.from_pretrained("SimianLuo/LCM_Dreamshaper_v7")

    # To save GPU memory, torch.float16 can be used, but it may compromise image quality.
    pipe.to(torch_device="cuda", torch_dtype=torch.float32)

    return pipe

pipe = load_lcm_pipe()

@app.get("/download/{name_file}")
def download_file(name_file: str):
    return FileResponse(path= "data/" + name_file, media_type='application/octet-stream', filename=name_file)

def gen_image(prompt):
    num_inference_steps = 4
    images = pipe(prompt=prompt, num_inference_steps=num_inference_steps, guidance_scale=8.0, lcm_origin_steps=50, output_type="pil").images
    print(len(images))
    image = images[0]

    fname = "%s.jpg"%("-".join(prompt.split(" ")))
    image.save("data/" + fname)
    shutil.copy("data/" + fname, "data/res.jpg")
    return fname

def test_infer(self):
    prompt = "Self-portrait oil painting, a beautiful cyborg with golden hair, 8k"
    gen_image(prompt)

@app.get("/txt2img/{prompt}")
def get_image(prompt: str):
    t0 = time.time()
    fname = gen_image(prompt)
    return {"file_name": fname, "prompt": prompt, "time": time.time() - t0}