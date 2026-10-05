import torch
from diffusers import StableDiffusionPipeline
from diffusers import DPMSolverMultistepScheduler
import os
import uuid

from diffusers import AutoencoderKL


# Force GPU
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Running on: {device}")



# Set SD_MODEL_PATH / SD_VAE_PATH in your .env to point at wherever you keep
# these models on your machine (local folder or a Hugging Face repo id).
# The old hardcoded "D:\F32 (2)\..." path only worked on the original dev's PC.
model_id = os.environ.get("SD_MODEL_PATH", "SG161222/Realistic_Vision_V6.0_B1_noVAE")
vae_id = os.environ.get("SD_VAE_PATH", "stabilityai/sd-vae-ft-mse")


print("Loading Realistic Vision model...")


vae = AutoencoderKL.from_pretrained(
    vae_id,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
)


pipe = StableDiffusionPipeline.from_pretrained(
    model_id,
    vae=vae,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    safety_checker=None,
    feature_extractor=None
)

pipe = pipe.to(device)

#if device == "cuda":
    #pipe.enable_xformers_memory_efficient_attention()


# Better scheduler for CPU
pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config,
    final_sigmas_type="sigma_min"
)


# CPU memory optimization
pipe.enable_attention_slicing()


print("Model loaded successfully!")


def generate_face(prompt):

    negative_prompt = (
        "blurry, low quality, bad quality, "
        "deformed face, distorted face, "
        "bad anatomy, extra eyes, extra nose, "
        "extra mouth, duplicate face, "
        "cartoon, painting, anime, "
        "watermark, text"
    )


    with torch.no_grad():

        image = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,

            # Reduce for CPU speed
            num_inference_steps=25,

            guidance_scale=7.5,

            # CPU friendly size
            width=512,
            height=512

        ).images[0]


    output_folder = os.path.join(
        "static",
        "generated_faces"
    )

    os.makedirs(
        output_folder,
        exist_ok=True
    )


    filename = f"{uuid.uuid4().hex}.png"


    output_path = os.path.join(
        output_folder,
        filename
    )


    image.save(output_path)


    return output_path
