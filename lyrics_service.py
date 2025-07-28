import requests
import re
import logging
import asyncio
from typing import Optional, Dict
from urllib.parse import quote

logger = logging.getLogger(__name__)

class LyricsService:
    def __init__(self, genius_token: str):
        self.genius_token = genius_token
        self.base_url = "https://api.genius.com"
        self.headers = {
            "Authorization": f"Bearer {self.genius_token}",
            "User-Agent": "SimpleMusicBot/1.0"
        }
    
    def clean_title(self, title: str) -> str:
        """Clean video title for better search results"""
        # Remove common patterns from YouTube titles
        patterns = [
            r'\(Official.*?\)',
            r'\[Official.*?\]',
            r'\(Lyrics.*?\)',
            r'\[Lyrics.*?\]',
            r'\(Audio.*?\)',
            r'\[Audio.*?\]',
            r'\(Video.*?\)',
            r'\[Video.*?\]',
            r'\(HD.*?\)',
            r'\[HD.*?\]',
            r'\(4K.*?\)',
            r'\[4K.*?\]',
            r'- Topic',
            r'ft\..*',
            r'feat\..*',
            r'featuring.*',
        ]
        
        cleaned = title
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove extra whitespace and common separators
        cleaned = re.sub(r'\s*[-|•]\s*', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    async def search_lyrics(self, song_title: str, artist: str = None) -> Optional[Dict]:
        """Search for lyrics on Genius"""
        try:
            # Clean the song title
            clean_title = self.clean_title(song_title)
            
            # Create search query
            if artist:
                search_query = f"{clean_title} {artist}"
            else:
                search_query = clean_title
            
            logger.info(f"Searching lyrics for: {search_query}")
            
            # Search for the song
            search_url = f"{self.base_url}/search"
            params = {"q": search_query}
            
            # Run in thread to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.get(search_url, headers=self.headers, params=params, timeout=10)
            )
            response.raise_for_status()
            
            search_data = response.json()
            
            if not search_data.get("response", {}).get("hits"):
                logger.info("No search results found")
                return None
            
            # Get the first result
            first_hit = search_data["response"]["hits"][0]["result"]
            song_id = first_hit["id"]
            song_title_result = first_hit["title"]
            artist_name = first_hit["primary_artist"]["name"]
            song_url = first_hit["url"]
            
            logger.info(f"Found song: {song_title_result} by {artist_name}")
            
            # Get song details (lyrics URL)
            song_url_api = f"{self.base_url}/songs/{song_id}"
            song_response = await loop.run_in_executor(
                None,
                lambda: requests.get(song_url_api, headers=self.headers, timeout=10)
            )
            song_response.raise_for_status()
            
            song_data = song_response.json()
            song_info = song_data["response"]["song"]
            
            return {
                "title": song_title_result,
                "artist": artist_name,
                "url": song_url,
                "genius_id": song_id,
                "album": song_info.get("album", {}).get("name") if song_info.get("album") else None,
                "release_date": song_info.get("release_date_for_display"),
                "description": song_info.get("description", {}).get("plain") if song_info.get("description") else None
            }
            
        except requests.RequestException as e:
            logger.error(f"Request error while searching lyrics: {e}")
            return None
        except Exception as e:
            logger.error(f"Error searching lyrics: {e}")
            return None
    
    def format_lyrics_info(self, lyrics_info: Dict) -> str:
        """Format lyrics information for display"""
        title = lyrics_info["title"]
        artist = lyrics_info["artist"]
        url = lyrics_info["url"]
        album = lyrics_info.get("album", "Unknown Album")
        release_date = lyrics_info.get("release_date", "Unknown")
        
        lyrics_text = f"""
🎵 **{title}**
👤 **Artist:** {artist}
💿 **Album:** {album}
📅 **Released:** {release_date}

🔗 **View Full Lyrics:** [Genius.com]({url})

💡 **Note:** Click the link above to view the complete lyrics on Genius.com
        """
        
        return lyrics_text.strip()
