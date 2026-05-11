# 🎧 Mumble - DJ Mixing Assistant

A web application that helps DJs find the perfect songs to mix together. Upload or search for a song, analyze its musical characteristics, and get recommendations for compatible tracks based on BPM, key, mood, and your custom prompts.

![Mumble Screenshot](https://via.placeholder.com/800x400/0a0a0f/00d4ff?text=Mumble+DJ+Mixing+Assistant)

## ✨ Features

- **Audio Analysis**: Analyze songs for BPM, musical key, energy, and mood
- **Multiple Input Methods**: Upload audio files, paste URLs (YouTube/Spotify/SoundCloud), or search by song name
- **Smart Key Compatibility**: Automatically calculates harmonically compatible keys for mixing:
  - Same key
  - Relative major/minor
  - One semitone up/down
  - Perfect fifth relationships
- **AI-Powered Recommendations**: Describe what you're looking for in natural language
- **Beautiful UI**: Dark, atmospheric design with vinyl/DJ aesthetics

## 🎵 Key Compatibility Logic

The app follows DJ-friendly harmonic mixing rules. For example, if your source song is in **C major**, compatible keys include:

| Key | Relationship |
|-----|--------------|
| C major | Same key |
| A minor | Relative minor |
| G# minor | Relative minor -1 semitone |
| A# minor | Relative minor +1 semitone |
| B major | Source -1 semitone |
| C# major | Source +1 semitone |
| G major | Perfect fifth down |
| F major | Perfect fourth |

## 🌐 Data Sources

### 🎵 ListenBrainz / MusicBrainz (Primary - No Setup Required!)
The app uses the **ListenBrainz API** combined with **MusicBrainz** and **AcousticBrainz** to get real song data:
- BPM (tempo) from acoustic analysis
- Musical key and mode
- Energy levels
- Song metadata (title, artist, album)

This works out of the box - no API keys needed!

**How it works:**
1. Searches ListenBrainz for the song → Gets MusicBrainz Recording ID
2. Fetches acoustic features from AcousticBrainz → BPM, key, energy
3. Returns accurate data for millions of songs

### 🎧 Spotify API (Optional Backup)
If you want to use Spotify as an additional source:
1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Create an app and get Client ID + Secret
3. Set environment variables:
   ```powershell
   $env:SPOTIFY_CLIENT_ID = "your_client_id"
   $env:SPOTIFY_CLIENT_SECRET = "your_client_secret"
   ```

### Built-in Database (Last Resort)
If external APIs fail, the app falls back to a built-in database of ~40 popular songs.

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone or download the project**
   ```bash
   cd Mumble
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   > **Note**: `librosa` installation may take a few minutes as it includes audio processing libraries.

4. **Run the application**
   ```bash
   cd backend
   python app.py
   ```

5. **Open in browser**
   Navigate to [http://localhost:5000](http://localhost:5000)

## 📁 Project Structure

```
Mumble/
├── backend/
│   ├── app.py              # Flask web server
│   ├── audio_analyzer.py   # BPM, key, mood detection
│   ├── key_compatibility.py # Harmonic mixing rules
│   └── song_recommender.py  # AI-powered recommendations
├── frontend/
│   ├── index.html          # Main HTML page
│   ├── styles.css          # Dark DJ-themed styles
│   └── app.js              # Frontend logic
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🎛️ Usage

### Step 1: Add Your Track
Choose one of three input methods:
- **Upload**: Drag and drop or click to upload MP3, WAV, FLAC, OGG, M4A, or AAC files
- **Link**: Paste a YouTube, Spotify, or SoundCloud URL
- **Search**: Enter the song name and artist

### Step 2: Analyze
Click "Analyze Track" to detect:
- **BPM**: Beats per minute
- **Key**: Musical key (e.g., C major, A minor)
- **Energy**: Intensity level (0-100%)
- **Mood**: Emotional character (romantic, energetic, sad, etc.)

### Step 3: Find Matches
Describe what you're looking for using natural language:
- *"Find an English pop song with similar romantic vibe"*
- *"Find an EDM track that would mix well for a club set"*
- *"Find a Hindi Bollywood song with similar feel"*

### Step 4: Review Results
Browse recommended tracks sorted by compatibility score. Each result shows:
- Key and BPM compatibility
- Mood and energy match
- Reasons for recommendation

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI-enhanced recommendations | Optional |

Set environment variables before running:
```bash
# Windows
set OPENAI_API_KEY=your-key-here

# macOS/Linux
export OPENAI_API_KEY=your-key-here
```

### Optional Features

**Without librosa**: The app will work but will use database lookups instead of actual audio analysis for uploaded files.

**Without OpenAI**: Recommendations work without AI, using rule-based matching. AI enhances recommendations with natural language explanations.

## 🎨 Customization

### Adding More Songs to Database

Edit `backend/song_recommender.py` and add entries to `SONG_DATABASE`:

```python
{
    "title": "Song Title",
    "artist": "Artist Name",
    "bpm": 120,
    "key": "A minor",
    "mood": "energetic",
    "genre": "Pop",
    "language": "English",
    "energy": 75
}
```

### Modifying Key Compatibility

Edit `backend/key_compatibility.py` to adjust which keys are considered compatible for mixing.

## 🛠️ API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Analyze a song (file upload, URL, or name) |
| `/api/recommend` | POST | Get song recommendations |
| `/api/compatible-keys/<key>` | GET | Get compatible keys for a given key |
| `/api/health` | GET | Health check |

## 🤝 Contributing

Contributions are welcome! Ideas for improvement:
- Integration with Spotify/YouTube APIs for real metadata
- Actual audio analysis for URL sources
- More sophisticated AI prompts
- User accounts and saved playlists
- Waveform visualization

## 📄 License

MIT License - feel free to use, modify, and distribute.

---

Built with 💜 for DJs who love seamless transitions 🎧

