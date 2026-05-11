"""
GetSongBPM API Client
Gets accurate BPM and key data from getsongbpm.com API

API: https://getsongbpm.com/api
"""

import os
import requests
import time


class GetSongBPMClient:
    def __init__(self, api_key=None):
        # GetSongBPM API key - get free key at https://getsongbpm.com/api
        self.api_key = api_key or os.environ.get('GETSONGBPM_API_KEY')
        self.api_base = "https://api.getsongbpm.com"
        
        # Rate limiting
        self._last_request_time = 0
        self._min_delay = 1.0
    
    def is_available(self):
        """Check if API is configured"""
        return self.api_key is not None
    
    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed)
        self._last_request_time = time.time()
    
    def search_song(self, query):
        """
        Search for a song
        
        Args:
            query: Search query (song name + artist)
        
        Returns:
            Song data with BPM and key
        """
        if not self.api_key:
            return None
        
        self._rate_limit()
        
        try:
            url = f"{self.api_base}/search/"
            params = {
                'api_key': self.api_key,
                'type': 'song',
                'lookup': query
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('search') and len(data['search']) > 0:
                    song = data['search'][0]
                    return self._parse_song(song)
            
            return None
            
        except Exception as e:
            print(f"GetSongBPM error: {e}")
            return None
    
    def _parse_song(self, song):
        """Parse song data from API response"""
        result = {
            'title': song.get('title', ''),
            'artist': song.get('artist', {}).get('name', ''),
            'source': 'getsongbpm'
        }
        
        # BPM
        if song.get('tempo'):
            result['bpm'] = float(song['tempo'])
        
        # Key
        if song.get('key_of'):
            key = song['key_of']
            # Normalize key format
            if key:
                # Handle formats like "F# Minor" or "C Major"
                result['key'] = key
                result['mode'] = 'minor' if 'minor' in key.lower() else 'major'
        
        # Album
        if song.get('album'):
            result['album'] = song['album'].get('title', '')
        
        result['confidence'] = 0.95
        
        return result


# Alternative: Scrape songbpm.com (no API key needed)
class SongBPMScraper:
    """Scrapes songbpm.com for BPM/key data (no API key required)"""
    
    def __init__(self):
        self.base_url = "https://songbpm.com"
        self._last_request_time = 0
        self._min_delay = 2.0
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
    
    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed)
        self._last_request_time = time.time()
    
    def search_song(self, song_name, artist=''):
        """Search for song BPM and key"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            print("BeautifulSoup not installed")
            return None
        
        self._rate_limit()
        
        try:
            # Search URL
            query = f"{song_name} {artist}".strip().replace(' ', '+')
            search_url = f"{self.base_url}/search?q={query}"
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                print(f"SongBPM search failed: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find first result
            result_link = soup.select_one('a[href*="/song/"]')
            if not result_link:
                return None
            
            # Get song page
            song_url = result_link.get('href')
            if not song_url.startswith('http'):
                song_url = self.base_url + song_url
            
            self._rate_limit()
            response = requests.get(song_url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            result = {
                'source': 'songbpm',
                'confidence': 0.9
            }
            
            # Extract title
            title_el = soup.select_one('h1')
            if title_el:
                result['title'] = title_el.get_text(strip=True)
            
            # Extract BPM
            bpm_el = soup.select_one('[class*="bpm"], [class*="tempo"]')
            if bpm_el:
                import re
                bpm_match = re.search(r'(\d+)', bpm_el.get_text())
                if bpm_match:
                    result['bpm'] = float(bpm_match.group(1))
            
            # Extract key
            key_el = soup.select_one('[class*="key"]')
            if key_el:
                key_text = key_el.get_text(strip=True)
                result['key'] = key_text
                result['mode'] = 'minor' if 'minor' in key_text.lower() else 'major'
            
            return result if result.get('bpm') else None
            
        except Exception as e:
            print(f"SongBPM scraper error: {e}")
            return None

