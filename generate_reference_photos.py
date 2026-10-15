"""
generate_reference_photos.py

Creates the gender-specific reference photos used by the sketch page
(static/images/hints/male_<step>_<option>.jpg and female_<step>_<option>.jpg)
with the same Stable Diffusion model your image_generator.py uses.

Put this file in the project root (next to app.py) and run:

    python generate_reference_photos.py                 # everything (66 photos)
    python generate_reference_photos.py --step age      # only the age photos
    python generate_reference_photos.py --gender Female --step hair
    python generate_reference_photos.py --force         # re-make existing files

Files that already exist are skipped, so you can stop and resume anytime.
On CPU each photo takes about a minute or more; a GPU is much faster.
All faces are AI-generated people, not real individuals.
Check the results and delete/replace any photo you do not like, then re-run.
"""

import argparse
import os
import re

OUT_DIR = os.path.join("static", "images", "hints")

# Same option names as FEATURE_OPTIONS in templates/sketch.html ("Unknown" has no photo).
OPTIONS = {
    "age": ["Below 18", "18-25 years", "26-35 years", "36-45 years", "46-60 years", "Above 60"],
    "head": ["Oval face", "Round face", "Long face", "Square face",
             "Heart-shaped face", "Wide face", "Narrow face"],
    "hair": ["Short straight hair", "Long straight hair", "Curly hair", "Wavy hair",
             "Bald", "Crew cut", "Afro"],
    "nose": ["Button nose", "Broad nose", "Pointed nose", "Flat nose", "Hooked nose"],
    "lips": ["Thin lips", "Full lips", "Wide mouth", "Small mouth", "Pouty lips"],
    "mustach": ["Clean shaven", "Stubble", "Goatee", "Mustache", "Thick mustache", "Full beard"],
}

# Facial hair photos are only made for Male (same as the checklist).
GENDERS = {"Male": "man", "Female": "woman"}

AGE_PHRASE = {
    "Below 18": {"Male": "15 year old teenage boy", "Female": "15 year old teenage girl"},
    "18-25 years": {"Male": "22 year old young man", "Female": "22 year old young woman"},
    "26-35 years": {"Male": "30 year old man", "Female": "30 year old woman"},
    "36-45 years": {"Male": "40 year old man, slight wrinkles", "Female": "40 year old woman, slight wrinkles"},
    "46-60 years": {"Male": "53 year old man, wrinkles, some grey hair",
                    "Female": "53 year old woman, wrinkles, some grey hair"},
    "Above 60": {"Male": "68 year old elderly man, deep wrinkles, grey hair",
                 "Female": "68 year old elderly woman, deep wrinkles, grey hair"},
}

BASE = "Photorealistic front facing passport style portrait, neutral expression, white background, natural skin texture, sharp focus"


def slug(label):
    # Must match the slug() logic in static/js/hint_icons.js
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def filename(gender, step, label):
    return f"{gender.lower()}_{step}_{slug(label)}.jpg"


def build_prompt(gender, step, label):
    noun = GENDERS[gender]
    if step == "age":
        return f"{BASE}, {AGE_PHRASE[label][gender]}"
    if step == "head":
        return f"{BASE}, adult {noun}, {label.lower()}, clean background"
    if step == "hair":
        if label == "Bald":
            return f"{BASE}, adult {noun}, completely bald head, no hair"
        return f"{BASE}, adult {noun}, {label.lower()}, hairstyle clearly visible"
    if step == "nose":
        return f"Photorealistic close-up portrait of the nose and eyes area of an adult {noun}, {label.lower()}, neutral expression, natural skin texture"
    if step == "lips":
        return f"Photorealistic close-up of the lower face of an adult {noun}, {label.lower()}, neutral expression, natural skin texture"
    if step == "mustach":
        return f"Photorealistic close-up of the lower face of an adult {noun}, {label.lower()}, natural skin texture"
    raise ValueError(step)


def plan(gender_filter=None, step_filter=None):
    items = []
    for gender in GENDERS:
        if gender_filter and gender != gender_filter:
            continue
        for step, labels in OPTIONS.items():
            if step_filter and step != step_filter:
                continue
            if step == "mustach" and gender == "Female":
                continue
            for label in labels:
                items.append((gender, step, label))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gender", choices=list(GENDERS))
    ap.add_argument("--step", choices=list(OPTIONS))
    ap.add_argument("--force", action="store_true", help="re-generate files that already exist")
    ap.add_argument("--size", type=int, default=256, help="saved image size in px (default 256)")
    ap.add_argument("--inference-steps", type=int, default=25)
    args = ap.parse_args()

    items = plan(args.gender, args.step)
    todo = [it for it in items
            if args.force or not os.path.exists(os.path.join(OUT_DIR, filename(*it)))]
    print(f"{len(items)} photos planned, {len(todo)} to generate.")
    if not todo:
        return

    import torch
    from diffusers import AutoencoderKL, DPMSolverMultistepScheduler, StableDiffusionPipeline

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    model_id = os.environ.get("SD_MODEL_PATH", "SG161222/Realistic_Vision_V6.0_B1_noVAE")
    vae_id = os.environ.get("SD_VAE_PATH", "stabilityai/sd-vae-ft-mse")
    print(f"Running on {device}; loading model...")

    vae = AutoencoderKL.from_pretrained(vae_id, torch_dtype=dtype)
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id, vae=vae, torch_dtype=dtype, safety_checker=None, feature_extractor=None
    ).to(device)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(
        pipe.scheduler.config, final_sigmas_type="sigma_min"
    )
    pipe.enable_attention_slicing()

    negative = ("blurry, low quality, deformed face, distorted face, bad anatomy, extra eyes, "
                "duplicate face, cartoon, painting, anime, watermark, text, sunglasses, hat")

    os.makedirs(OUT_DIR, exist_ok=True)
    for n, (gender, step, label) in enumerate(todo, 1):
        name = filename(gender, step, label)
        prompt = build_prompt(gender, step, label)
        print(f"[{n}/{len(todo)}] {name}")
        gen = torch.Generator(device="cpu").manual_seed(1000 + n)
        with torch.no_grad():
            img = pipe(prompt=prompt, negative_prompt=negative,
                       num_inference_steps=args.inference_steps, guidance_scale=7.5,
                       width=512, height=512, generator=gen).images[0]
        img = img.convert("RGB").resize((args.size, args.size))
        img.save(os.path.join(OUT_DIR, name), quality=90)

    print("Done. Restart the app and hard-refresh the browser (Ctrl+Shift+R).")


if __name__ == "__main__":
    main()
