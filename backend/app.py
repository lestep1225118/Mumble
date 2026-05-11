"""
Mumble - DJ Mixing Assistant Backend
Analyzes songs and recommends compatible tracks for mixing
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import tempfile
import requests
from werkzeug.utils import secure_filename
from audio_analyzer import AudioAnalyzer
from key_compatibility import KeyCompatibility
from song_recommender import SongRecommender

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Configuration
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Initialize components
analyzer = AudioAnalyzer()
key_compat = KeyCompatibility()
recommender = SongRecommender()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_pitch_semitone_range(value, default=1):
    try:
        r = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, min(r, 11))


def parse_include_fifths(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ('false', '0', 'no', 'off', ''):
        return False
    if s in ('true', '1', 'yes', 'on'):
        return True
    return default


@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze_song():
    """
    Analyze a song from file upload or URL
    Returns BPM, key, mood, energy, and other characteristics
    """
    try:
        analysis_result = None
        
        # Check if file was uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Analyze the audio file
                analysis_result = analyzer.analyze_file(filepath)
                analysis_result['source'] = 'upload'
                analysis_result['filename'] = filename
                
                # Clean up temp file
                try:
                    os.remove(filepath)
                except:
                    pass
        
        # Check if URL was provided
        elif request.json and 'url' in request.json:
            url = request.json['url']
            analysis_result = analyzer.analyze_url(url)
            analysis_result['source'] = 'url'
            analysis_result['url'] = url
        
        # Check if song info was provided directly (for lookup)
        elif request.json and 'song_name' in request.json:
            song_name = request.json['song_name']
            artist = request.json.get('artist', '')
            analysis_result = analyzer.lookup_song(song_name, artist)
            analysis_result['source'] = 'lookup'
        
        if analysis_result:
            pitch_range = 1
            include_fifths = True
            if request.json:
                pitch_range = parse_pitch_semitone_range(
                    request.json.get('pitch_semitone_range', 1), 1
                )
                include_fifths = parse_include_fifths(
                    request.json.get('include_fifths', True), True
                )
            elif request.form:
                pitch_range = parse_pitch_semitone_range(
                    request.form.get('pitch_semitone_range', 1), 1
                )
                include_fifths = parse_include_fifths(
                    request.form.get('include_fifths', 'true'), True
                )

            if 'key' in analysis_result:
                analysis_result['compatible_keys'] = key_compat.get_compatible_keys(
                    analysis_result['key'],
                    pitch_semitone_range=pitch_range,
                    include_fifths=include_fifths,
                )
                analysis_result['pitch_semitone_range'] = pitch_range
                analysis_result['include_fifths'] = include_fifths
            
            return jsonify({
                'success': True,
                'analysis': analysis_result
            })
        
        return jsonify({
            'success': False,
            'error': 'No valid input provided. Please upload a file or provide a URL.'
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/recommend', methods=['POST'])
def recommend_songs():
    """
    Get song recommendations based on analysis and user prompt
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Get the source song analysis
        source_analysis = data.get('analysis', {})
        prompt = data.get('prompt', '')
        
        if not source_analysis:
            return jsonify({
                'success': False,
                'error': 'No source song analysis provided'
            }), 400
        
        pitch_range = parse_pitch_semitone_range(
            data.get('pitch_semitone_range',
                     source_analysis.get('pitch_semitone_range', 1)), 1
        )
        include_fifths = parse_include_fifths(
            data.get('include_fifths', source_analysis.get('include_fifths', True)), True
        )

        compatible_keys = []
        if 'key' in source_analysis:
            compatible_keys = key_compat.get_compatible_keys(
                source_analysis['key'],
                pitch_semitone_range=pitch_range,
                include_fifths=include_fifths,
            )
        
        # Get recommendations
        recommendations = recommender.get_recommendations(
            source_analysis=source_analysis,
            prompt=prompt,
            compatible_keys=compatible_keys
        )
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'filters_applied': {
                'source_key': source_analysis.get('key'),
                'compatible_keys': compatible_keys,
                'source_bpm': source_analysis.get('bpm'),
                'prompt': prompt,
                'pitch_semitone_range': pitch_range,
                'include_fifths': include_fifths,
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/compatible-keys/<path:key>', methods=['GET'])
def get_compatible_keys_route(key):
    """
    Get all keys compatible for mixing with the given key.
    Query: pitch_semitone_range (0–11, default 1), include_fifths (default true).
    """
    try:
        pitch_range = parse_pitch_semitone_range(
            request.args.get('pitch_semitone_range', 1), 1
        )
        include_fifths = parse_include_fifths(
            request.args.get('include_fifths', 'true'), True
        )

        compatible = key_compat.get_compatible_keys(
            key, pitch_semitone_range=pitch_range, include_fifths=include_fifths
        )
        explanation = key_compat.explain_compatibility(
            key, pitch_semitone_range=pitch_range, include_fifths=include_fifths
        )

        return jsonify({
            'success': True,
            'source_key': key,
            'compatible_keys': compatible,
            'explanation': explanation,
            'pitch_semitone_range': pitch_range,
            'include_fifths': include_fifths,
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'Mumble DJ Assistant'})


if __name__ == '__main__':
    print("🎵 Starting Mumble DJ Mixing Assistant...")
    print("📍 Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)

