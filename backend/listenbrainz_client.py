"""
ListenBrainz API Client
Gets song data (BPM, key, etc.) from ListenBrainz/MusicBrainz

API Docs: https://listenbrainz.readthedocs.io/
"""

import os
import requests
import time


class ListenBrainzClient:
    def __init__(self, user_token=None):
        # Default token (can be overridden via env var or parameter)
        default_token = '2e8002c8-fb62-4c04-aabf-871d625d3cef'
        self.user_token = user_token or os.environ.get('LISTENBRAINZ_TOKEN', default_token)
        self.api_base = "https://api.listenbrainz.org"
        self.musicbrainz_api = "https://musicbrainz.org/ws/2"
        self.acousticbrainz_api = "https://acousticbrainz.org/api/v1"  # May be deprecated
        
        # Rate limiting
        self._last_request_time = 0
        self._min_delay = 1.0  # 1 second between requests to be safe
        
        # Key mapping
        self.key_map = {
            'C': 'C', 'C#': 'C#', 'Db': 'C#',
            'D': 'D', 'D#': 'D#', 'Eb': 'D#',
            'E': 'E', 'Fb': 'E',
            'F': 'F', 'E#': 'F', 'F#': 'F#', 'Gb': 'F#',
            'G': 'G', 'G#': 'G#', 'Ab': 'G#',
            'A': 'A', 'A#': 'A#', 'Bb': 'A#',
            'B': 'B', 'Cb': 'B'
        }
    
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed)
        self._last_request_time = time.time()
    
    def _get_headers(self):
        """Get request headers with auth token"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mumble-DJ-Assistant/1.0 (https://github.com/mumble)'
        }
        if self.user_token:
            headers['Authorization'] = f'Token {self.user_token}'
        return headers
    
    def is_available(self):
        """Check if the API is configured"""
        return self.user_token is not None
    
    def lookup_recording(self, artist_name, recording_name):
        """
        Look up a recording using ListenBrainz metadata API
        
        Args:
            artist_name: Name of the artist
            recording_name: Name of the song/recording
        
        Returns:
            Recording metadata or None
        """
        self._rate_limit()
        
        try:
            # Use the metadata lookup endpoint
            url = f"{self.api_base}/1/metadata/lookup/"
            params = {
                'artist_name': artist_name,
                'recording_name': recording_name,
                'metadata': 'true',
                'inc': 'artist tag release'
            }
            
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"ListenBrainz lookup failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"ListenBrainz lookup error: {e}")
            return None
    
    def get_recording_metadata(self, recording_mbid):
        """
        Get detailed metadata for a recording by MBID
        
        Args:
            recording_mbid: MusicBrainz Recording ID
        
        Returns:
            Recording metadata
        """
        self._rate_limit()
        
        try:
            url = f"{self.api_base}/1/metadata/recording/"
            params = {
                'recording_mbids': recording_mbid,
                'inc': 'artist tag release'
            }
            
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"Recording metadata error: {e}")
            return None
    
    def search_musicbrainz(self, query, artist=''):
        """
        Search MusicBrainz for a recording
        
        Args:
            query: Song name
            artist: Artist name (optional)
        
        Returns:
            Recording data with MBID
        """
        self._rate_limit()
        
        try:
            url = f"{self.musicbrainz_api}/recording/"
            
            # Build search query
            search_query = f'recording:"{query}"'
            if artist:
                search_query += f' AND artist:"{artist}"'
            
            params = {
                'query': search_query,
                'fmt': 'json',
                'limit': 5
            }
            
            headers = {
                'User-Agent': 'Mumble-DJ-Assistant/1.0 (contact@example.com)',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('recordings'):
                    return data['recordings'][0]
            
            return None
            
        except Exception as e:
            print(f"MusicBrainz search error: {e}")
            return None
    
    def get_acousticbrainz_data(self, recording_mbid):
        """
        Get acoustic analysis data from AcousticBrainz
        Note: AcousticBrainz was discontinued but data may still be accessible
        
        Args:
            recording_mbid: MusicBrainz Recording ID
        
        Returns:
            Acoustic features (BPM, key, etc.)
        """
        self._rate_limit()
        
        try:
            # Try high-level features
            url = f"{self.acousticbrainz_api}/{recording_mbid}/high-level"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            print(f"AcousticBrainz error: {e}")
            return None
    
    def get_low_level_features(self, recording_mbid):
        """Get low-level acoustic features (BPM, key, etc.)"""
        self._rate_limit()
        
        try:
            url = f"{self.acousticbrainz_api}/{recording_mbid}/low-level"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Low-level features error: {e}")
            return None
    
    def analyze_song(self, song_name, artist=''):
        """
        Full song analysis: search and get all available data
        
        Args:
            song_name: Name of the song
            artist: Artist name
        
        Returns:
            dict with bpm, key, mood, etc. or None
        """
        print(f"🔍 ListenBrainz: Searching for '{song_name}' by '{artist}'")
        
        # Step 1: Try ListenBrainz lookup first
        lb_result = self.lookup_recording(artist, song_name)
        
        recording_mbid = None
        recording_name = song_name
        artist_name = artist
        
        if lb_result:
            recording_mbid = lb_result.get('recording_mbid')
            if lb_result.get('recording_name'):
                recording_name = lb_result['recording_name']
            if lb_result.get('artist_credit_name'):
                artist_name = lb_result['artist_credit_name']
            print(f"   Found via ListenBrainz: {recording_name} - MBID: {recording_mbid}")
        
        # Step 2: If no MBID, search MusicBrainz directly
        if not recording_mbid:
            print(f"   Searching MusicBrainz...")
            mb_result = self.search_musicbrainz(song_name, artist)
            if mb_result:
                recording_mbid = mb_result.get('id')
                recording_name = mb_result.get('title', song_name)
                if mb_result.get('artist-credit'):
                    artist_name = mb_result['artist-credit'][0].get('name', artist)
                print(f"   Found via MusicBrainz: {recording_name} - MBID: {recording_mbid}")
        
        if not recording_mbid:
            print(f"   ❌ Recording not found in MusicBrainz")
            return None
        
        # Step 3: Get acoustic features
        result = {
            'title': recording_name,
            'artist': artist_name,
            'mbid': recording_mbid,
            'source': 'listenbrainz'
        }
        
        # Try to get BPM/key from AcousticBrainz (may be deprecated)
        print(f"   Fetching acoustic features...")
        low_level = self.get_low_level_features(recording_mbid)
        
        if low_level:
            # Extract rhythm info
            rhythm = low_level.get('rhythm', {})
            if 'bpm' in rhythm:
                bpm = rhythm['bpm']
                # Fix common BPM doubling error - if BPM > 150, it might be doubled
                # Most pop/hip-hop/R&B is 70-130 BPM
                if bpm > 150:
                    bpm = bpm / 2
                    print(f"   📊 Adjusted BPM from {rhythm['bpm']} to {bpm} (likely doubled)")
                result['bpm'] = round(bpm, 1)
            
            # Extract tonal info (key)
            tonal = low_level.get('tonal', {})
            if 'key_key' in tonal:
                key_note = tonal['key_key']
                key_scale = tonal.get('key_scale', 'major')
                result['key'] = f"{key_note} {key_scale}"
                result['mode'] = key_scale
            
            # Extract other features
            if 'lowlevel' in low_level:
                ll = low_level['lowlevel']
                if 'average_loudness' in ll:
                    # Convert loudness to energy (rough approximation)
                    loudness = ll['average_loudness']
                    result['energy'] = min(100, max(0, round(loudness * 100, 1)))
            
            result['confidence'] = 0.9
            print(f"   ✅ Got acoustic features: {result.get('bpm')} BPM, {result.get('key')}")
        else:
            print(f"   ⚠️ No acoustic features available (AcousticBrainz may be deprecated)")
            # Set defaults based on metadata lookup
            result['bpm'] = None
            result['key'] = None
            result['confidence'] = 0.5
        
        # Try to get high-level mood/genre from AcousticBrainz
        high_level = self.get_acousticbrainz_data(recording_mbid)
        if high_level:
            hl = high_level.get('highlevel', {})
            
            # Mood
            if 'mood_happy' in hl:
                happy_prob = hl['mood_happy'].get('all', {}).get('happy', 0)
                sad_prob = hl['mood_happy'].get('all', {}).get('sad', 0)
                if happy_prob > sad_prob:
                    result['mood'] = 'happy' if happy_prob > 0.6 else 'neutral'
                else:
                    result['mood'] = 'sad' if sad_prob > 0.6 else 'melancholic'
            
            # Danceability
            if 'danceability' in hl:
                dance_prob = hl['danceability'].get('all', {}).get('danceable', 0.5)
                result['danceability'] = round(dance_prob * 100, 1)
            
            # Genre (if available)
            if 'genre_electronic' in hl:
                genre_probs = hl['genre_electronic'].get('all', {})
                if genre_probs:
                    top_genre = max(genre_probs.items(), key=lambda x: x[1])
                    if top_genre[1] > 0.5:
                        result['genre'] = top_genre[0].title()
        
        # Set default mood if not found
        if 'mood' not in result:
            result['mood'] = self._guess_mood(result)
        
        return result
    
    def _guess_mood(self, data):
        """Guess mood based on available data"""
        bpm = data.get('bpm', 120)
        key = data.get('key', '').lower()
        energy = data.get('energy', 50)
        
        is_minor = 'minor' in key
        
        if bpm and bpm < 90:
            return 'melancholic' if is_minor else 'peaceful'
        elif bpm and bpm > 130:
            return 'intense' if is_minor else 'energetic'
        else:
            return 'emotional' if is_minor else 'uplifting'
    
    def get_similar_recordings(self, recording_mbid, limit=10):
        """
        Get similar recordings based on a seed recording
        
        Args:
            recording_mbid: MusicBrainz Recording ID
            limit: Max results
        
        Returns:
            List of similar recordings
        """
        # ListenBrainz doesn't have a direct similarity endpoint yet
        # This could use their recommendation API in the future
        return []


# Test the client
if __name__ == '__main__':
    # Use token from environment or test token
    token = os.environ.get('LISTENBRAINZ_TOKEN', '2e8002c8-fb62-4c04-aabf-871d625d3cef')
    client = ListenBrainzClient(user_token=token)
    
    if client.is_available():
        print("✅ ListenBrainz client initialized")
        
        # Test searches
        test_songs = [
            ("Shape of You", "Ed Sheeran"),
            ("Tum Hi Ho", "Arijit Singh"),
            ("Blinding Lights", "The Weeknd"),
        ]
        
        for song, artist in test_songs:
            print(f"\n{'='*50}")
            result = client.analyze_song(song, artist)
            if result:
                print(f"\n📊 Result for '{song}':")
                print(f"   Title: {result.get('title')}")
                print(f"   Artist: {result.get('artist')}")
                print(f"   BPM: {result.get('bpm', 'N/A')}")
                print(f"   Key: {result.get('key', 'N/A')}")
                print(f"   Mood: {result.get('mood', 'N/A')}")
                print(f"   Energy: {result.get('energy', 'N/A')}")
            else:
                print(f"❌ No results for '{song}'")
    else:
        print("⚠️ ListenBrainz token not configured")

