"""
generate_synthetic_database.py

Builds a synthetic "criminal database" using the SAME Stable Diffusion
pipeline and the SAME feature vocabulary your app's sketch builder uses
(copied from FEATURE_OPTIONS in templates/sketch.html).

Why: your /generate-face route produces SD-generated portraits, but your
existing criminal_database/ contains real photographed faces (CelebA-style).
That domain mismatch hurts InsightFace matching. This script instead builds
a database of SD-generated portraits, tagged with their exact ground-truth
features, so generated queries and database entries come from the same
distribution and you can validate matches against known features.

Usage:
    python generate_synthetic_database.py --count 300 --out synthetic_database

Output:
    synthetic_database/000001.png ... 
    synthetic_database.csv   (image, name, age, crime, last_seen, gender,
                               skin, head, hair, eyebrows, eyes, nose, lips, mustach)

NOTE: This runs Stable Diffusion on CPU (same as your image_generator.py),
so each image takes on the order of a minute or more. Start with a small
--count (e.g. 20-50) to test before generating hundreds.
"""

import argparse
import csv
import os
import random

import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
import pandas as pd


# ---------------------------------------------------------------------------
# 1. Same feature vocabulary as templates/sketch.html FEATURE_OPTIONS
#    ("Unknown" is dropped here since we want concrete ground truth for
#    every database entry, not "Skipped"/"Unknown" placeholders).
# ---------------------------------------------------------------------------
FEATURE_OPTIONS = {
    "gender": ["Male", "Female"],
    "skin": [
        "Very fair", "Fair", "Light brown", "Medium brown",
        "Dark brown", "Deep brown", "Black", "Olive", "Tan",
    ],
    "head": [
        "Oval face", "Round face", "Long face", "Square face",
        "Heart-shaped face", "Wide face", "Narrow face",
    ],
    "hair": [
        "Short straight hair", "Long straight hair", "Curly hair",
        "Wavy hair", "Bald", "Crew cut", "Afro",
    ],
    "eyebrows": [
        "Thin eyebrows", "Thick eyebrows", "Bushy eyebrows",
        "Arched eyebrows", "Straight eyebrows",
    ],
    "eyes": [
        "Large eyes", "Small eyes", "Round eyes", "Almond eyes",
        "Narrow eyes", "Deep-set eyes",
    ],
    "nose": [
        "Button nose", "Broad nose", "Pointed nose", "Flat nose", "Hooked nose",
    ],
    "lips": [
        "Thin lips", "Full lips", "Wide mouth", "Small mouth", "Pouty lips",
    ],
    "mustach": [
        "Clean shaven", "Stubble", "Goatee", "Mustache",
        "Thick mustache", "Full beard",
    ],
}

# Fake identity fields (purely synthetic labels, mirrors what your
# create_csv.py / criminal_database_3000.csv already contain)
FIRST_NAMES = ["Rahul", "Arjun", "Nikhil", "Prakash", "Suresh", "Vikram",
               "Ananya", "Priya", "Kavya", "Sneha", "Divya", "Meera"]
LAST_NAMES = ["Sharma", "Patel", "Yadav", "Reddy", "Kumar", "Gowda", "Nair"]
CRIMES = ["Burglary", "Fraud", "Smuggling", "Forgery", "Theft", "Assault"]
CITIES = ["Hubli", "Belagavi", "Tumakuru", "Dharwad", "Mysuru", "Mangaluru"]


def build_prompt(features: dict) -> str:
    """Mirrors app.py's build_face_prompt(), but also includes skin tone."""
    gender = features.get("gender", "person")

    mapping = {
        "skin": "{} skin tone",
        "head": "{} face shape",
        "hair": "{} hairstyle",
        "eyebrows": "{} eyebrows",
        "eyes": "{} eyes",
        "nose": "{} nose",
        "lips": "{} lips",
        "mustach": "{} facial hair",
    }

    parts = []
    for key, template in mapping.items():
        value = features.get(key)
        if value:
            parts.append(template.format(value))

    description = ", ".join(parts)

    return f"""
Ultra realistic forensic police portrait of a {gender}.

Features:
{description}

Front facing.
Neutral facial expression.
Natural skin texture.
Professional DSLR portrait.
Passport style.
White background.
Highly detailed.
"""


def random_features() -> dict:
    return {key: random.choice(values) for key, values in FEATURE_OPTIONS.items()}


def random_identity(gender: str) -> dict:
    if gender == "Male":
        first_names = ["Rahul", "Arjun", "Nikhil", "Prakash", "Suresh", "Vikram"]
    else:
        first_names = ["Ananya", "Priya", "Kavya", "Sneha", "Divya", "Meera"]

    return {
        "name": f"{random.choice(first_names)} {random.choice(LAST_NAMES)}",
        "age": random.randint(18, 65),
        "crime": random.choice(CRIMES),
        "last_seen": random.choice(CITIES),
    }


def load_pipeline(device: str, use_xformers: bool = False):
    model_id = "SG161222/Realistic_Vision_V6.0_B1_noVAE"

    use_fp16 = device == "cuda"
    print(f"Loading Realistic Vision model on {device} "
          f"({'float16' if use_fp16 else 'float32'})...")

    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16 if use_fp16 else torch.float32,
        safety_checker=None,
        feature_extractor=None,
    )
    pipe = pipe.to(device)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config,
    final_sigmas_type="sigma_min"
)

    # Memory-saving options - matter most on a 4-6GB laptop GPU
    pipe.enable_attention_slicing()
    pipe.enable_vae_slicing()
    if device == "cuda" and use_xformers:
        try:
            pipe.enable_xformers_memory_efficient_attention()
            print("xformers memory-efficient attention enabled.")
        except Exception as e:
            print(f"xformers not available ({e}), continuing without it.")

    print("Model loaded.")
    return pipe


NEGATIVE_PROMPT = (
    "blurry, low quality, bad quality, "
    "deformed face, distorted face, "
    "bad anatomy, extra eyes, extra nose, "
    "extra mouth, duplicate face, "
    "cartoon, painting, anime, "
    "watermark, text"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50,
                         help="Number of database entries to generate")
    parser.add_argument("--out", type=str, default="synthetic_database",
                         help="Output folder for images")
    parser.add_argument("--csv", type=str, default="synthetic_database.csv",
                         help="Output CSV path")
    parser.add_argument("--steps", type=int, default=25,
                         help="Inference steps (lower = faster, less detail)")
    parser.add_argument("--seed", type=int, default=None,
                         help="Optional random seed for reproducibility")
    parser.add_argument("--device", type=str, default=None,
                         choices=["cuda", "cpu"],
                         help="Force a device. Default: auto-detect GPU if available.")
    parser.add_argument("--append", action="store_true",
                         help="Add new images on top of an existing dataset instead "
                              "of overwriting it. Continues numbering after the "
                              "highest existing image index and appends to the CSV.")
    parser.add_argument("--xformers", action="store_true",
                         help="Try to enable xformers memory-efficient attention. "
                              "OFF by default - on Windows this can silently crash "
                              "if your xformers build doesn't match your torch/CUDA "
                              "version. Only add this flag if you've confirmed it "
                              "works, or want to test it.")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    os.makedirs(args.out, exist_ok=True)
    pipe = load_pipeline(device, use_xformers=args.xformers)

    fieldnames = [
        "image", "name", "age", "crime", "last_seen",
        "gender", "skin", "head", "hair", "eyebrows",
        "eyes", "nose", "lips", "mustach",
    ]

    # Work out where to start numbering and whether to write a fresh header
    start_index = 1
    write_header = True
    file_mode = "w"

    if args.append and os.path.exists(args.csv):
        existing = pd.read_csv(args.csv)
        if len(existing) > 0:
            # existing "image" values look like 000123.png -> pull the number out
            existing_nums = (
                existing["image"]
                .str.extract(r"(\d+)")[0]
                .astype(int)
            )
            start_index = int(existing_nums.max()) + 1
        write_header = False
        file_mode = "a"
        print(f"Appending: starting new images at {start_index:06d}.png, "
              f"existing CSV has {len(existing)} rows.")
    elif args.append:
        print("--append set but no existing CSV found, starting fresh at 000001.")

    end_index = start_index + args.count - 1

    with open(args.csv, file_mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        for i in range(start_index, end_index + 1):
            n = i - start_index + 1
            features = random_features()
            identity = random_identity(features["gender"])
            prompt = build_prompt(features)

            print(f"[{n}/{args.count}] (index {i:06d}) "
                  f"Generating with features: {features}")

            with torch.no_grad():
                image = pipe(
                    prompt=prompt,
                    negative_prompt=NEGATIVE_PROMPT,
                    num_inference_steps=args.steps,
                    guidance_scale=7.5,
                    width=512,
                    height=512,
                ).images[0]

            filename = f"{i:06d}.png"
            image.save(os.path.join(args.out, filename))

            row = {"image": filename, **identity, **features}
            writer.writerow(row)

            if device == "cuda":
                torch.cuda.empty_cache()

    print(f"\nDone. {args.count} images in '{args.out}/', metadata in '{args.csv}'.")


if __name__ == "__main__":
    main()




