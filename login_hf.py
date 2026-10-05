from huggingface_hub import login
import os

token = os.getenv("HF_TOKEN")

if token:
    login(token)
else:
    print("HF_TOKEN not set. Skipping Hugging Face login.")
