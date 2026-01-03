FOLLOWUP_QUESTIONS = {
    "emotion_direction": {
        "question": "Are you leaning toward something soothing or something intense?",
        "variants": [
            "What vibe are you in the mood for? gentle and comforting or bold and intense?",
            "Would you like a cozy, easy-going watch or something with higher stakes?",
            "Prefer something soft and reassuring, or something gripping and powerful?"
        ],
        "options": ["comforting", "intense"],
        "mapping": {
            "comforting": "comforting",
            "intense": "intense"
        }
    },
    "cognitive_load": {
        "question": "Do you feel like switching off and escaping, or engaging with something more reflective?",
        "variants": [
            "Are you after an escapist unwind or a thoughtful, reflective watch?",
            "Would you prefer a light, switch-off experience or something to chew on?",
            "Should we go breezy and fun, or more contemplative and layered?"
        ],
        "options": ["escapist", "thoughtful"],
        "mapping": {
            "escapist": "escapist",
            "thoughtful": "thoughtful"
        }
    },
    "desired_outcome": {
        "question": "Would you like a pick‑me‑up, something reflective, or a rush?",
        "variants": [
            "What would you like the film to do—lift your spirits, help process feelings, or get your adrenaline going?",
            "Are you looking to feel better, think things through, or get excited?",
            "Should the movie cheer you up, give room to reflect, or energize you?"
        ],
        "options": ["feel better", "process feelings", "get excited"],
        "mapping": {
            "feel better": "feel_better",
            "process feelings": "process_feelings",
            "get excited": "get_excited"
        }
    },
    "era_preference": {
        "question": "Do you have a soft spot for older classics or prefer more contemporary releases?",
        "variants": [
            "Should we lean classic or go modern?",
            "Would you like something vintage or more recent?",
            "In the mood for a classic era or a contemporary one?"
        ],
        "options": ["classic", "modern"],
        "mapping": {
            "classic": "classic",
            "modern": "modern"
        }
    },
    "content_sensitivity": {
        "question": "Anything you'd like me to steer clear of?",
        "variants": [
            "Let me know if you'd rather avoid horror, heavy themes, or on‑screen violence.",
            "Any content you'd prefer not to see (e.g., horror, heavy drama, violence)?",
            "Tell me if there are topics or tones you'd like me to avoid."
        ],
        "options": ["avoid horror", "avoid heavy drama", "avoid violence", "no preference"],
        "mapping": {
            "avoid horror": "avoid_horror",
            "avoid heavy drama": "avoid_drama",
            "avoid violence": "avoid_violence",
            "no preference": "none"
        }
    },
    # Adaptive pools based on emotion_direction
    "intensity_style": {
        "question": "For a punchier vibe, are you drawn more to high‑octane excitement, edge‑of‑your‑seat tension, or moody‑dark tones?",
        "variants": [
            "If we go intense, should it be adrenaline, suspense, or moody and dark?",
            "Thinking intense: more explosive action, taut suspense, or darker ambience?",
            "For an intense feel, do you prefer high energy, tight tension, or darker edges?"
        ],
        "options": ["adrenaline", "suspense", "dark"],
        "mapping": {
            "adrenaline": "adrenaline",
            "suspense": "suspense",
            "dark": "dark"
        }
    },
    "comfort_style": {
        "question": "For a gentle vibe, do you prefer feel‑good and uplifting, warm and heartwarming, or calm and soothing?",
        "variants": [
            "If we keep it comforting, should it be uplifting, heartwarming, or calm?",
            "A softer tone: more feel‑good, warmly sentimental, or quietly soothing?",
            "For comfort, are you leaning toward uplifting, heartwarming, or calm?"
        ],
        "options": ["uplifting", "heartwarming", "calm"],
        "mapping": {
            "uplifting": "uplifting",
            "heartwarming": "heartwarming",
            "calm": "calm"
        }
    },
    "pace_preference": {
        "question": "Do you want something brisk and energetic or slow and contemplative?",
        "variants": [
            "Should the pace be fast and lively or slow‑burn and reflective?",
            "Are you up for a quick tempo or a steady, unhurried flow?",
            "Prefer a zippier pace or a patient slow burn?"
        ],
        "options": ["fast", "slow", "no preference"],
        "mapping": {
            "fast": "fast",
            "slow": "slow",
            "no preference": "none"
        }
    },
    "violence_tolerance": {
        "question": "How comfortable are you with on‑screen violence?",
        "variants": [
            "Should we avoid violence entirely, keep it mild, or is strong okay?",
            "Violence level—none, mild, or strong?",
            "Do you prefer to avoid violence, tolerate a little, or not mind it?"
        ],
        "options": ["none", "mild", "strong"],
        "mapping": {
            "none": "none",
            "mild": "mild",
            "strong": "strong"
        }
    },
    "usual_preference": {
        "question": "What do you usually enjoy—family‑friendly, action‑packed, or thoughtful drama?",
        "variants": [
            "Do you tend toward family‑friendly, action‑packed, or more thoughtful movies?",
            "Your baseline taste: cozy family picks, explosive action, or layered drama?",
            "Would you describe your usual picks as family‑friendly, action‑packed, or thoughtful?"
        ],
        "options": ["family‑friendly", "action‑packed", "thoughtful"],
        "mapping": {
            "family‑friendly": "family_friendly",
            "action‑packed": "action_packed",
            "thoughtful": "thoughtful"
        }
    },
    "music_tone": {
        "question": "For the film’s musical feel, do you prefer uplifting, somber, or intense?",
        "variants": [
            "Score tone: uplifting/feel‑good, somber, or intense?",
            "Do you enjoy an uplifting score, something somber, or something more intense?",
            "Music vibe—uplifting, somber, or intense?"
        ],
        "options": ["uplifting", "somber", "intense"],
        "mapping": {
            "uplifting": "uplifting",
            "somber": "somber",
            "intense": "intense"
        }
    }
}
