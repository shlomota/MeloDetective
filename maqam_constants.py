"""
Maqam Constants Module

This module defines the constants for Middle Eastern musical modes (maqams),
including the semitone intervals for each maqam.
"""

# Define note names for reference
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Define semitone positions for each maqam (used in calculations)
MAQAM_SEMITONE_POSITIONS = {
    "ajam": [0, 2, 4, 5, 7, 9, 11],  # Major scale
    "nahawand": [0, 2, 3, 5, 7, 8, 10],  # Natural minor scale
    "rast": [0, 2, 4, 5, 7, 9, 11],  # Approximated for Western ears
    "hijaz": [0, 1, 4, 5, 7, 8, 10],  # Distinctive augmented second
    "kurd": [0, 1, 3, 5, 7, 8, 10],  # Phrygian mode
    "bayati": [0, 2, 3, 5, 7, 9, 10],  # Approximated for Western ears
    "saba": [0, 2, 3, 4, 7, 8, 10],  # Distinctive diminished fourth
    "siga": [0, 2, 4, 5, 7, 9, 11]  # Approximated for Western ears
}

# Define precise intervals with quarter tones (for display only)
MAQAM_PRECISE_INTERVALS = {
    "ajam": [0, 2, 2, 1, 2, 2, 2, 1],  # [0, 2, 4, 5, 7, 9, 11, 12]
    "rast": [0, 2, 1.5, 1.5, 2, 2, 1.5, 1.5],  # [0, 2, 3.5, 5, 7, 9, 10.5, 12]
    "nahawand": [0, 2, 1, 2, 2, 1, 2, 2],  # [0, 2, 3, 5, 7, 8, 10, 12]
    "hijaz": [0, 1, 3, 1, 2, 1, 2, 2],  # [0, 1, 4, 5, 7, 8, 10, 12]
    "kurd": [0, 1, 2, 2, 2, 1, 2, 2],  # [0, 1, 3, 5, 7, 8, 10, 12]
    "bayati": [0, 1.5, 1.5, 2, 2, 2, 1.5, 1.5],  # [0, 1.5, 3, 5, 7, 9, 10.5, 12]
    "saba": [0, 1.5, 1.5, 1, 3, 1, 2, 2],  # [0, 1.5, 3, 4, 7, 8, 10, 12]
    "siga": [0, 1.5, 2, 1.5, 2, 1.5, 2, 1.5]  # [0, 1.5, 3.5, 5, 7, 8.5, 10.5, 12]
}

# Define maqam descriptions
MAQAM_DESCRIPTIONS = {
    "ajam": "Ajam is a maqam that closely resembles the Western major scale. The name 'Ajam' means 'Persian' or 'non-Arab' in Arabic, reflecting its origins outside the traditional Arabic music system. Unlike many other maqams, Ajam doesn't use quarter tones, making it more accessible to musicians trained in Western music. It's characterized by its bright, straightforward sound and is often used as a foundation for learning other maqams.",
    "rast": "Rast is one of the most fundamental and common maqams in Middle Eastern music. It's similar to the Western major scale but with a neutral third (between major and minor). The name 'Rast' means 'straight' or 'direct' in Persian, reflecting its foundational role in the maqam system. It serves as a reference point for many other maqams and is often the first maqam taught to students.",
    "nahawand": "Nahawand is similar to the Western natural minor scale. It has a distinctive melancholic quality that makes it popular for emotional expressions. Named after the city of Nahavand in Iran, this maqam has spread throughout the Middle East and North Africa. It's particularly prominent in Turkish classical music where it's known as Buselik.",
    "hijaz": "Hijaz features an augmented second between the second and third degrees, giving it a distinctive Middle Eastern sound that's immediately recognizable to Western ears. Named after the Hijaz region in Saudi Arabia, this maqam is widely used across Arabic, Turkish, and Jewish music traditions. Its characteristic interval creates a tension that resolves beautifully in melodic phrases.",
    "kurd": "Kurd is similar to the Western Phrygian mode with a flattened second degree. Named after the Kurdish people, this maqam has a distinctive character created by its minor second interval at the beginning. It's widely used in Kurdish folk music but has spread throughout the Middle East and Mediterranean regions.",
    "bayati": "Bayati features a neutral second degree (between major and minor) and is one of the most common and beloved maqams in Arabic music. Its name may derive from the Arabic word 'bayt' meaning 'home,' reflecting its familiar and comfortable feeling. Bayati is often considered the 'everyday' maqam due to its prevalence in both folk and classical traditions.",
    "saba": "Saba features a diminished fourth, giving it a very distinctive and somewhat unstable sound. Named after the Saba wind (east wind) in Arabic tradition, this maqam has a unique character that sets it apart from other maqams. Its unusual interval structure creates a sense of tension that doesn't fully resolve, contributing to its emotional impact.",
    "siga": "Siga features neutral seconds and thirds, giving it a distinctive Middle Eastern sound that's neither major nor minor in the Western sense. It's closely related to Rast but with different intonation of certain notes. Siga is particularly important in Turkish classical music where it's known as Segah."
}

# Define maqam common uses
MAQAM_COMMON_USES = {
    "ajam": "Commonly used for expressing joy, celebration, and triumph. Ajam's bright and uplifting quality makes it perfect for festive occasions, weddings, and other celebratory events. It's also used in children's songs and educational music due to its simplicity and familiarity to Western ears. In traditional settings, Ajam is associated with afternoon performances.",
    "rast": "Often used for joyful, stately, or proud musical expressions. Rast conveys a sense of stability, strength, and clarity. It's commonly used in celebratory music, anthems, and pieces that express dignity or confidence. In traditional settings, Rast is associated with morning performances.",
    "nahawand": "Used for expressing sadness, longing, or contemplation. Nahawand is perfect for romantic songs, laments, and pieces that convey nostalgia or yearning. Its emotional range allows for both gentle melancholy and deeper expressions of grief.",
    "hijaz": "Often used to express longing, nostalgia, or spiritual yearning. Hijaz is common in religious music across multiple faiths in the Middle East. It's also used in folk music and dance pieces. The dramatic quality of Hijaz makes it suitable for expressing intense emotions and passionate themes.",
    "kurd": "Often used for melancholic or contemplative pieces. Kurd can express a range of emotions from gentle sadness to deep introspection. It's commonly used in folk songs, lullabies, and pieces that tell stories of hardship or perseverance. The maqam can also convey a sense of mystery or ancient wisdom.",
    "bayati": "Bayati is an extremely versatile maqam used for various emotional expressions. It can convey tenderness, warmth, and intimacy, making it perfect for love songs and lullabies. It's also used for narrative songs, improvisations (taqasim), and dance music. In traditional settings, Bayati is associated with mid-morning performances.",
    "saba": "Often used to express deep sadness, pain, or lamentation. Saba is traditionally associated with funerals, mourning, and expressions of grief. It can convey a sense of yearning that goes beyond ordinary sadness into a realm of profound emotional depth. In some traditions, Saba is associated with dawn performances.",
    "siga": "Often used for contemplative, spiritual, or mystical music. Siga can create an atmosphere of transcendence and otherworldliness, making it suitable for religious music and meditative pieces. It's also used in improvisations that explore subtle emotional nuances and spiritual themes."
}