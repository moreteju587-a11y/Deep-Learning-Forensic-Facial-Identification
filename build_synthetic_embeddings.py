"""
build_synthetic_embeddings.py

Same idea as your existing create_embeddings.py, but:
  - points at the synthetic_database/ folder + synthetic_database.csv
    produced by generate_synthetic_database.py
  - carries the ground-truth feature columns (head, hair, eyes, etc.)
    through into the .pkl, so match_face.py's results can later be checked
    against known features, not just a raw similarity score.

Usage:
    python build_synthetic_embeddings.py \
        --folder synthetic_database \
        --csv synthetic_database.csv \
        --out synthetic_embeddings.pkl

After this runs, point match_face.py at the new pkl file (just change the
filename it opens) to match against the synthetic database instead of the
original criminal_embeddings.pkl.
"""

import argparse
import os
import pickle

import cv2
import pandas as pd
import insightface


FEATURE_COLUMNS = [
    "gender", "skin", "head", "hair", "eyebrows", "eyes", "nose", "lips", "mustach",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, default="synthetic_database")
    parser.add_argument("--csv", type=str, default="synthetic_database.csv")
    parser.add_argument("--out", type=str, default="synthetic_embeddings.pkl")
    args = parser.parse_args()

    app = insightface.app.FaceAnalysis(name="buffalo_l")
    app.prepare(ctx_id=-1, det_size=(640, 640))  # ctx_id=-1 -> CPU

    info = pd.read_csv(args.csv)
    embeddings = []
    skipped = 0

    for _, row in info.iterrows():
        image_path = os.path.join(args.folder, row["image"])
        image = cv2.imread(image_path)

        if image is None:
            print(f"Cannot read {row['image']}")
            skipped += 1
            continue

        faces = app.get(image)
        if len(faces) == 0:
            print(f"No face detected in {row['image']}")
            skipped += 1
            continue

        entry = {
            "image": row["image"],
            "name": row["name"],
            "age": row["age"],
            "crime": row["crime"],
            "last_seen": row["last_seen"],
            "embedding": faces[0].embedding,
        }
        # carry ground-truth features through for later validation
        for col in FEATURE_COLUMNS:
            if col in row:
                entry[col] = row[col]

        embeddings.append(entry)

    print(f"Processed {len(embeddings)} faces, skipped {skipped}.")

    with open(args.out, "wb") as f:
        pickle.dump(embeddings, f)

    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
