import os
import pickle
import cv2
import pandas as pd
import insightface

# Load InsightFace model
app = insightface.app.FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=1, det_size=(640, 640))

database_folder = "criminal_database"

# Read criminal information
criminal_info = pd.read_csv("criminal_database.csv")

embeddings = []

for image_name in os.listdir(database_folder):

    image_path = os.path.join(database_folder, image_name)

    image = cv2.imread(image_path)

    if image is None:
        print("Cannot read:", image_name)
        continue

    faces = app.get(image)

    if len(faces) == 0:
        print("No face:", image_name)
        continue

    # Find the matching row in the CSV
    row = criminal_info[criminal_info["image"] == image_name]

    if row.empty:
        print("Not found in CSV:", image_name)
        continue

    row = row.iloc[0]

    embeddings.append({
        "image": image_name,
        "embedding": faces[0].embedding,
        "name": row["name"],
        "age": row["age"],
        "crime": row["crime"],
        "last_seen": row["last_seen"]
    })

    print("Added:", image_name)

# Save embeddings
with open("criminal_embeddings.pkl", "wb") as f:
    pickle.dump(embeddings, f)

print(f"\nSaved {len(embeddings)} embeddings to criminal_embeddings.pkl")