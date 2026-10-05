import cv2
import pickle
import numpy as np
import insightface

# Load InsightFace model
app = insightface.app.FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=-1)

# Load criminal embeddings
with open("synthetic_embeddings.pkl", "rb") as f:
    criminal_db = pickle.load(f)

# Minimum similarity to accept a match
SIMILARITY_THRESHOLD = 50.0


def find_best_match(image_path):

    image = cv2.imread(image_path)

    if image is None:
        return None

    faces = app.get(image)

    if len(faces) == 0:
        return None

    query_embedding = faces[0].embedding

    best_match = None
    highest_similarity = -1

    for person in criminal_db:

        similarity = np.dot(query_embedding, person["embedding"]) / (
            np.linalg.norm(query_embedding)
            * np.linalg.norm(person["embedding"])
        )

        similarity = round(float(similarity * 100), 2)

        if similarity > highest_similarity:
            highest_similarity = similarity

            best_match = {
                "image": person["image"],
                "name": person["name"],
                "age": person["age"],
                "crime": person["crime"],
                "last_seen": person["last_seen"],
                "similarity": similarity
            }

    # Return only if similarity is above threshold
    if best_match:
        print("Highest Similarity:", best_match["similarity"])
        if best_match["similarity"] >= SIMILARITY_THRESHOLD:
            return best_match

    return None