#!/usr/bin/env python3
"""
HTML5 to Video Converter - Simple Flask Web App
Works anywhere Python runs
"""

from flask import Flask, render_template, request, send_file, jsonify, Response
import os
import tempfile
import zipfile
from pathlib import Path
import shutil

# Import the converter classes from standalone converter module
from converter import HTML5ToVideoConverter, VideoConfig, HTML5Analyzer, FormatCSS

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching

# Add CORS headers for all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST')
    return response


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze uploaded HTML5 file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save temporarily
    temp_dir = tempfile.mkdtemp()

    try:
        file_extension = file.filename.lower().split('.')[-1]

        if file_extension == 'zip':
            temp_zip = os.path.join(temp_dir, 'upload.zip')
            file.save(temp_zip)
        elif file_extension in ['html', 'htm']:
            # Create ZIP from HTML
            temp_html = os.path.join(temp_dir, 'index.html')
            file.save(temp_html)
            temp_zip = os.path.join(temp_dir, 'upload.zip')
            with zipfile.ZipFile(temp_zip, 'w') as zipf:
                zipf.write(temp_html, arcname='index.html')
        else:
            return jsonify({'error': 'Invalid file type'}), 400

        # Extract and analyze
        extract_dir = os.path.join(temp_dir, 'extract')
        os.makedirs(extract_dir)

        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        html_files = list(Path(extract_dir).rglob("*.html"))

        if not html_files:
            return jsonify({'error': 'No HTML files found'}), 400

        main_html = None
        for html_file in html_files:
            if html_file.name.lower() in ['index.html', 'index.htm']:
                main_html = html_file
                break
        if not main_html:
            main_html = html_files[0]

        analyzer = HTML5Analyzer()
        detected = analyzer.analyze_html(str(main_html))

        # Get format recommendation
        auto_width, auto_height, auto_format = FormatCSS.detect_best_format(
            detected['width'], detected['height']
        )

        return jsonify({
            'width': detected['width'],
            'height': detected['height'],
            'fps': detected['fps'],
            'duration': detected['duration'],
            'auto_format': auto_format,
            'auto_width': auto_width,
            'auto_height': auto_height
        })

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.route('/convert', methods=['POST'])
def convert():
    """Convert HTML5 to video"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Get settings from form
    try:
        duration = int(request.form.get('duration', 10))
        target_format = request.form.get('target_format', 'auto')
    except ValueError:
        return jsonify({'error': 'Invalid parameters'}), 400

    temp_dir = tempfile.mkdtemp()

    try:
        # Save file
        file_extension = file.filename.lower().split('.')[-1]

        if file_extension == 'zip':
            temp_zip = os.path.join(temp_dir, 'upload.zip')
            file.save(temp_zip)
        elif file_extension in ['html', 'htm']:
            temp_html = os.path.join(temp_dir, 'index.html')
            file.save(temp_html)
            temp_zip = os.path.join(temp_dir, 'upload.zip')
            with zipfile.ZipFile(temp_zip, 'w') as zipf:
                zipf.write(temp_html, arcname='index.html')
        else:
            return jsonify({'error': 'Invalid file type'}), 400

        # Analyze to get dimensions
        extract_dir = os.path.join(temp_dir, 'extract')
        os.makedirs(extract_dir)

        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        html_files = list(Path(extract_dir).rglob("*.html"))
        if not html_files:
            return jsonify({'error': 'No HTML files found'}), 400

        main_html = None
        for html_file in html_files:
            if html_file.name.lower() in ['index.html', 'index.htm']:
                main_html = html_file
                break
        if not main_html:
            main_html = html_files[0]

        analyzer = HTML5Analyzer()
        detected = analyzer.analyze_html(str(main_html))

        # Create config
        config = VideoConfig(
            width=detected['width'],
            height=detected['height'],
            fps=detected['fps'],
            duration=duration,
            codec="libx264",
            bitrate="10M",
            preset="slow",
            crf=18,
            animation_speed=1.0,
            target_format=target_format
        )

        # Convert
        base_name = os.path.splitext(file.filename)[0]
        output_path = os.path.join(temp_dir, f"{base_name}.mp4")

        converter = HTML5ToVideoConverter()
        success = converter.convert(temp_zip, output_path, config)

        if not success or not os.path.exists(output_path):
            return jsonify({'error': 'Conversion failed', 'log': converter.get_debug_output()}), 500

        # Read video into memory so we can cleanup temp dir
        with open(output_path, 'rb') as f:
            video_data = f.read()

        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)

        # Return video data as blob
        return Response(
            video_data,
            mimetype='video/mp4',
            headers={
                'Content-Disposition': f'attachment; filename="{base_name}.mp4"'
            }
        )

    except Exception as e:
        # Cleanup on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
