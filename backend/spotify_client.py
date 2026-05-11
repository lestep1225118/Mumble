"""
Spotify API Client
Gets song data (BPM, key, energy, etc.) from Spotify's Web API
Uses client credentials flow (no user login required)
"""

import os
import base64
import requests
from urllib.parse import quote


class SpotifyClient:
    def __init__(self, client_id=None, client_secret=None):
        # Default credentials (can be overridden via env vars or parameters)
        default_client_id = '2b152f7d721f4e119f51d468fa919902'
        default_client_secret = '45c1b2e9d45540c2be1efaaab617f7ef'
        
        self.client_id = client_id or os.environ.get('SPOTIFY_CLIENT_ID', default_client_id)
        self.client_secret = client_secret or os.environ.get('SPOTIFY_CLIENT_SECRET', default_client_secret)
        self.token = None
        self.token_url = "https://accounts.spotify.com/api/token"
        self.api_base = "https://api.spotify.com/v1"
        
        # Key mapping from Spotify's pitch class to key name
        # Spotify uses pitch class notation: 0 = C, 1 = C#, etc.
        self.pitch_class_to_key = {
            0: 'C', 1: 'C#', 2: 'D', 3: 'D#', 4: 'E', 5: 'F',
            6: 'F#', 7: 'G', 8: 'G#', 9: 'A', 10: 'A#', 11: 'B'
        }
        
        if self.client_id and self.client_secret:
            self._get_token()
    
    def is_available(self):
        """Check if Spotify API is configured and working"""
        return self.token is not None
    
    def _get_token(self):
        """Get access token using client credentials flow"""
        try:
            auth_str = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_str.encode('utf-8')
            auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {'grant_type': 'client_credentials'}
            
            response = requests.post(self.token_url, headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                self.token = response.json().get('access_token')
                print("✅ Spotify API connected")
            else:
                print(f"⚠️ Spotify auth failed: {response.status_code}")
                self.token = None
                
        except Exception as e:
            print(f"⚠️ Spotify auth error: {e}")
            self.token = None
    
    def _api_request(self, endpoint, params=None):
        """Make an authenticated API request"""
        if not self.token:
            return None
        
        headers = {'Authorization': f'Bearer {self.token}'}
        url = f"{self.api_base}{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                # Token expired, try to refresh
                self._get_token()
                if self.token:
                    headers = {'Authorization': f'Bearer {self.token}'}
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                    if response.status_code == 200:
                        return response.json()
            
            return None
            
        except Exception as e:
            print(f"Spotify API error: {e}")
            return None
    
    def search_track(self, query, limit=1):
        """
        Search for a track on Spotify
        
        Args:
            query: Search query (song name + artist)
            limit: Maximum number of results
        
        Returns:
            Track data or None
        """
        params = {
            'q': query,
            'type': 'track',
            'limit': limit
        }
        
        result = self._api_request('/search', params)
        
        if result and result.get('tracks', {}).get('items'):
            return result['tracks']['items'][0]
        
        return None
    
    def get_audio_features(self, track_id):
        """
        Get audio features for a track
        
        Returns:
            dict with tempo, key, mode, energy, danceability, etc.
        """
        result = self._api_request(f'/audio-features/{track_id}')
        return result
    
    def analyze_song(self, song_name, artist=''):
        """
        Search for a song and get its audio analysis
        
        Args:
            song_name: Name of the song
            artist: Artist name (optional but recommended)
        
        Returns:
            dict with bpm, key, energy, mood, etc. or None
        """
        query = f"{song_name} {artist}".strip()
        
        # Search for the track
        track = self.search_track(query)
        if not track:
            print(f"⚠️ Spotify: Track not found for '{query}'")
            return None
        
        track_id = track['id']
        track_name = track['name']
        track_artist = track['artists'][0]['name'] if track['artists'] else 'Unknown'
        
        # Get audio features
        features = self.get_audio_features(track_id)
        if not features:
            print(f"⚠️ Spotify: No audio features for '{track_name}'")
            return None
        
        # Convert Spotify's key notation to standard
        key_note = self.pitch_class_to_key.get(features.get('key', 0), 'C')
        mode = 'major' if features.get('mode', 1) == 1 else 'minor'
        key = f"{key_note} {mode}"
        
        # Convert values to percentages
        energy = round(features.get('energy', 0.5) * 100, 1)
        danceability = round(features.get('danceability', 0.5) * 100, 1)
        valence = round(features.get('valence', 0.5) * 100, 1)  # Musical positivity
        
        # Determine mood based on valence and energy
        mood = self._determine_mood(valence, energy, mode)
        
        return {
            'title': track_name,
            'artist': track_artist,
            'bpm': round(features.get('tempo', 120), 1),
            'key': key,
            'mode': mode,
            'energy': energy,
            'danceability': danceability,
            'valence': valence,
            'acousticness': round(features.get('acousticness', 0) * 100, 1),
            'instrumentalness': round(features.get('instrumentalness', 0) * 100, 1),
            'liveness': round(features.get('liveness', 0) * 100, 1),
            'speechiness': round(features.get('speechiness', 0) * 100, 1),
            'duration': features.get('duration_ms', 0) // 1000,
            'mood': mood,
            'spotify_id': track_id,
            'source': 'spotify',
            'confidence': 0.99
        }
    
    def _determine_mood(self, valence, energy, mode):
        """Determine mood based on valence, energy, and mode"""
        if valence > 60:
            if energy > 60:
                return 'euphoric' if valence > 75 else 'energetic'
            else:
                return 'happy' if valence > 75 else 'peaceful'
        elif valence > 40:
            if energy > 60:
                return 'powerful'
            else:
                return 'chill' if mode == 'major' else 'emotional'
        else:
            if energy > 60:
                return 'intense' if mode == 'minor' else 'dramatic'
            else:
                return 'sad' if valence < 25 else 'melancholic'
    
    def get_recommendations(self, seed_track_id=None, target_bpm=None, target_key=None, limit=10):
        """
        Get track recommendations from Spotify
        
        Args:
            seed_track_id: Spotify track ID to use as seed
            target_bpm: Target tempo
            target_key: Target key (0-11 for pitch class)
            limit: Number of recommendations
        
        Returns:
            List of recommended tracks
        """
        params = {'limit': limit}
        
        if seed_track_id:
            params['seed_tracks'] = seed_track_id
        
        if target_bpm:
            params['target_tempo'] = target_bpm
            params['min_tempo'] = target_bpm * 0.9
            params['max_tempo'] = target_bpm * 1.1
        
        if target_key is not None:
            params['target_key'] = target_key
        
        result = self._api_request('/recommendations', params)
        
        if result and result.get('tracks'):
            recommendations = []
            for track in result['tracks']:
                recommendations.append({
                    'title': track['name'],
                    'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                    'spotify_id': track['id'],
                    'preview_url': track.get('preview_url'),
                    'source': 'spotify'
                })
            return recommendations
        
        return []


# Test the client
if __name__ == '__main__':
    client = SpotifyClient()
    
    if client.is_available():
        # Test search
        result = client.analyze_song("Shape of You", "Ed Sheeran")
        if result:
            print(f"\n✅ Found: {result['title']} by {result['artist']}")
            print(f"   BPM: {result['bpm']}")
            print(f"   Key: {result['key']}")
            print(f"   Energy: {result['energy']}%")
            print(f"   Mood: {result['mood']}")
        else:
            print("❌ Song not found")
    else:
        print("⚠️ Spotify API not configured")
        print("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")
        print("\nTo get credentials:")
        print("1. Go to https://developer.spotify.com/dashboard")
        print("2. Create an app")
        print("3. Copy Client ID and Client Secret")

