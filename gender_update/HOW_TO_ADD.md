# How to add this to your project

Your project folder (where app.py is) should end up like this:

    your-project/
      app.py
      generate_reference_photos.py        <- NEW (copy here)
      templates/
        sketch.html                       <- REPLACE
      static/
        js/
          hint_icons.js                   <- REPLACE
        images/
          hints/
            face_1.jpg ... (existing)
            male_age_below-18.jpg         <- NEW photos (see gender_photo_checklist.md)
            female_age_below-18.jpg
            ...

## Steps
1. Unzip this folder over your project root. Say yes to replace `sketch.html` and `hint_icons.js`.
2. Photos (choose one):
   a) Your own photos: save each as the exact filename in `gender_photo_checklist.md`
      into `static/images/hints/` (square, about 256x256 px, .jpg).
   b) Generate them once with your Stable Diffusion setup:
        python generate_reference_photos.py --step age     (try the age photos first)
        python generate_reference_photos.py                (all 66 photos)
      Photos are saved as files, so they are the same every time. Delete one you dislike and run again to remake it.
3. Restart the app: `python app.py`, then hard-refresh the browser (Ctrl+Shift+R).

## What you will see
- Pick **Male**: age, head shape, hair, nose, lips and facial hair show male photos only.
- Pick **Female**: the same steps show female photos only, and Facial Hair is skipped automatically.
- Each age/option shows its own photo from your files. If a file is missing, a photo of the same gender is shown instead.
