"""
Song Recommender Module
Uses AI and music databases to recommend compatible songs for mixing
"""

import os
import json
import requests

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not installed. AI recommendations disabled.")

# Try to import Tunebat scraper
try:
    from tunebat_scraper import TunebatScraper
    TUNEBAT_AVAILABLE = True
except ImportError:
    TUNEBAT_AVAILABLE = False
    print("⚠️ Tunebat scraper not available for recommendations.")

# Sample song database with various genres and characteristics
SONG_DATABASE = [
    # Bollywood
    {"title": "Tum Hi Ho", "artist": "Arijit Singh", "bpm": 70, "key": "E minor", "mood": "romantic", "genre": "Bollywood", "language": "Hindi", "energy": 45},
    {"title": "Kesariya", "artist": "Arijit Singh", "bpm": 98, "key": "G major", "mood": "romantic", "genre": "Bollywood", "language": "Hindi", "energy": 55},
    {"title": "Raataan Lambiyan", "artist": "Jubin Nautiyal", "bpm": 85, "key": "A minor", "mood": "romantic", "genre": "Bollywood", "language": "Hindi", "energy": 50},
    {"title": "Dil Diyan Gallan", "artist": "Atif Aslam", "bpm": 75, "key": "C major", "mood": "romantic", "genre": "Bollywood", "language": "Hindi", "energy": 40},
    {"title": "Channa Mereya", "artist": "Arijit Singh", "bpm": 78, "key": "D major", "mood": "melancholic", "genre": "Bollywood", "language": "Hindi", "energy": 35},
    {"title": "Gerua", "artist": "Arijit Singh", "bpm": 90, "key": "A major", "mood": "uplifting", "genre": "Bollywood", "language": "Hindi", "energy": 60},
    {"title": "Badtameez Dil", "artist": "Benny Dayal", "bpm": 128, "key": "F major", "mood": "energetic", "genre": "Bollywood", "language": "Hindi", "energy": 85},
    {"title": "Kar Gayi Chull", "artist": "Badshah", "bpm": 125, "key": "G major", "mood": "party", "genre": "Bollywood", "language": "Hindi", "energy": 88},
    
    # English Pop
    {"title": "Perfect", "artist": "Ed Sheeran", "bpm": 95, "key": "G major", "mood": "romantic", "genre": "Pop", "language": "English", "energy": 45},
    {"title": "All of Me", "artist": "John Legend", "bpm": 63, "key": "A♭ major", "mood": "romantic", "genre": "Pop", "language": "English", "energy": 40},
    {"title": "Thinking Out Loud", "artist": "Ed Sheeran", "bpm": 79, "key": "D major", "mood": "romantic", "genre": "Pop", "language": "English", "energy": 50},
    {"title": "Someone Like You", "artist": "Adele", "bpm": 68, "key": "A major", "mood": "melancholic", "genre": "Pop", "language": "English", "energy": 35},
    {"title": "Say Something", "artist": "A Great Big World", "bpm": 68, "key": "B♭ minor", "mood": "sad", "genre": "Pop", "language": "English", "energy": 30},
    {"title": "Stay With Me", "artist": "Sam Smith", "bpm": 84, "key": "A minor", "mood": "emotional", "genre": "Pop", "language": "English", "energy": 45},
    {"title": "Love Story", "artist": "Taylor Swift", "bpm": 119, "key": "D major", "mood": "happy", "genre": "Pop", "language": "English", "energy": 65},
    {"title": "Shallow", "artist": "Lady Gaga", "bpm": 96, "key": "G major", "mood": "emotional", "genre": "Pop", "language": "English", "energy": 55},
    
    # Dance/EDM
    {"title": "Titanium", "artist": "David Guetta ft. Sia", "bpm": 126, "key": "D♭ major", "mood": "powerful", "genre": "EDM", "language": "English", "energy": 80},
    {"title": "Don't You Worry Child", "artist": "Swedish House Mafia", "bpm": 129, "key": "G major", "mood": "euphoric", "genre": "EDM", "language": "English", "energy": 85},
    {"title": "Wake Me Up", "artist": "Avicii", "bpm": 124, "key": "B minor", "mood": "uplifting", "genre": "EDM", "language": "English", "energy": 82},
    {"title": "Clarity", "artist": "Zedd", "bpm": 128, "key": "F♯ minor", "mood": "emotional", "genre": "EDM", "language": "English", "energy": 78},
    {"title": "Lean On", "artist": "Major Lazer", "bpm": 98, "key": "G minor", "mood": "chill", "genre": "EDM", "language": "English", "energy": 70},
    {"title": "Faded", "artist": "Alan Walker", "bpm": 90, "key": "F minor", "mood": "melancholic", "genre": "EDM", "language": "English", "energy": 65},
    
    # R&B/Soul
    {"title": "Earned It", "artist": "The Weeknd", "bpm": 80, "key": "G major", "mood": "sensual", "genre": "R&B", "language": "English", "energy": 55},
    {"title": "Blinding Lights", "artist": "The Weeknd", "bpm": 171, "key": "F minor", "mood": "energetic", "genre": "Synthwave", "language": "English", "energy": 75},
    {"title": "Save Your Tears", "artist": "The Weeknd", "bpm": 118, "key": "C major", "mood": "nostalgic", "genre": "Pop", "language": "English", "energy": 70},
    {"title": "Halo", "artist": "Beyoncé", "bpm": 80, "key": "A major", "mood": "uplifting", "genre": "R&B", "language": "English", "energy": 60},
    {"title": "Crazy in Love", "artist": "Beyoncé", "bpm": 100, "key": "D minor", "mood": "energetic", "genre": "R&B", "language": "English", "energy": 80},
    
    # Latin
    {"title": "Despacito", "artist": "Luis Fonsi", "bpm": 89, "key": "B minor", "mood": "romantic", "genre": "Latin", "language": "Spanish", "energy": 65},
    {"title": "Shape of You", "artist": "Ed Sheeran", "bpm": 96, "key": "C♯ minor", "mood": "catchy", "genre": "Pop", "language": "English", "energy": 75},
    {"title": "Bailando", "artist": "Enrique Iglesias", "bpm": 104, "key": "C minor", "mood": "dance", "genre": "Latin", "language": "Spanish", "energy": 78},
    
    # Hip-Hop
    {"title": "See You Again", "artist": "Wiz Khalifa", "bpm": 80, "key": "G major", "mood": "emotional", "genre": "Hip-Hop", "language": "English", "energy": 50},
    {"title": "Lose Yourself", "artist": "Eminem", "bpm": 86, "key": "D minor", "mood": "intense", "genre": "Hip-Hop", "language": "English", "energy": 85},
    {"title": "Sunflower", "artist": "Post Malone", "bpm": 90, "key": "D major", "mood": "chill", "genre": "Hip-Hop", "language": "English", "energy": 55},
    
    # Rock/Alternative
    {"title": "Someone You Loved", "artist": "Lewis Capaldi", "bpm": 110, "key": "C major", "mood": "emotional", "genre": "Pop", "language": "English", "energy": 50},
    {"title": "Fix You", "artist": "Coldplay", "bpm": 69, "key": "E♭ major", "mood": "hopeful", "genre": "Alternative", "language": "English", "energy": 55},
    {"title": "The Scientist", "artist": "Coldplay", "bpm": 75, "key": "F major", "mood": "melancholic", "genre": "Alternative", "language": "English", "energy": 40},
    {"title": "Yellow", "artist": "Coldplay", "bpm": 88, "key": "B major", "mood": "romantic", "genre": "Alternative", "language": "English", "energy": 50},
    {"title": "Chasing Cars", "artist": "Snow Patrol", "bpm": 104, "key": "A major", "mood": "emotional", "genre": "Alternative", "language": "English", "energy": 45},
]


class SongRecommender:
    def __init__(self):
        self.database = SONG_DATABASE
        self.openai_client = None
        self.tunebat = TunebatScraper() if TUNEBAT_AVAILABLE else None
        
        # Initialize OpenAI if API key is available
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key and OPENAI_AVAILABLE:
            try:
                self.openai_client = OpenAI(api_key=api_key)
            except Exception as e:
                print(f"OpenAI initialization failed: {e}")
    
    def get_recommendations(self, source_analysis, prompt, compatible_keys):
        """
        Get song recommendations based on source analysis and user prompt
        
        Args:
            source_analysis: dict with bpm, key, mood, energy, etc.
            prompt: user's search prompt
            compatible_keys: list of harmonically compatible keys
        
        Returns:
            list of recommended songs with compatibility scores
        """
        # Parse the prompt for additional filters
        prompt_filters = self._parse_prompt(prompt)
        source_bpm = source_analysis.get('bpm', 120)
        
        # Try to get results from Tunebat first
        tunebat_results = []
        if self.tunebat:
            tunebat_results = self._search_tunebat_recommendations(
                source_analysis, prompt_filters, compatible_keys
            )
        
        # Also filter local database
        key_filtered = self._filter_by_keys(compatible_keys)
        bpm_filtered = self._filter_by_bpm(key_filtered, source_bpm, tolerance=0.15)
        prompt_filtered = self._apply_prompt_filters(bpm_filtered, prompt_filters)
        
        # Combine Tunebat results with local database
        all_results = tunebat_results + prompt_filtered
        
        # Remove duplicates (by title similarity)
        seen_titles = set()
        unique_results = []
        for song in all_results:
            title_key = song.get('title', '').lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_results.append(song)
        
        # Score and rank results
        scored_results = self._score_results(unique_results, source_analysis, prompt_filters)
        
        # Sort by score
        scored_results.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        # If we have OpenAI, enhance with AI analysis
        if self.openai_client and len(scored_results) > 0:
            scored_results = self._enhance_with_ai(scored_results, source_analysis, prompt)
        
        # Limit results
        return scored_results[:10]
    
    def _search_tunebat_recommendations(self, source_analysis, prompt_filters, compatible_keys):
        """Search Tunebat for songs matching the criteria"""
        results = []
        
        try:
            source_bpm = source_analysis.get('bpm', 120)
            source_key = source_analysis.get('key', 'C major')
            
            # Build search queries based on prompt filters
            search_queries = []
            
            # Add genre/language specific searches
            if prompt_filters.get('genre'):
                search_queries.append(f"{prompt_filters['genre']} {source_bpm} bpm")
            
            if prompt_filters.get('language'):
                lang = prompt_filters['language']
                if lang.lower() == 'english':
                    search_queries.append(f"pop {source_bpm} bpm")
                    search_queries.append(f"english song {source_key}")
                elif lang.lower() == 'hindi':
                    search_queries.append(f"bollywood {source_bpm} bpm")
                    search_queries.append(f"hindi song {source_key}")
            
            if prompt_filters.get('mood'):
                search_queries.append(f"{prompt_filters['mood']} song {source_bpm} bpm")
            
            # Default search if no specific filters
            if not search_queries:
                search_queries.append(f"{source_key} {source_bpm} bpm")
            
            # Execute searches (limit to avoid too many requests)
            for query in search_queries[:2]:
                print(f"🔍 Tunebat recommendation search: {query}")
                song = self.tunebat.search_song(query)
                if song and song.get('bpm'):
                    # Check if key is compatible
                    song_key = self._normalize_key(song.get('key', 'C major'))
                    normalized_compatible = [self._normalize_key(k) for k in compatible_keys]
                    
                    if song_key in normalized_compatible:
                        song['source'] = 'tunebat'
                        results.append(song)
                        print(f"✅ Found compatible: {song.get('title')}")
        
        except Exception as e:
            print(f"Tunebat recommendation search error: {e}")
        
        return results
    
    def _filter_by_keys(self, compatible_keys):
        """Filter songs by compatible keys"""
        if not compatible_keys:
            return self.database.copy()
        
        # Normalize keys for comparison
        normalized_compatible = set()
        for key in compatible_keys:
            normalized_compatible.add(self._normalize_key(key))
        
        filtered = []
        for song in self.database:
            song_key = self._normalize_key(song['key'])
            if song_key in normalized_compatible:
                filtered.append(song.copy())
        
        return filtered
    
    def _normalize_key(self, key):
        """Normalize key names for comparison"""
        key = key.strip().lower()
        
        # Replace common variations
        replacements = {
            '♭': 'b', '♯': '#',
            ' major': ' major', ' minor': ' minor',
            ' maj': ' major', ' min': ' minor',
            'm': ' minor'  # Handle "Am" format
        }
        
        for old, new in replacements.items():
            key = key.replace(old, new)
        
        # Ensure proper format
        if 'major' not in key and 'minor' not in key:
            if key.endswith(' minor'):
                pass
            else:
                key = key + ' major'
        
        return key
    
    def _filter_by_bpm(self, songs, target_bpm, tolerance=0.15):
        """Filter songs within BPM tolerance (also considers half/double time)"""
        filtered = []
        
        for song in songs:
            song_bpm = song['bpm']
            
            # Check direct BPM match
            if abs(song_bpm - target_bpm) <= target_bpm * tolerance:
                song_copy = song.copy()
                song_copy['bpm_match'] = 'direct'
                filtered.append(song_copy)
            # Check half-time match
            elif abs(song_bpm * 2 - target_bpm) <= target_bpm * tolerance:
                song_copy = song.copy()
                song_copy['bpm_match'] = 'half-time (double to match)'
                filtered.append(song_copy)
            # Check double-time match
            elif abs(song_bpm / 2 - target_bpm) <= target_bpm * tolerance:
                song_copy = song.copy()
                song_copy['bpm_match'] = 'double-time (halve to match)'
                filtered.append(song_copy)
        
        return filtered
    
    def _parse_prompt(self, prompt):
        """Parse user prompt for filter criteria"""
        prompt_lower = prompt.lower()
        
        filters = {
            'language': None,
            'genre': None,
            'mood': None,
            'energy_preference': None
        }
        
        # Language detection
        if 'english' in prompt_lower:
            filters['language'] = 'English'
        elif 'hindi' in prompt_lower or 'bollywood' in prompt_lower:
            filters['language'] = 'Hindi'
        elif 'spanish' in prompt_lower or 'latin' in prompt_lower:
            filters['language'] = 'Spanish'
        
        # Genre detection
        genres = ['pop', 'edm', 'bollywood', 'hip-hop', 'r&b', 'rock', 'latin', 'alternative']
        for genre in genres:
            if genre in prompt_lower:
                filters['genre'] = genre.title()
                break
        
        # Mood/vibe detection
        moods = ['romantic', 'energetic', 'sad', 'happy', 'chill', 'uplifting', 'emotional', 'party', 'melancholic']
        for mood in moods:
            if mood in prompt_lower:
                filters['mood'] = mood
                break
        
        # Energy preference
        if 'high energy' in prompt_lower or 'upbeat' in prompt_lower or 'energetic' in prompt_lower:
            filters['energy_preference'] = 'high'
        elif 'low energy' in prompt_lower or 'calm' in prompt_lower or 'chill' in prompt_lower:
            filters['energy_preference'] = 'low'
        elif 'similar energy' in prompt_lower or 'same energy' in prompt_lower:
            filters['energy_preference'] = 'similar'
        
        return filters
    
    def _apply_prompt_filters(self, songs, filters):
        """Apply parsed prompt filters to song list"""
        filtered = songs
        
        if filters['language']:
            filtered = [s for s in filtered if s.get('language', '').lower() == filters['language'].lower()]
        
        if filters['genre']:
            filtered = [s for s in filtered if filters['genre'].lower() in s.get('genre', '').lower()]
        
        # If we filtered too aggressively, return original list
        if len(filtered) == 0:
            return songs
        
        return filtered
    
    def _score_results(self, songs, source_analysis, filters):
        """Score songs based on compatibility"""
        source_bpm = source_analysis.get('bpm', 120)
        source_energy = source_analysis.get('energy', 50)
        source_mood = source_analysis.get('mood', '')
        
        scored = []
        
        for song in songs:
            score = 50  # Base score
            reasons = []
            
            # BPM compatibility (up to +20 points)
            bpm_diff = abs(song['bpm'] - source_bpm)
            bpm_score = max(0, 20 - (bpm_diff / source_bpm) * 100)
            score += bpm_score
            if bpm_diff < 5:
                reasons.append("BPM closely matches")
            
            # Energy compatibility (up to +15 points)
            energy_diff = abs(song.get('energy', 50) - source_energy)
            if filters.get('energy_preference') == 'similar':
                energy_score = max(0, 15 - energy_diff / 5)
                score += energy_score
                if energy_diff < 10:
                    reasons.append("Similar energy level")
            elif filters.get('energy_preference') == 'high' and song.get('energy', 50) > 70:
                score += 15
                reasons.append("High energy as requested")
            elif filters.get('energy_preference') == 'low' and song.get('energy', 50) < 40:
                score += 15
                reasons.append("Low energy as requested")
            
            # Mood compatibility (up to +10 points)
            if song.get('mood', '').lower() == source_mood.lower():
                score += 10
                reasons.append("Matching mood")
            elif self._moods_compatible(song.get('mood', ''), source_mood):
                score += 5
                reasons.append("Compatible mood")
            
            # Language bonus if specified (up to +5 points)
            if filters.get('language') and song.get('language', '').lower() == filters['language'].lower():
                score += 5
                reasons.append(f"Requested language ({filters['language']})")
            
            song_result = song.copy()
            song_result['compatibility_score'] = round(score, 1)
            song_result['compatibility_reasons'] = reasons
            scored.append(song_result)
        
        return scored
    
    def _moods_compatible(self, mood1, mood2):
        """Check if two moods are compatible"""
        compatible_groups = [
            {'romantic', 'emotional', 'melancholic', 'sad'},
            {'happy', 'uplifting', 'euphoric', 'energetic'},
            {'chill', 'peaceful', 'dreamy', 'nostalgic'},
            {'powerful', 'intense', 'dramatic', 'aggressive'},
            {'party', 'dance', 'catchy', 'energetic'}
        ]
        
        mood1_lower = mood1.lower()
        mood2_lower = mood2.lower()
        
        for group in compatible_groups:
            if mood1_lower in group and mood2_lower in group:
                return True
        
        return False
    
    def _enhance_with_ai(self, results, source_analysis, prompt):
        """Use AI to enhance recommendations with explanations"""
        try:
            # Create a summary for AI
            source_desc = f"BPM: {source_analysis.get('bpm')}, Key: {source_analysis.get('key')}, Mood: {source_analysis.get('mood')}, Energy: {source_analysis.get('energy')}"
            
            songs_list = "\n".join([
                f"- {r['title']} by {r['artist']} ({r['bpm']} BPM, {r['key']}, {r['mood']})"
                for r in results[:5]
            ])
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional DJ helping with song mixing recommendations. Provide brief, helpful insights about why songs would mix well together."
                    },
                    {
                        "role": "user",
                        "content": f"""Source song characteristics: {source_desc}
User's request: {prompt}

Top recommended songs:
{songs_list}

For each song, provide a one-sentence explanation of why it would mix well with the source. Format as JSON array with 'title' and 'ai_reason' fields."""
                    }
                ],
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            
            # Try to parse AI response
            try:
                ai_reasons = json.loads(ai_response)
                for result in results:
                    for ai_item in ai_reasons:
                        if ai_item.get('title', '').lower() in result['title'].lower():
                            result['ai_recommendation'] = ai_item.get('ai_reason', '')
                            break
            except json.JSONDecodeError:
                # If parsing fails, just add the raw response to first result
                if results:
                    results[0]['ai_recommendation'] = ai_response[:200]
        
        except Exception as e:
            print(f"AI enhancement failed: {e}")
        
        return results


# Test the module
if __name__ == '__main__':
    recommender = SongRecommender()
    
    # Test with a Bollywood song analysis
    source = {
        'bpm': 98,
        'key': 'G major',
        'mood': 'romantic',
        'energy': 55
    }
    
    compatible_keys = ['G major', 'E minor', 'F# minor', 'F minor', 'G# major', 'F# major']
    
    results = recommender.get_recommendations(
        source_analysis=source,
        prompt="find an English song with similar mood and vibe",
        compatible_keys=compatible_keys
    )
    
    print("Recommendations:")
    for r in results:
        print(f"\n{r['title']} by {r['artist']}")
        print(f"  Key: {r['key']}, BPM: {r['bpm']}, Mood: {r['mood']}")
        print(f"  Score: {r['compatibility_score']}")
        print(f"  Reasons: {', '.join(r.get('compatibility_reasons', []))}")

