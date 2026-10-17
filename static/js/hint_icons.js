/* ThirdEye Forensic - professional gender-aware reference hints.
   These references are independent UI help images; they are NOT database/person images. */
const HINT_BASE = '/static/images/hints/';
const photo = (path, alt='') => `<img class="hint-photo" src="${HINT_BASE}${path}" alt="${alt}" loading="lazy">`;

const HINT_MAP = {
  "male": {
    "age": {
      "Below 18": 1,
      "18-25 years": 2,
      "26-35 years": 3,
      "36-45 years": 4,
      "46-60 years": 5,
      "Above 60": 6
    },
    "skin": {
      "Very fair": 1,
      "Fair": 1,
      "Light brown": 2,
      "Medium brown": 2,
      "Dark brown": 4,
      "Deep brown": 4,
      "Black": 4,
      "Olive": 3,
      "Tan": 3
    },
    "head": {
      "Oval face": 2,
      "Round face": 1,
      "Long face": 4,
      "Square face": 3,
      "Heart-shaped face": 2,
      "Wide face": 1,
      "Narrow face": 4
    },
    "hair": {
      "Short straight hair": 1,
      "Long straight hair": 1,
      "Curly hair": 3,
      "Wavy hair": 2,
      "Bald": 4,
      "Crew cut": 1,
      "Afro": 3
    },
    "eyebrows": {
      "Thin eyebrows": 1,
      "Thick eyebrows": 3,
      "Bushy eyebrows": 3,
      "Arched eyebrows": 4,
      "Straight eyebrows": 2
    },
    "eyes": {
      "Large eyes": 1,
      "Small eyes": 2,
      "Round eyes": 1,
      "Almond eyes": 3,
      "Narrow eyes": 2,
      "Deep-set eyes": 4
    },
    "nose": {
      "Button nose": 1,
      "Broad nose": 3,
      "Pointed nose": 2,
      "Flat nose": 4,
      "Hooked nose": 2
    },
    "lips": {
      "Thin lips": 1,
      "Full lips": 3,
      "Wide mouth": 4,
      "Small mouth": 1,
      "Pouty lips": 3
    },
    "mustach": {
      "Clean shaven": 1,
      "Stubble": 2,
      "Goatee": 3,
      "Mustache": 4,
      "Thick mustache": 4,
      "Full beard": 3
    }
  },
  "female": {
    "age": {
      "Below 18": 1,
      "18-25 years": 2,
      "26-35 years": 3,
      "36-45 years": 4,
      "46-60 years": 5,
      "Above 60": 6
    },
    "skin": {
      "Very fair": 1,
      "Fair": 1,
      "Light brown": 2,
      "Medium brown": 2,
      "Dark brown": 4,
      "Deep brown": 4,
      "Black": 4,
      "Olive": 3,
      "Tan": 3
    },
    "head": {
      "Oval face": 2,
      "Round face": 1,
      "Long face": 4,
      "Square face": 3,
      "Heart-shaped face": 2,
      "Wide face": 1,
      "Narrow face": 4
    },
    "hair": {
      "Short straight hair": 4,
      "Long straight hair": 1,
      "Curly hair": 3,
      "Wavy hair": 2,
      "Bald": 4,
      "Crew cut": 4,
      "Afro": 3
    },
    "eyebrows": {
      "Thin eyebrows": 1,
      "Thick eyebrows": 3,
      "Bushy eyebrows": 3,
      "Arched eyebrows": 4,
      "Straight eyebrows": 2
    },
    "eyes": {
      "Large eyes": 1,
      "Small eyes": 2,
      "Round eyes": 1,
      "Almond eyes": 3,
      "Narrow eyes": 2,
      "Deep-set eyes": 4
    },
    "nose": {
      "Button nose": 1,
      "Broad nose": 3,
      "Pointed nose": 2,
      "Flat nose": 4,
      "Hooked nose": 2
    },
    "lips": {
      "Thin lips": 1,
      "Full lips": 3,
      "Wide mouth": 4,
      "Small mouth": 1,
      "Pouty lips": 3
    },
    "mustach": {
      "Clean shaven": 1,
      "Stubble": 2,
      "Goatee": 3,
      "Mustache": 3,
      "Thick mustache": 3,
      "Full beard": 4
    }
  }
};

function currentHintGender() {
  const g = (typeof collected !== 'undefined' && collected.gender && collected.gender.label) ? collected.gender.label : 'Unknown';
  return g === 'Female' ? 'female' : g === 'Male' ? 'male' : 'unknown';
}

// head and hair images are named by style (e.g. head/oval.jpg), not by number.
const NAMED_HINTS = {
  head: {
    "Oval face": "oval", "Round face": "round", "Long face": "long",
    "Square face": "square", "Heart-shaped face": "heart_shaped",
    "Wide face": "wide", "Narrow face": "narrow"
  },
  hair: {
    male: {
      "Short straight hair": "short_straight", "Long straight hair": "long_straight",
      "Curly hair": "curly", "Wavy hair": "wavy", "Bald": "bald",
      "Crew cut": "crew_cut", "Afro": "afro"
    },
    female: {
      "Short straight hair": "short_straight", "Long straight hair": "long_straight",
      "Curly hair": "curly", "Wavy hair": "wavy", "Bald": "bald",
      "Crew cut": "crew_cut", "Afro": "afro"
    }
  }
};

function hintPath(key, label) {
  if (label === 'Unknown') return `neutral_${key === 'mustach' ? 'facial' : key}.jpg`;
  const gender = currentHintGender();

  if (key === 'head' || key === 'hair') {
    const table = key === 'hair' ? (NAMED_HINTS.hair[gender] || {}) : NAMED_HINTS.head;
    const name = table[label];
    if (name && gender !== 'unknown') return `${gender}/${key}/${name}.jpg`;
    return `neutral_${key}.jpg`;
  }

  const mapped = HINT_MAP[gender] && HINT_MAP[gender][key] ? HINT_MAP[gender][key][label] : null;
  if (mapped) return `${gender}/${key === 'mustach' ? 'facial' : key}/${mapped}.jpg`;
  return `neutral_${key === 'mustach' ? 'facial' : key}.jpg`;
}

function getHintIcon(key, label) {
  if (key === 'gender') {
    if (label === 'Male') return photo('male/age/2.jpg','Male reference');
    if (label === 'Female') return photo('female/age/2.jpg','Female reference');
    return photo('neutral_gender.jpg','Gender reference');
  }
  return photo(hintPath(key, label), label);
}

const REF_ICONS = {};
const UNKNOWN_ICON = '<div class="hint-unknown">?</div>';
