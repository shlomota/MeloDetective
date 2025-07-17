"""
Maqam Definitions Module

This module defines Middle Eastern musical modes (maqams) using a numerical system
that supports quarter tones. The numerical system uses the following units:
- Whole step = 4 units
- Half step = 2 units
- Quarter step = 1 unit

This allows precise representation of the microtonal intervals in maqams.

The module provides:
1. Definitions for common maqams (Rast, Nahawand, Hijaz, Kurd, Bayati, Saba, Siga)
2. Conversion between frequencies and note values with quarter tone precision
3. Functions for normalizing and comparing note sequences
4. Utilities for maqam detection and analysis
"""

import numpy as np
from typing import Dict, List, Tuple, Optional

# Try to import scipy, but provide a fallback if not available
try:
    from scipy.spatial.distance import cosine as scipy_cosine
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("Warning: scipy not found. Using fallback cosine similarity implementation.")


class Maqam:
    """
    Class representing a Middle Eastern musical mode (maqam).
    """
    def __init__(self, name: str, intervals: List[int], description: str = "", common_uses: str = ""):
        """
        Initialize a maqam with its characteristic intervals.
        
        Args:
            name: The name of the maqam
            intervals: List of intervals in the numerical system (quarter tone units)
            description: Description of the maqam's characteristics
            common_uses: Common uses or emotional qualities of the maqam
        """
        self.name = name
        self.intervals = intervals  # Original intervals in quarter tones
        self.description = description
        self.common_uses = common_uses
        
        # Convert intervals to semitones for practical use
        self.semitone_intervals = [interval // 2 for interval in intervals]
        
        # Generate the scale (two octaves) starting from 0
        self.scale = self._generate_scale()
        
    def _generate_scale(self) -> List[int]:
        """
        Generate a two-octave scale from the intervals.
        
        Returns:
            List of note values representing the maqam scale
        """
        scale = [0]  # Start with the root note
        current = 0
        
        # Generate first octave
        for interval in self.intervals[1:]:
            current += interval
            scale.append(current)
            
        # Generate second octave
        octave = scale[-1]
        for interval in self.intervals[1:]:
            current += interval
            scale.append(current)
            
        return scale
    
    def get_notes_in_range(self, min_note: int, max_note: int) -> List[int]:
        """
        Get all notes of this maqam within a specific range.
        
        Args:
            min_note: Minimum note value
            max_note: Maximum note value
            
        Returns:
            List of notes within the specified range
        """
        # Find the octave size
        octave_size = self.scale[len(self.intervals) - 1]
        
        # Generate enough octaves to cover the range
        extended_scale = []
        current_base = min_note - (min_note % octave_size) - octave_size
        
        while current_base <= max_note:
            for note in self.scale:
                extended_note = note + current_base
                if min_note <= extended_note <= max_note:
                    extended_scale.append(extended_note)
            current_base += octave_size
            
        return sorted(list(set(extended_scale)))
    
    def get_histogram_template(self, bin_range: Tuple[int, int] = (-24, 25)) -> np.ndarray:
        """
        Generate a histogram template for this maqam.
        
        Args:
            bin_range: Range of bins for the histogram (min, max+1)
            
        Returns:
            Numpy array representing the histogram template
        """
        # Create an empty histogram
        num_bins = bin_range[1] - bin_range[0]
        histogram = np.zeros(num_bins)
        
        # Get normalized scale (centered around 0)
        normalized_scale = [note % 24 for note in self.scale]
        
        # Fill the histogram
        for note in normalized_scale:
            # Shift the note to match the bin range
            bin_index = note - bin_range[0]
            if 0 <= bin_index < num_bins:
                histogram[bin_index] += 1
                
        # Normalize the histogram
        if np.sum(histogram) > 0:
            histogram = histogram / np.sum(histogram)
            
        return histogram


# Define the maqams
MAQAMS = {
    "ajam": Maqam(
        name="Ajam",
        intervals=[0, 4, 4, 2, 4, 4, 4, 2],  # [0, 4, 8, 10, 14, 18, 22, 24]
        description="Ajam is a maqam that closely resembles the Western major scale. The name 'Ajam' means 'Persian' or 'non-Arab' in Arabic, reflecting its origins outside the traditional Arabic music system. Unlike many other maqams, Ajam doesn't use quarter tones, making it more accessible to musicians trained in Western music. It's characterized by its bright, straightforward sound and is often used as a foundation for learning other maqams.",
        common_uses="Commonly used for expressing joy, celebration, and triumph. Ajam's bright and uplifting quality makes it perfect for festive occasions, weddings, and other celebratory events. It's also used in children's songs and educational music due to its simplicity and familiarity to Western ears. In traditional settings, Ajam is associated with afternoon performances."
    ),
    "rast": Maqam(
        name="Rast",
        intervals=[0, 4, 3, 3, 4, 4, 3, 3],  # [0, 4, 7, 10, 14, 18, 21, 24]
        description="Rast is one of the most fundamental and common maqams in Middle Eastern music. It's similar to the Western major scale but with a neutral third (between major and minor). The name 'Rast' means 'straight' or 'direct' in Persian, reflecting its foundational role in the maqam system. It serves as a reference point for many other maqams and is often the first maqam taught to students.",
        common_uses="Often used for joyful, stately, or proud musical expressions. Rast conveys a sense of stability, strength, and clarity. It's commonly used in celebratory music, anthems, and pieces that express dignity or confidence. In traditional settings, Rast is associated with morning performances."
    ),
    "nahawand": Maqam(
        name="Nahawand",
        intervals=[0, 4, 2, 4, 4, 2, 4, 4],  # [0, 4, 6, 10, 14, 16, 20, 24]
        # This corresponds to the Western natural minor scale: [0, 2, 3, 5, 7, 8, 10, 12] in semitones
        # Or in note names: A, B, C, D, E, F, G, A (when starting on A)
        description="Nahawand is similar to the Western natural minor scale. It has a distinctive melancholic quality that makes it popular for emotional expressions. Named after the city of Nahavand in Iran, this maqam has spread throughout the Middle East and North Africa. It's particularly prominent in Turkish classical music where it's known as Buselik.",
        common_uses="Used for expressing sadness, longing, or contemplation. Nahawand is perfect for romantic songs, laments, and pieces that convey nostalgia or yearning. Its emotional range allows for both gentle melancholy and deeper expressions of grief."
    ),
    "hijaz": Maqam(
        name="Hijaz",
        intervals=[0, 2, 5, 3, 4, 2, 4, 4],  # [0, 2, 7, 10, 14, 16, 20, 24]
        description="Hijaz features an augmented second between the second and third degrees, giving it a distinctive Middle Eastern sound that's immediately recognizable to Western ears. Named after the Hijaz region in Saudi Arabia, this maqam is widely used across Arabic, Turkish, and Jewish music traditions. Its characteristic interval creates a tension that resolves beautifully in melodic phrases.",
        common_uses="Often used to express longing, nostalgia, or spiritual yearning. Hijaz is common in religious music across multiple faiths in the Middle East. It's also used in folk music and dance pieces. The dramatic quality of Hijaz makes it suitable for expressing intense emotions and passionate themes."
    ),
    "kurd": Maqam(
        name="Kurd",
        intervals=[0, 2, 4, 4, 4, 2, 4, 4],  # [0, 2, 6, 10, 14, 16, 20, 24]
        description="Kurd is similar to the Western Phrygian mode with a flattened second degree. Named after the Kurdish people, this maqam has a distinctive character created by its minor second interval at the beginning. It's widely used in Kurdish folk music but has spread throughout the Middle East and Mediterranean regions.",
        common_uses="Often used for melancholic or contemplative pieces. Kurd can express a range of emotions from gentle sadness to deep introspection. It's commonly used in folk songs, lullabies, and pieces that tell stories of hardship or perseverance. The maqam can also convey a sense of mystery or ancient wisdom."
    ),
    "bayati": Maqam(
        name="Bayati",
        intervals=[0, 3, 3, 4, 4, 4, 3, 3],  # [0, 3, 6, 10, 14, 18, 21, 24]
        description="Bayati features a neutral second degree (between major and minor) and is one of the most common and beloved maqams in Arabic music. Its name may derive from the Arabic word 'bayt' meaning 'home,' reflecting its familiar and comfortable feeling. Bayati is often considered the 'everyday' maqam due to its prevalence in both folk and classical traditions.",
        common_uses="Bayati is an extremely versatile maqam used for various emotional expressions. It can convey tenderness, warmth, and intimacy, making it perfect for love songs and lullabies. It's also used for narrative songs, improvisations (taqasim), and dance music. In traditional settings, Bayati is associated with mid-morning performances."
    ),
    "saba": Maqam(
        name="Saba",
        intervals=[0, 3, 3, 2, 6, 2, 4, 4],  # [0, 3, 6, 8, 14, 16, 20, 24]
        description="Saba features a diminished fourth, giving it a very distinctive and somewhat unstable sound. Named after the Saba wind (east wind) in Arabic tradition, this maqam has a unique character that sets it apart from other maqams. Its unusual interval structure creates a sense of tension that doesn't fully resolve, contributing to its emotional impact.",
        common_uses="Often used to express deep sadness, pain, or lamentation. Saba is traditionally associated with funerals, mourning, and expressions of grief. It can convey a sense of yearning that goes beyond ordinary sadness into a realm of profound emotional depth. In some traditions, Saba is associated with dawn performances."
    ),
    "siga": Maqam(
        name="Siga",
        intervals=[0, 3, 4, 3, 4, 3, 4, 3],  # [0, 3, 7, 10, 14, 17, 21, 24]
        description="Siga features neutral seconds and thirds, giving it a distinctive Middle Eastern sound that's neither major nor minor in the Western sense. It's closely related to Rast but with different intonation of certain notes. Siga is particularly important in Turkish classical music where it's known as Segah.",
        common_uses="Often used for contemplative, spiritual, or mystical music. Siga can create an atmosphere of transcendence and otherworldliness, making it suitable for religious music and meditative pieces. It's also used in improvisations that explore subtle emotional nuances and spiritual themes."
    )
}


def get_maqam(name: str) -> Optional[Maqam]:
    """
    Get a maqam by name.
    
    Args:
        name: Name of the maqam (case-insensitive)
        
    Returns:
        Maqam object if found, None otherwise
    """
    return MAQAMS.get(name.lower())


def get_all_maqams() -> List[Maqam]:
    """
    Get all available maqams.
    
    Returns:
        List of all maqam objects
    """
    return list(MAQAMS.values())


def frequency_to_note_value(frequency: float, reference_frequency: float = 440.0, reference_note: int = 69) -> float:
    """
    Convert a frequency to a note value with quarter tone precision.
    
    Args:
        frequency: The frequency in Hz
        reference_frequency: Reference frequency (default: A4 = 440 Hz)
        reference_note: MIDI note number of the reference frequency (default: A4 = 69)
        
    Returns:
        Note value with quarter tone precision
    """
    if frequency <= 0:
        return 0
    
    # Standard MIDI note calculation (12 semitones per octave)
    midi_note = reference_note + 12 * np.log2(frequency / reference_frequency)
    
    # Convert to quarter tone system (24 quarter tones per octave)
    quarter_tone_note = midi_note * 2
    
    return quarter_tone_note


def note_value_to_frequency(note_value: float, reference_frequency: float = 440.0, reference_note: int = 69) -> float:
    """
    Convert a note value to a frequency.
    
    Args:
        note_value: Note value with quarter tone precision
        reference_frequency: Reference frequency (default: A4 = 440 Hz)
        reference_note: MIDI note number of the reference frequency (default: A4 = 69)
        
    Returns:
        Frequency in Hz
    """
    # Convert from quarter tone system to standard MIDI note
    midi_note = note_value / 2
    
    # Convert MIDI note to frequency
    frequency = reference_frequency * 2 ** ((midi_note - reference_note) / 12)
    
    return frequency


def normalize_note_sequence(notes: List[float]) -> List[float]:
    """
    Normalize a sequence of notes by subtracting the median.
    
    Args:
        notes: List of note values
        
    Returns:
        Normalized note sequence
    """
    if len(notes) == 0:
        return []
    
    median = np.median(notes)
    return [note - median for note in notes]


def calculate_note_histogram(notes: List[float], bin_range: Tuple[int, int] = (-24, 25), 
                        weighted: bool = False, durations: List[float] = None) -> np.ndarray:
    """
    Calculate a histogram of normalized notes.
    
    Args:
        notes: List of note values
        bin_range: Range of bins for the histogram (min, max+1)
        weighted: Whether to weight notes by their duration
        durations: List of note durations (required if weighted=True)
        
    Returns:
        Numpy array representing the histogram
    """
    if len(notes) == 0:
        return np.zeros(bin_range[1] - bin_range[0])
    
    # Normalize notes
    normalized_notes = normalize_note_sequence(notes)
    
    # Modulo to bring all notes within one octave (24 quarter tones)
    normalized_notes = [note % 24 for note in normalized_notes]
    
    # Calculate histogram
    num_bins = bin_range[1] - bin_range[0]
    if weighted and durations is not None:
        # Create weighted histogram
        histogram = np.zeros(num_bins)
        for note, duration in zip(normalized_notes, durations):
            bin_index = int(note - bin_range[0])
            if 0 <= bin_index < num_bins:
                histogram[bin_index] += duration
    else:
        # Create standard histogram
        histogram, _ = np.histogram(normalized_notes, bins=np.arange(bin_range[0], bin_range[1] + 1))
    
    # Normalize histogram
    if np.sum(histogram) > 0:
        histogram = histogram / np.sum(histogram)
    
    return histogram


def _cosine_similarity_fallback(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Fallback implementation of cosine similarity when scipy is not available.
    
    Args:
        v1: First vector
        v2: Second vector
        
    Returns:
        Cosine similarity (0-1, higher is more similar)
    """
    dot_product = np.dot(v1, v2)
    norm_v1 = np.sqrt(np.sum(v1 * v1))
    norm_v2 = np.sqrt(np.sum(v2 * v2))
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    
    return dot_product / (norm_v1 * norm_v2)

def calculate_maqam_accuracy_score(input_notes: List[float], maqam_scale: List[int], use_semitones: bool = True, 
                              is_nahawand: bool = False, is_shift_9: bool = False) -> float:
    """
    Calculate an accuracy score based on how many input notes match notes in the maqam scale.
    This function directly compares the actual notes without normalization.
    Score is weighted by amplitude in the histogram.
    
    Args:
        input_notes: List of input note values
        maqam_scale: List of note values in the maqam scale
        use_semitones: Whether to use semitones (half-tones) for matching (default: True)
        is_nahawand: Whether this is for Nahawand maqam (for debug printing)
        is_shift_9: Whether this is for shift 9 (for debug printing)
        
    Returns:
        Accuracy score (0-1, higher is better)
    """
    if len(input_notes) == 0 or len(maqam_scale) == 0:
        return 0.0
    
    # Always quantize notes to semitones for practical matching
    input_notes_semitones = [round(note / 2) * 2 for note in input_notes]
    maqam_scale_semitones = [round(note / 2) * 2 for note in maqam_scale]
    
    # Convert to MIDI note numbers for easier comparison
    input_midi_notes = [int(round(note / 2)) for note in input_notes_semitones]
    maqam_midi_notes = [int(round(note / 2)) for note in maqam_scale_semitones]
    
    # Create a set of the maqam scale notes for efficient lookup
    maqam_notes_set = set(maqam_midi_notes)
    
    # For debugging, also track normalized notes
    maqam_notes_normalized_set = set([note % 12 for note in maqam_midi_notes])
    
    # Print debug info only for Nahawand at shift 9
    debug_print = is_nahawand and is_shift_9
    
    if debug_print:
        print(f"Maqam notes set (normalized): {sorted(list(maqam_notes_normalized_set))}")
        print(f"Maqam notes set (absolute, first 20): {sorted(list(maqam_notes_set))[:20]}")
    
    # Count occurrences of each note in the input (weighted by amplitude)
    note_counts = {}
    
    for note in input_midi_notes:
        if note in note_counts:
            note_counts[note] += 1
        else:
            note_counts[note] = 1
    
    # Print input notes for debugging
    if debug_print:
        print(f"Input notes (absolute): {sorted(list(note_counts.keys()))}")
    
    # Count matching notes (weighted by amplitude)
    matching_notes = 0
    total_notes = len(input_midi_notes)
    
    for note, count in note_counts.items():
        if note in maqam_notes_set:
            matching_notes += count
            if debug_print:
                print(f"Note {note} matched in maqam scale, count: {count}")
        elif debug_print:
            print(f"Note {note} not found in maqam scale, count: {count}")
    
    # Calculate the accuracy score - ratio of matching notes to total notes, weighted by amplitude
    accuracy = matching_notes / total_notes if total_notes > 0 else 0.0
    
    # Print detailed scores for debugging
    if debug_print:
        print(f"Matching notes: {matching_notes}/{total_notes}, Accuracy: {accuracy:.4f}")
    
    return accuracy


def calculate_maqam_accuracy_score(input_notes: List[float], maqam_semitone_positions: List[int], 
                                 shift: int = 0, is_nahawand: bool = False, is_shift_9: bool = False) -> float:
    """
    Calculate a weighted accuracy score based on how many input notes match the maqam pattern.
    Score = (sum of weights for matching notes) / (total sum of weights)
    
    Args:
        input_notes: List of input note values
        maqam_semitone_positions: List of semitone positions in the maqam (0-11)
        shift: Semitone shift to apply to maqam (0-11)
        
    Returns:
        Weighted accuracy score (0-1, higher is better)
    """
    if len(input_notes) == 0 or len(maqam_semitone_positions) == 0:
        return 0.0
    
    # Convert to MIDI note numbers
    input_midi_notes = [int(round(note / 2)) for note in input_notes]
    
    # Create shifted maqam pattern (modulo 12 for octave equivalence)
    shifted_maqam_set = set((pos + shift) % 12 for pos in maqam_semitone_positions)
    
    # Count occurrences of each note (weights)
    note_weights = {}
    for note in input_midi_notes:
        note_mod12 = note % 12  # Reduce to octave equivalence
        note_weights[note_mod12] = note_weights.get(note_mod12, 0) + 1
    
    # Calculate weighted score
    matching_weight = sum(weight for note, weight in note_weights.items() if note in shifted_maqam_set)
    total_weight = sum(note_weights.values())
    
    return matching_weight / total_weight if total_weight > 0 else 0.0


def compare_histograms(hist1: np.ndarray, hist2: np.ndarray) -> float:
    """
    Compare two histograms using cosine similarity.
    
    Args:
        hist1: First histogram
        hist2: Second histogram
        
    Returns:
        Similarity score (0-1, higher is more similar)
    """
    # Handle zero histograms
    if np.sum(hist1) == 0 or np.sum(hist2) == 0:
        return 0.0
    
    if SCIPY_AVAILABLE:
        return 1 - scipy_cosine(hist1, hist2)
    else:
        return _cosine_similarity_fallback(hist1, hist2)


# Cache for maqam histograms
_maqam_histogram_cache = {}

def detect_maqam(notes: List[float], transposition_range: Tuple[int, int] = (-12, 13), 
                use_semitones: bool = True) -> List[Tuple[str, float, int, float, int]]:
    """
    Detect the most likely maqam from a sequence of notes using absolute note positions.
    
    Args:
        notes: List of note values
        transposition_range: Range of transpositions to try (min, max)
        use_semitones: Whether to use semitones (half-tones) for matching instead of quarter tones
        
    Returns:
        List of (maqam_name, confidence, best_shift, original_pitch, starting_note) tuples, sorted by confidence (highest first)
        where:
        - original_pitch is the estimated starting pitch of the input
        - starting_note is the actual starting note of the melody (MIDI note number)
    """
    if len(notes) == 0:
        return []
    
    # Always use semitones for practical matching
    use_semitones = True
    
    # Calculate the original pitch (median) and starting note
    original_pitch = np.median(notes) if len(notes) > 0 else 0
    starting_note = int(round(min(notes) / 2)) if len(notes) > 0 else 0  # Convert to MIDI note number
    
    # Convert to MIDI note numbers for easier comparison
    # This is what's used in the visualization
    input_midi_notes = [int(round(note / 2)) for note in notes]
    
    # Print debug info about the input notes
    print(f"Input notes (first 10): {notes[:10]}")
    print(f"Starting MIDI note: {starting_note}")
    print(f"Original pitch: {original_pitch}")
    print(f"Input MIDI notes: {input_midi_notes[:10]}")
    
    # Compare with each maqam
    results = []
    for maqam_name, maqam in MAQAMS.items():
        # Define the semitone positions for each maqam
        if maqam_name == "nahawand":
            # Nahawand corresponds to the natural minor scale: [0, 2, 3, 5, 7, 8, 10, 12] in semitones
            semitone_positions = [0, 2, 3, 5, 7, 8, 10]
        elif maqam_name == "ajam":
            # Ajam corresponds to the major scale: [0, 2, 4, 5, 7, 9, 11, 12] in semitones
            semitone_positions = [0, 2, 4, 5, 7, 9, 11]
        elif maqam_name == "rast":
            # Rast with neutral third: [0, 2, 3.5, 5, 7, 9, 10.5, 12] in semitones
            # Approximated to: [0, 2, 4, 5, 7, 9, 11, 12] for Western ears
            semitone_positions = [0, 2, 4, 5, 7, 9, 11]
        elif maqam_name == "hijaz":
            # Hijaz with augmented second: [0, 1, 4, 5, 7, 8, 10, 12] in semitones
            semitone_positions = [0, 1, 4, 5, 7, 8, 10]
        elif maqam_name == "kurd":
            # Kurd (Phrygian): [0, 1, 3, 5, 7, 8, 10, 12] in semitones
            semitone_positions = [0, 1, 3, 5, 7, 8, 10]
        elif maqam_name == "bayati":
            # Bayati with neutral second: [0, 1.5, 3, 5, 7, 9, 10.5, 12] in semitones
            # Approximated to: [0, 2, 3, 5, 7, 9, 10, 12] for Western ears
            semitone_positions = [0, 2, 3, 5, 7, 9, 10]
        elif maqam_name == "saba":
            # Saba with diminished fourth: [0, 1.5, 3, 4, 7, 8, 10, 12] in semitones
            # Approximated to: [0, 2, 3, 4, 7, 8, 10, 12] for Western ears
            semitone_positions = [0, 2, 3, 4, 7, 8, 10]
        elif maqam_name == "siga":
            # Siga with neutral seconds and thirds: [0, 1.5, 3.5, 5, 7, 8.5, 10.5, 12] in semitones
            # Approximated to: [0, 2, 4, 5, 7, 9, 11, 12] for Western ears
            semitone_positions = [0, 2, 4, 5, 7, 9, 11]
        else:
            # For other maqams, calculate from intervals
            semitone_positions = []
            current_pos = 0
            
            # Convert quarter tone intervals to semitone positions
            for i, interval in enumerate(maqam.intervals):
                semitone_positions.append(current_pos // 2)  # Convert to semitones
                current_pos += interval
            
            # Remove the last position (octave) to avoid duplicates
            semitone_positions = semitone_positions[:-1]
        
        # Try different transpositions (shifts)
        best_score = 0
        best_shift = 0
        
        # Try all 12 semitone shifts
        for shift in range(0, 12, 1):
            # Generate the maqam scale with this shift
            maqam_scale = []
            
            # Find the range of input notes
            min_midi_note = min(input_midi_notes)
            max_midi_note = max(input_midi_notes)
            
            # Extend the range by 2 octaves in each direction
            min_octave = (min_midi_note // 12) - 1
            max_octave = (max_midi_note // 12) + 1
            
            # Generate the maqam scale across this range
            for octave in range(min_octave, max_octave + 1):
                for pos in semitone_positions:
                    note = octave * 12 + pos + shift
                    maqam_scale.append(note)
            
            # Calculate accuracy score for this shift
            is_nahawand = (maqam_name == "nahawand")
            is_shift_9 = (shift == 9)
            accuracy = calculate_maqam_accuracy_score(notes, semitone_positions, shift, 
                                        is_nahawand=is_nahawand, is_shift_9=is_shift_9)
            
            # Calculate the maqam's root note based on the shift
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            maqam_root_index = (shift % 12)
            maqam_root_note = note_names[maqam_root_index]
            
            # Print detailed info ONLY for Nahawand
            if is_nahawand:
                print(f"Maqam Nahawand, Shift {shift} (starting on {maqam_root_note}): accuracy = {accuracy:.4f}")
            
            if accuracy > best_score:
                best_score = accuracy
                best_shift = shift
        
        # Include the original pitch and starting note in the results
        results.append((maqam_name, best_score, best_shift, original_pitch, starting_note))
    
    # Sort by similarity (highest first)
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results


def get_maqam_note_names(maqam_name: str, base_note: str = "C") -> List[str]:
    """
    Get the note names for a maqam starting from a specific base note.
    
    Args:
        maqam_name: Name of the maqam
        base_note: Base note name (default: "C")
        
    Returns:
        List of note names in the maqam
    """
    maqam = get_maqam(maqam_name)
    if not maqam:
        return []
    
    # Define note names
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    quarter_tone_names = {
        1: "quarter sharp",
        3: "quarter flat"
    }
    
    # Find base note index
    base_index = note_names.index(base_note)
    
    # Generate note names for the maqam
    result = []
    current_note = 0
    
    for interval in maqam.intervals:
        # Calculate the note index
        note_index = (current_note // 2 + base_index) % 12
        quarter_tone = current_note % 2
        
        # Get the note name
        note_name = note_names[note_index]
        
        # Add quarter tone indicator if needed
        if quarter_tone in quarter_tone_names:
            note_name += " " + quarter_tone_names[quarter_tone]
        
        result.append(note_name)
        current_note += interval
    
    return result


if __name__ == "__main__":
    # Example usage
    rast = get_maqam("rast")
    print(f"Maqam: {rast.name}")
    print(f"Scale: {rast.scale}")
    print(f"Description: {rast.description}")
    
    # Test frequency conversion
    a4_freq = 440.0
    a4_note = frequency_to_note_value(a4_freq)
    print(f"A4 (440 Hz) = Note value {a4_note}")
    print(f"Note value {a4_note} = {note_value_to_frequency(a4_note)} Hz")
    
    # Test quarter tone
    quarter_tone_up = note_value_to_frequency(a4_note + 1)
    print(f"Quarter tone above A4 = {quarter_tone_up} Hz")
    
    # Test maqam detection
    print("\nMaqam Detection Test:")
    
    # Create a sample note sequence for Hijaz
    hijaz = get_maqam("hijaz")
    hijaz_notes = hijaz.scale[:8]  # First octave
    print(f"Original Hijaz notes: {hijaz_notes}")
    
    # Add some random variations to simulate real input
    import random
    random.seed(42)  # For reproducibility
    noisy_hijaz = [note + random.uniform(-1, 1) for note in hijaz_notes]
    print(f"Noisy Hijaz notes: {[round(n, 2) for n in noisy_hijaz]}")
    
    # Transpose the notes to simulate different starting pitch
    transposed_hijaz = [note + 5 for note in noisy_hijaz]  # Transpose up
    print(f"Transposed Hijaz: {[round(n, 2) for n in transposed_hijaz]}")
    
    # Detect the maqam
    results = detect_maqam(transposed_hijaz)
    print("\nDetection Results:")
    for maqam_name, confidence, shift in results[:10]:  # Show top 3
        print(f"{get_maqam(maqam_name).name}: {confidence:.4f} (shift: {shift})")
    
    # Show note names for the detected maqam
    top_maqam = results[0][0]
    note_names = get_maqam_note_names(top_maqam, "D")  # Starting from D
    print(f"\n{get_maqam(top_maqam).name} starting from D: {note_names}")
    
    # Test with a more realistic example - create a longer sequence with more notes
    print("\n\nMore Realistic Test:")
    
    # Create a longer sequence of Hijaz notes with repetitions
    hijaz_longer = []
    for _ in range(3):  # Repeat the scale 3 times
        hijaz_longer.extend(hijaz.scale[:8])
    
    # Add some random variations and occasional "wrong" notes
    random.seed(43)  # Different seed
    realistic_hijaz = []
    for note in hijaz_longer:
        # 90% chance of using a note from the scale with small variation
        if random.random() < 0.9:
            realistic_hijaz.append(note + random.uniform(-0.5, 0.5))
        else:
            # 10% chance of a "wrong" note (could be from singing errors)
            realistic_hijaz.append(note + random.uniform(-4, 4))
    
    # Transpose to simulate different vocal range
    realistic_transposed = [note + 3 for note in realistic_hijaz]
    
    print(f"Created a realistic Hijaz melody with {len(realistic_transposed)} notes")
    
    # Detect the maqam
    results = detect_maqam(realistic_transposed)
    print("\nDetection Results (Realistic Test):")
    for maqam_name, confidence, shift in results[:10]:  # Show top 3
        print(f"{get_maqam(maqam_name).name}: {confidence:.4f} (shift: {shift})")