# Gender photo checklist

Put every photo in: `static/images/hints/` (same folder as face_1.jpg, hair_1.jpg ...)
File names must match exactly (lowercase, `.jpg`). Square photos around 256x256 px work best.
Any file you skip simply falls back to the existing photo, so you can add them gradually.

## Male

| Step | Option shown on screen | File name to add |
|---|---|---|
| age | Below 18 | `male_age_below-18.jpg` |
| age | 18-25 years | `male_age_18-25-years.jpg` |
| age | 26-35 years | `male_age_26-35-years.jpg` |
| age | 36-45 years | `male_age_36-45-years.jpg` |
| age | 46-60 years | `male_age_46-60-years.jpg` |
| age | Above 60 | `male_age_above-60.jpg` |
| head | Oval face | `male_head_oval-face.jpg` |
| head | Round face | `male_head_round-face.jpg` |
| head | Long face | `male_head_long-face.jpg` |
| head | Square face | `male_head_square-face.jpg` |
| head | Heart-shaped face | `male_head_heart-shaped-face.jpg` |
| head | Wide face | `male_head_wide-face.jpg` |
| head | Narrow face | `male_head_narrow-face.jpg` |
| hair | Short straight hair | `male_hair_short-straight-hair.jpg` |
| hair | Long straight hair | `male_hair_long-straight-hair.jpg` |
| hair | Curly hair | `male_hair_curly-hair.jpg` |
| hair | Wavy hair | `male_hair_wavy-hair.jpg` |
| hair | Bald | `male_hair_bald.jpg` |
| hair | Crew cut | `male_hair_crew-cut.jpg` |
| hair | Afro | `male_hair_afro.jpg` |
| nose | Button nose | `male_nose_button-nose.jpg` |
| nose | Broad nose | `male_nose_broad-nose.jpg` |
| nose | Pointed nose | `male_nose_pointed-nose.jpg` |
| nose | Flat nose | `male_nose_flat-nose.jpg` |
| nose | Hooked nose | `male_nose_hooked-nose.jpg` |
| lips | Thin lips | `male_lips_thin-lips.jpg` |
| lips | Full lips | `male_lips_full-lips.jpg` |
| lips | Wide mouth | `male_lips_wide-mouth.jpg` |
| lips | Small mouth | `male_lips_small-mouth.jpg` |
| lips | Pouty lips | `male_lips_pouty-lips.jpg` |
| mustach | Clean shaven | `male_mustach_clean-shaven.jpg` |
| mustach | Stubble | `male_mustach_stubble.jpg` |
| mustach | Goatee | `male_mustach_goatee.jpg` |
| mustach | Mustache | `male_mustach_mustache.jpg` |
| mustach | Thick mustache | `male_mustach_thick-mustache.jpg` |
| mustach | Full beard | `male_mustach_full-beard.jpg` |

## Female

| Step | Option shown on screen | File name to add |
|---|---|---|
| age | Below 18 | `female_age_below-18.jpg` |
| age | 18-25 years | `female_age_18-25-years.jpg` |
| age | 26-35 years | `female_age_26-35-years.jpg` |
| age | 36-45 years | `female_age_36-45-years.jpg` |
| age | 46-60 years | `female_age_46-60-years.jpg` |
| age | Above 60 | `female_age_above-60.jpg` |
| head | Oval face | `female_head_oval-face.jpg` |
| head | Round face | `female_head_round-face.jpg` |
| head | Long face | `female_head_long-face.jpg` |
| head | Square face | `female_head_square-face.jpg` |
| head | Heart-shaped face | `female_head_heart-shaped-face.jpg` |
| head | Wide face | `female_head_wide-face.jpg` |
| head | Narrow face | `female_head_narrow-face.jpg` |
| hair | Short straight hair | `female_hair_short-straight-hair.jpg` |
| hair | Long straight hair | `female_hair_long-straight-hair.jpg` |
| hair | Curly hair | `female_hair_curly-hair.jpg` |
| hair | Wavy hair | `female_hair_wavy-hair.jpg` |
| hair | Bald | `female_hair_bald.jpg` |
| hair | Crew cut | `female_hair_crew-cut.jpg` |
| hair | Afro | `female_hair_afro.jpg` |
| nose | Button nose | `female_nose_button-nose.jpg` |
| nose | Broad nose | `female_nose_broad-nose.jpg` |
| nose | Pointed nose | `female_nose_pointed-nose.jpg` |
| nose | Flat nose | `female_nose_flat-nose.jpg` |
| nose | Hooked nose | `female_nose_hooked-nose.jpg` |
| lips | Thin lips | `female_lips_thin-lips.jpg` |
| lips | Full lips | `female_lips_full-lips.jpg` |
| lips | Wide mouth | `female_lips_wide-mouth.jpg` |
| lips | Small mouth | `female_lips_small-mouth.jpg` |
| lips | Pouty lips | `female_lips_pouty-lips.jpg` |

## After adding the photos

1. Restart the app (`python app.py`) and hard-refresh the browser (Ctrl+Shift+R) so the old JS is not cached.
2. Pick Male or Female in step 1; every later step then shows only that gender's photos.
3. When Female is chosen, the Facial Hair step is skipped automatically (saved as "Clean shaven").
