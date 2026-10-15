/* ThirdEye Forensic - realistic photographic reference thumbnails */
const HINT_BASE = '/static/images/hints/';
const photo = (name, alt='') => `<img class="hint-photo" src="${HINT_BASE}${name}" alt="${alt}" loading="lazy">`;

const REF_ICONS = {
  gender: {
    "Male": photo('face_2.jpg?v=2','Male reference'),
    "Female": photo('face_1.jpg?v=2','Female reference'),
    "Unknown": photo('face_4.jpg?v=2','Neutral face reference')
  },
  age: {
    "Below 18": photo('face_1.jpg?v=2','Young face reference'),
    "18-25 years": photo('face_1.jpg?v=2','Young adult face reference'),
    "26-35 years": photo('face_2.jpg?v=2','Adult face reference'),
    "36-45 years": photo('face_3.jpg','Adult face reference'),
    "46-60 years": photo('face_4.jpg?v=2','Mature face reference'),
    "Above 60": photo('face_4.jpg?v=2','Older face reference'),
    "Unknown": photo('face_3.jpg','Neutral age reference')
  },
  skin: {
    "Very fair": photo('skin_1.jpg','Very fair skin'),
    "Fair": photo('skin_2.jpg','Fair skin'),
    "Light brown": photo('skin_2.jpg','Light brown skin'),
    "Medium brown": photo('skin_3.jpg','Medium brown skin'),
    "Dark brown": photo('skin_4.jpg','Dark brown skin'),
    "Deep brown": photo('skin_4.jpg','Deep brown skin'),
    "Black": photo('skin_4.jpg','Dark skin'),
    "Olive": photo('skin_3.jpg','Olive skin'),
    "Tan": photo('skin_3.jpg','Tan skin'),
    "Unknown": photo('skin_2.jpg','Neutral skin reference')
  },
  head: {
    "Oval face": photo('face_1.jpg?v=2','Oval face'),
    "Round face": photo('face_2.jpg?v=2','Round face'),
    "Long face": photo('face_3.jpg','Long face'),
    "Square face": photo('face_4.jpg?v=2','Square face'),
    "Heart-shaped face": photo('face_1.jpg?v=2','Heart shaped face'),
    "Wide face": photo('face_4.jpg?v=2','Wide face'),
    "Narrow face": photo('face_3.jpg','Narrow face'),
    "Unknown": photo('face_2.jpg?v=2','Neutral face shape reference')
  },
  hair: {
    "Short straight hair": photo('hair_4.jpg','Short straight hair'),
    "Long straight hair": photo('hair_1.jpg','Long straight hair'),
    "Curly hair": photo('hair_3.jpg','Curly hair'),
    "Wavy hair": photo('hair_2.jpg','Wavy hair'),
    "Bald": photo('hair_4.jpg','Short hair reference'),
    "Crew cut": photo('hair_4.jpg','Crew cut reference'),
    "Afro": photo('hair_3.jpg','Curly hair reference'),
    "Unknown": photo('hair_1.jpg','Neutral hair reference')
  },
  eyebrows: {
    "Thin eyebrows": photo('eyes_1.jpg','Thin eyebrows reference'),
    "Thick eyebrows": photo('eyes_2.jpg','Thick eyebrows reference'),
    "Bushy eyebrows": photo('eyes_3.jpg','Bushy eyebrows reference'),
    "Arched eyebrows": photo('eyes_4.jpg','Arched eyebrows reference'),
    "Straight eyebrows": photo('eyes_2.jpg','Straight eyebrows reference'),
    "Unknown": photo('eyes_1.jpg','Neutral eyebrow reference')
  },
  eyes: {
    "Large eyes": photo('eyes_1.jpg','Large eyes'),
    "Small eyes": photo('eyes_2.jpg','Small eyes'),
    "Round eyes": photo('eyes_3.jpg','Round eyes'),
    "Almond eyes": photo('eyes_1.jpg','Almond eyes'),
    "Narrow eyes": photo('eyes_2.jpg','Narrow eyes'),
    "Deep-set eyes": photo('eyes_4.jpg','Deep set eyes'),
    "Unknown": photo('eyes_3.jpg','Neutral eye reference')
  },
  nose: {
    "Button nose": photo('facial_1.jpg','Button nose reference'),
    "Broad nose": photo('facial_2.jpg','Broad nose reference'),
    "Pointed nose": photo('facial_1.jpg','Pointed nose reference'),
    "Flat nose": photo('facial_2.jpg','Flat nose reference'),
    "Hooked nose": photo('facial_3.jpg','Hooked nose reference'),
    "Unknown": photo('facial_1.jpg','Neutral nose reference')
  },
  lips: {
    "Thin lips": photo('facial_1.jpg','Thin lips reference'),
    "Full lips": photo('facial_3.jpg','Full lips reference'),
    "Wide mouth": photo('facial_2.jpg','Wide mouth reference'),
    "Small mouth": photo('facial_1.jpg','Small mouth reference'),
    "Pouty lips": photo('facial_3.jpg','Pouty lips reference'),
    "Unknown": photo('facial_1.jpg','Neutral lip reference')
  },
  mustach: {
    "Clean shaven": photo('facial_1.jpg','Clean shaven'),
    "Stubble": photo('facial_2.jpg','Stubble'),
    "Goatee": photo('facial_2.jpg','Goatee'),
    "Mustache": photo('facial_2.jpg','Mustache'),
    "Thick mustache": photo('facial_2.jpg','Thick mustache'),
    "Full beard": photo('facial_3.jpg','Full beard'),
    "Unknown": photo('facial_1.jpg','Neutral facial hair reference')
  }
};
const UNKNOWN_ICON = '<div class="hint-unknown">?</div>';

// ─── Gender-aware references ─────────────────────────────────────────────────
// Once the suspect's gender is chosen (Male / Female), every remaining step that
// shows a face or facial feature uses ONLY that gender's photos.
//
// Photos are plain files you add to static/images/hints/ (made once, never random):
//   male_<step>_<option>.jpg      e.g. male_age_26-35-years.jpg
//   female_<step>_<option>.jpg    e.g. female_hair_curly-hair.jpg
// (the exact names are in gender_photo_checklist.md)
//
// If one of those files is missing, a built-in photo of the SAME gender is shown,
// never a photo of the other gender.
const GENDERED_KEYS = ['age', 'head', 'hair', 'nose', 'lips', 'mustach'];

const SAFE_FALLBACK = {
  Male: {
    age:     ['face_2.jpg?v=2'],
    head:    ['face_2.jpg?v=2'],
    hair:    ['hair_4.jpg', 'hair_3.jpg'],
    nose:    ['facial_1.jpg'],
    lips:    ['facial_1.jpg'],
    mustach: null                      // existing facial_*.jpg photos are already male
  },
  Female: {
    age:     ['face_1.jpg?v=2', 'face_3.jpg', 'face_4.jpg'],
    head:    ['face_1.jpg?v=2', 'face_3.jpg', 'face_4.jpg'],
    hair:    ['hair_1.jpg', 'hair_2.jpg', 'hair_3.jpg'],
    nose:    ['face_1.jpg?v=2'],
    lips:    ['face_1.jpg?v=2'],
    mustach: null                      // step is skipped for Female (see sketch.html)
  }
};

function refIcon(key, label, gender) {
  const set = REF_ICONS[key] || {};
  const base = set[label];
  if (!base) return null;
  if (gender !== 'Male' && gender !== 'Female') return base;
  if (!GENDERED_KEYS.includes(key)) return base;

  const slug = label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  let fallback = (base.match(/src="([^"]+)"/) || [])[1];
  const safe = SAFE_FALLBACK[gender][key];
  if (safe) fallback = HINT_BASE + safe[Object.keys(set).indexOf(label) % safe.length];

  return `<img class="hint-photo" src="${HINT_BASE}${gender.toLowerCase()}_${key}_${slug}.jpg" alt="${gender} - ${label}" loading="lazy" onerror="this.onerror=null;this.src='${fallback}'">`;
}
