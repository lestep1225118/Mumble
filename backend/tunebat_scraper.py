"""
Tunebat Scraper Module
Scrapes song information (BPM, key, energy, etc.) from Tunebat.com
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import quote_plus


class TunebatScraper:
    def __init__(self):
        self.base_url = "https://tunebat.com"
        self.search_url = "https://tunebat.com/Search"
        
        # Rotate user agents to avoid blocks
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        ]
        
        self.session = requests.Session()
        self._last_request_time = 0
        self._min_delay = 1.5  # Minimum seconds between requests
    
    def _get_headers(self):
        """Get request headers with random user agent"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
    
    def _rate_limit(self):
        """Ensure we don't make requests too quickly"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed + random.uniform(0.1, 0.5))
        self._last_request_time = time.time()
    
    def search_song(self, query):
        """
        Search for a song on Tunebat and return its musical characteristics
        
        Args:
            query: Search query (song name + artist)
        
        Returns:
            dict with bpm, key, energy, danceability, etc. or None if not found
        """
        try:
            self._rate_limit()
            
            # Search Tunebat
            search_params = {'q': query}
            response = self.session.get(
                self.search_url,
                params=search_params,
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"Tunebat search failed with status {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find search results
            results = self._parse_search_results(soup)
            
            if not results:
                print(f"No results found for: {query}")
                return None
            
            # Get the first (best) result
            best_match = results[0]
            
            # Optionally get more details from the song page
            if best_match.get('url'):
                detailed = self._get_song_details(best_match['url'])
                if detailed:
                    best_match.update(detailed)
            
            return best_match
            
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Scraping error: {e}")
            return None
    
    def _parse_search_results(self, soup):
        """Parse search results page for song data"""
        results = []
        
        # Tunebat shows results in a table or card format
        # Try to find song entries
        
        # Method 1: Look for song cards/rows with data attributes
        song_elements = soup.select('[class*="Track"], [class*="song"], [class*="result"]')
        
        if not song_elements:
            # Method 2: Look for table rows
            song_elements = soup.select('tr[class*="track"], div[class*="track"]')
        
        if not song_elements:
            # Method 3: Look for any element containing BPM data
            song_elements = soup.find_all(lambda tag: tag.name in ['div', 'tr', 'article'] 
                                          and tag.find(string=re.compile(r'\d+\s*BPM', re.I)))
        
        for element in song_elements[:10]:  # Limit to first 10 results
            song_data = self._extract_song_data(element)
            if song_data and song_data.get('title'):
                results.append(song_data)
        
        # If structured parsing failed, try regex-based extraction
        if not results:
            results = self._regex_extract(soup)
        
        return results
    
    def _extract_song_data(self, element):
        """Extract song data from a DOM element"""
        data = {}
        
        try:
            # Get text content
            text = element.get_text(separator=' ', strip=True)
            
            # Extract title and artist
            title_el = element.select_one('[class*="title"], [class*="name"], h3, h4, a')
            if title_el:
                data['title'] = title_el.get_text(strip=True)
            
            artist_el = element.select_one('[class*="artist"], [class*="subtitle"]')
            if artist_el:
                data['artist'] = artist_el.get_text(strip=True)
            
            # Extract BPM
            bpm_match = re.search(r'(\d{2,3})\s*BPM', text, re.I)
            if bpm_match:
                data['bpm'] = int(bpm_match.group(1))
            
            # Extract Key
            key_pattern = r'\b([A-G][#♯b♭]?)\s*(major|minor|maj|min|m)?\b'
            key_match = re.search(key_pattern, text, re.I)
            if key_match:
                note = key_match.group(1).replace('♯', '#').replace('♭', 'b')
                mode = key_match.group(2) or 'major'
                if mode.lower() in ['m', 'min', 'minor']:
                    mode = 'minor'
                else:
                    mode = 'major'
                data['key'] = f"{note} {mode}"
            
            # Extract Camelot notation (e.g., "8B", "11A")
            camelot_match = re.search(r'\b(\d{1,2}[AB])\b', text)
            if camelot_match:
                data['camelot'] = camelot_match.group(1)
                # Convert Camelot to key if key not found
                if 'key' not in data:
                    data['key'] = self._camelot_to_key(camelot_match.group(1))
            
            # Extract energy/danceability percentages
            energy_match = re.search(r'energy[:\s]*(\d{1,3})%?', text, re.I)
            if energy_match:
                data['energy'] = int(energy_match.group(1))
            
            dance_match = re.search(r'danc\w*[:\s]*(\d{1,3})%?', text, re.I)
            if dance_match:
                data['danceability'] = int(dance_match.group(1))
            
            # Get link to song page
            link = element.select_one('a[href*="/Info/"]')
            if link and link.get('href'):
                href = link['href']
                if not href.startswith('http'):
                    href = self.base_url + href
                data['url'] = href
            
        except Exception as e:
            print(f"Error extracting song data: {e}")
        
        return data
    
    def _regex_extract(self, soup):
        """Fallback: Use regex to extract data from page text"""
        results = []
        text = soup.get_text()
        
        # Look for patterns like "Song Title - Artist | 120 BPM | C major"
        pattern = r'(.+?)\s*[-–—]\s*(.+?)\s*[|｜]\s*(\d{2,3})\s*BPM\s*[|｜]?\s*([A-G][#b]?\s*(?:major|minor|m)?)?'
        
        matches = re.findall(pattern, text, re.I)
        
        for match in matches[:5]:
            results.append({
                'title': match[0].strip(),
                'artist': match[1].strip(),
                'bpm': int(match[2]),
                'key': match[3].strip() if match[3] else None
            })
        
        return results
    
    def _get_song_details(self, url):
        """Get detailed information from a song's dedicated page"""
        try:
            self._rate_limit()
            
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            
            details = {}
            
            # Extract all available metrics
            metrics = {
                'energy': r'energy[:\s]*(\d{1,3})',
                'danceability': r'danc\w*[:\s]*(\d{1,3})',
                'valence': r'valence[:\s]*(\d{1,3})',
                'acousticness': r'acoustic\w*[:\s]*(\d{1,3})',
                'instrumentalness': r'instrumental\w*[:\s]*(\d{1,3})',
                'liveness': r'live\w*[:\s]*(\d{1,3})',
                'speechiness': r'speech\w*[:\s]*(\d{1,3})',
                'popularity': r'popularity[:\s]*(\d{1,3})',
            }
            
            for metric, pattern in metrics.items():
                match = re.search(pattern, text, re.I)
                if match:
                    details[metric] = int(match.group(1))
            
            # Extract duration
            duration_match = re.search(r'(\d+):(\d{2})', text)
            if duration_match:
                minutes = int(duration_match.group(1))
                seconds = int(duration_match.group(2))
                details['duration'] = minutes * 60 + seconds
            
            # Determine mood based on valence and energy
            if 'valence' in details and 'energy' in details:
                details['mood'] = self._determine_mood(details['valence'], details['energy'])
            
            return details
            
        except Exception as e:
            print(f"Error getting song details: {e}")
            return None
    
    def _camelot_to_key(self, camelot):
        """Convert Camelot notation to standard key"""
        camelot_map = {
            '1A': 'G# minor', '1B': 'B major',
            '2A': 'D# minor', '2B': 'F# major',
            '3A': 'A# minor', '3B': 'C# major',
            '4A': 'F minor', '4B': 'G# major',
            '5A': 'C minor', '5B': 'D# major',
            '6A': 'G minor', '6B': 'A# major',
            '7A': 'D minor', '7B': 'F major',
            '8A': 'A minor', '8B': 'C major',
            '9A': 'E minor', '9B': 'G major',
            '10A': 'B minor', '10B': 'D major',
            '11A': 'F# minor', '11B': 'A major',
            '12A': 'C# minor', '12B': 'E major',
        }
        return camelot_map.get(camelot.upper(), 'C major')
    
    def _determine_mood(self, valence, energy):
        """Determine mood based on valence and energy"""
        if valence > 60:
            if energy > 60:
                return 'energetic'
            else:
                return 'happy'
        else:
            if energy > 60:
                return 'intense'
            else:
                return 'melancholic'
    
    def search_similar_songs(self, bpm, key, limit=20):
        """
        Search for songs with similar BPM and key
        
        Args:
            bpm: Target BPM
            key: Target key (e.g., "C major")
            limit: Maximum results to return
        
        Returns:
            List of songs with similar characteristics
        """
        try:
            # Tunebat has browse pages for BPM and key
            # Try to find songs in the same key and BPM range
            
            # Parse key
            key_parts = key.replace(' ', '').lower()
            
            # Build search URL for key
            search_query = f"{key} {bpm} bpm"
            
            results = []
            
            # Search Tunebat
            self._rate_limit()
            response = self.session.get(
                self.search_url,
                params={'q': search_query},
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = self._parse_search_results(soup)
            
            return results[:limit]
            
        except Exception as e:
            print(f"Error searching similar songs: {e}")
            return []


# Test the scraper
if __name__ == '__main__':
    scraper = TunebatScraper()
    
    # Test search
    test_queries = [
        "Tum Hi Ho Arijit Singh",
        "Shape of You Ed Sheeran",
        "Blinding Lights The Weeknd"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Searching: {query}")
        result = scraper.search_song(query)
        if result:
            print(f"Found: {result.get('title', 'Unknown')} by {result.get('artist', 'Unknown')}")
            print(f"BPM: {result.get('bpm', 'N/A')}")
            print(f"Key: {result.get('key', 'N/A')}")
            print(f"Energy: {result.get('energy', 'N/A')}")
        else:
            print("No results found")

