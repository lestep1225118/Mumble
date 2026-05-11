"""
Key Compatibility Module
Handles musical key relationships for DJ mixing

Compatible keys for mixing:
1. Same key
2. Relative major/minor (e.g., C major ↔ A minor)
3. One semitone up/down from source key
4. One semitone up/down from relative key
"""

class KeyCompatibility:
    def __init__(self):
        # All keys in chromatic order
        self.notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Alternative note names (flats)
        self.enharmonic = {
            'Db': 'C#', 'Eb': 'D#', 'Fb': 'E', 'Gb': 'F#', 
            'Ab': 'G#', 'Bb': 'A#', 'Cb': 'B',
            'E#': 'F', 'B#': 'C'
        }
        
        # Relative minor is 3 semitones down from major
        # Relative major is 3 semitones up from minor
        self.relative_interval = 3
    
    def normalize_key(self, key):
        """Normalize key name to standard format (e.g., 'C major', 'A minor')"""
        key = key.strip()
        
        # Handle various formats
        key_lower = key.lower()
        
        # Extract note and mode
        parts = key.replace('-', ' ').replace('_', ' ').split()
        
        if len(parts) >= 2:
            note = parts[0]
            mode = parts[1].lower()
        elif 'm' in key_lower and not key_lower.endswith('major') and not key_lower.endswith('maj'):
            # Handle format like "Am" or "C#m"
            if key_lower.endswith('min') or key_lower.endswith('minor'):
                note = key[:-5] if key_lower.endswith('minor') else key[:-3]
                mode = 'minor'
            else:
                note = key[:-1]
                mode = 'minor'
        else:
            note = key.rstrip('Mm')
            mode = 'major'
        
        # Normalize note name
        note = note[0].upper() + note[1:].lower() if len(note) > 1 else note.upper()
        
        # Convert flats to sharps
        if note in self.enharmonic:
            note = self.enharmonic[note]
        
        # Normalize mode
        if mode in ['min', 'm', 'minor']:
            mode = 'minor'
        else:
            mode = 'major'
        
        return f"{note} {mode}"
    
    def get_note_index(self, note):
        """Get the chromatic index of a note"""
        if note in self.enharmonic:
            note = self.enharmonic[note]
        return self.notes.index(note)
    
    def get_note_at_index(self, index):
        """Get note name at chromatic index (wraps around)"""
        return self.notes[index % 12]
    
    def get_relative_key(self, key):
        """Get the relative major/minor of a key"""
        normalized = self.normalize_key(key)
        parts = normalized.split()
        note = parts[0]
        mode = parts[1]
        
        note_index = self.get_note_index(note)
        
        if mode == 'major':
            # Relative minor is 3 semitones down
            relative_index = (note_index - self.relative_interval) % 12
            relative_note = self.get_note_at_index(relative_index)
            return f"{relative_note} minor"
        else:
            # Relative major is 3 semitones up
            relative_index = (note_index + self.relative_interval) % 12
            relative_note = self.get_note_at_index(relative_index)
            return f"{relative_note} major"
    
    def shift_key(self, key, semitones):
        """Shift a key by given semitones"""
        normalized = self.normalize_key(key)
        parts = normalized.split()
        note = parts[0]
        mode = parts[1]
        
        note_index = self.get_note_index(note)
        new_index = (note_index + semitones) % 12
        new_note = self.get_note_at_index(new_index)
        
        return f"{new_note} {mode}"
    
    def get_compatible_keys(self, source_key, pitch_semitone_range=1, include_fifths=True):
        """
        Get all keys compatible for mixing with the source key.

        Rules:
        1. Same key
        2. Relative major/minor
        3. Same mode, every key from (source ± pitch_semitone_range) semitones
        4. Same mode, every key from (relative ± pitch_semitone_range) semitones
        5. Optionally: perfect fifth up/down from source (circle-of-fifths neighbors)
        """
        normalized = self.normalize_key(source_key)
        relative = self.get_relative_key(normalized)

        try:
            r = int(pitch_semitone_range)
        except (TypeError, ValueError):
            r = 1
        r = max(0, min(r, 11))

        compatible = set()
        compatible.add(normalized)
        compatible.add(relative)

        for d in range(-r, r + 1):
            compatible.add(self.shift_key(normalized, d))
            compatible.add(self.shift_key(relative, d))

        if include_fifths:
            compatible.add(self.shift_key(normalized, 7))
            compatible.add(self.shift_key(normalized, -7))

        return sorted(list(compatible))

    def explain_compatibility(self, source_key, pitch_semitone_range=1, include_fifths=True):
        """Explain why each compatible key works for the current pitch range and options."""
        normalized = self.normalize_key(source_key)
        relative = self.get_relative_key(normalized)
        keys = self.get_compatible_keys(source_key, pitch_semitone_range, include_fifths)

        try:
            r = int(pitch_semitone_range)
        except (TypeError, ValueError):
            r = 1
        r = max(0, min(r, 11))

        fifth_up = self.shift_key(normalized, 7)
        fifth_down = self.shift_key(normalized, -7)

        explanations = {}
        for k in keys:
            nk = self.normalize_key(k)
            if nk == normalized:
                explanations[k] = "Same key — perfect harmonic match"
            elif nk == relative:
                explanations[k] = (
                    "Relative major/minor — same pitch classes, different tonic"
                )
            elif include_fifths and nk == self.normalize_key(fifth_up):
                explanations[k] = (
                    "Perfect fifth up — circle-of-fifths (e.g. A major if source is D major)"
                )
            elif include_fifths and nk == self.normalize_key(fifth_down):
                explanations[k] = (
                    "Perfect fifth down — circle-of-fifths (e.g. G major if source is D major)"
                )
            else:
                matched = False
                for d in range(-r, r + 1):
                    if nk == self.normalize_key(self.shift_key(normalized, d)):
                        if d != 0:
                            explanations[k] = (
                                f"Same mode; {d:+d} semitone(s) from source — "
                                "works with pitch shift / harmonic mixing"
                            )
                        matched = True
                        break
                if not matched:
                    for d in range(-r, r + 1):
                        if nk == self.normalize_key(self.shift_key(relative, d)):
                            explanations[k] = (
                                f"Relative key transposed by {d:+d} semitone(s)"
                            )
                            matched = True
                            break
                if not matched:
                    explanations[k] = "Within your selected compatible-key rules"

        return explanations
    
    def check_compatibility(self, key1, key2, pitch_semitone_range=1, include_fifths=True):
        """Check if two keys are compatible for mixing"""
        normalized1 = self.normalize_key(key1)
        normalized2 = self.normalize_key(key2)

        compatible_keys = self.get_compatible_keys(
            normalized1, pitch_semitone_range, include_fifths
        )
        normalized_compatible = {self.normalize_key(k) for k in compatible_keys}

        return normalized2 in normalized_compatible
    
    def get_camelot_code(self, key):
        """Convert key to Camelot wheel code (popular DJ notation)"""
        normalized = self.normalize_key(key)
        parts = normalized.split()
        note = parts[0]
        mode = parts[1]
        
        # Camelot wheel mapping
        camelot_major = {
            'B': '1B', 'F#': '2B', 'C#': '3B', 'G#': '4B',
            'D#': '5B', 'A#': '6B', 'F': '7B', 'C': '8B',
            'G': '9B', 'D': '10B', 'A': '11B', 'E': '12B'
        }
        
        camelot_minor = {
            'G#': '1A', 'D#': '2A', 'A#': '3A', 'F': '4A',
            'C': '5A', 'G': '6A', 'D': '7A', 'A': '8A',
            'E': '9A', 'B': '10A', 'F#': '11A', 'C#': '12A'
        }
        
        if mode == 'major':
            return camelot_major.get(note, 'Unknown')
        else:
            return camelot_minor.get(note, 'Unknown')


# Test the module
if __name__ == '__main__':
    kc = KeyCompatibility()
    
    test_keys = ['C major', 'Am', 'F# minor', 'Bb major', 'G minor']
    
    for key in test_keys:
        print(f"\n{'='*50}")
        print(f"Source Key: {key} → {kc.normalize_key(key)}")
        print(f"Relative: {kc.get_relative_key(key)}")
        print(f"Camelot: {kc.get_camelot_code(key)}")
        print(f"Compatible keys: {kc.get_compatible_keys(key)}")

