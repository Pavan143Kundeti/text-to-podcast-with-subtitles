import pyttsx3
import srt
import time
import re
from pathlib import Path
from datetime import timedelta
from pydub import AudioSegment
import os
import random
import requests
from flask import Flask, request, send_from_directory, jsonify, render_template_string
import threading

SCRIPT_FILE = 'script.txt'
AUDIO_FILE = 'output.wav'
SRT_FILE = 'subtitles.srt'
TEMP_DIR = 'temp_audio'

WORDS_PER_SECOND = 2.0
SILENCE_BETWEEN = 0.7  # seconds

SPEAKER_VOICES = {
    'A': None,
    'B': None
}

def get_engine():
    engine = pyttsx3.init()
    return engine

def get_voices():
    engine = get_engine()
    voices = engine.getProperty('voices')
    return voices

def parse_script(script_path):
    lines = []
    current_speaker = None
    with open(script_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Match 'Speaker A:', 'Speaker A (Host):', etc.
            m = re.match(r'Speaker ([A-Z])(?:\s*\(.*?\))?:\s*', line)
            if m:
                current_speaker = m.group(1)
                # Check if the rest of the line has text
                rest = line[m.end():].strip()
                if rest:
                    # Remove surrounding quotes if present
                    if rest.startswith('"') and rest.endswith('"'):
                        rest = rest[1:-1]
                    lines.append((current_speaker, rest))
                continue
            # If line is just quoted text, assign to last speaker
            if current_speaker and line:
                text = line
                if text.startswith('"') and text.endswith('"'):
                    text = text[1:-1]
                lines.append((current_speaker, text))
    return lines

def generate_line_audio(text, voice_id, out_path):
    engine = get_engine()
    engine.setProperty('voice', voice_id)
    engine.save_to_file(text, out_path)
    engine.runAndWait()

def generate_all_audio(lines):
    voices = get_voices()
    if len(voices) > 1:
        SPEAKER_VOICES['A'] = voices[0].id
        SPEAKER_VOICES['B'] = voices[1].id
    else:
        SPEAKER_VOICES['A'] = voices[0].id
        SPEAKER_VOICES['B'] = voices[0].id
    Path(TEMP_DIR).mkdir(exist_ok=True)
    audio_files = []
    for idx, (speaker, text) in enumerate(lines):
        out_file = f"{TEMP_DIR}/line_{idx}.wav"
        generate_line_audio(text, SPEAKER_VOICES[speaker], out_file)
        audio_files.append(out_file)
    return audio_files

def concatenate_audio(audio_files, out_path):
    combined = AudioSegment.empty()
    silence = AudioSegment.silent(duration=int(SILENCE_BETWEEN * 1000))
    for idx, file in enumerate(audio_files):
        seg = AudioSegment.from_wav(file)
        combined += seg
        if idx < len(audio_files) - 1:
            combined += silence
    combined.export(out_path, format="wav")

def generate_srt(lines, audio_files, srt_path):
    subs = []
    start = 0.0
    idx = 1
    for (speaker, text), audio_file in zip(lines, audio_files):
        seg = AudioSegment.from_wav(audio_file)
        duration = seg.duration_seconds
        end = start + duration
        subs.append(srt.Subtitle(index=idx,
                                 start=timedelta(seconds=start),
                                 end=timedelta(seconds=end),
                                 content=f"{speaker}: {text}"))
        start = end + SILENCE_BETWEEN
        idx += 1
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(srt.compose(subs))

def cleanup_temp():
    import shutil
    if Path(TEMP_DIR).exists():
        shutil.rmtree(TEMP_DIR)

def generate_template_script(topic, out_path):
    # Simple offline template-based podcast script
    intros = [
        f"Welcome to our podcast! Today we're talking about {topic}.",
        f"Hello and welcome! Our topic today is {topic}.",
        f"Hi listeners! Let's dive into {topic}."
    ]
    a_open = random.choice(intros)
    b_open = f"Thanks for having me! {topic.capitalize()} is such an important subject."
    a_q = f"So, what do you think is the biggest challenge about {topic}?"
    b_a = f"Great question! I think the biggest challenge is public awareness and action."
    a_follow = f"That's true. How can people contribute to solving issues around {topic}?"
    b_follow = f"People can start by educating themselves and making small changes in their daily lives."
    a_close = f"Wonderful advice! Any final thoughts on {topic}?"
    b_close = f"Just that every little bit helps. Thanks for discussing this with me!"
    lines = [
        f"Speaker A: {a_open}",
        f"Speaker B: {b_open}",
        f"Speaker A: {a_q}",
        f"Speaker B: {b_a}",
        f"Speaker A: {a_follow}",
        f"Speaker B: {b_follow}",
        f"Speaker A: {a_close}",
        f"Speaker B: {b_close}"
    ]
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Generated offline podcast script for topic '{topic}' in {out_path}")

def call_gemini_api(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': 'AIzaSyAJh6lRVXtwEt64x1XAIKC3zBx-NifTEbI'
    }
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        # Extract the text from the response
        try:
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            return str(result)
    else:
        return f"Error: {response.status_code} {response.text}"

def generate_gemini_podcast_script(topic, out_path):
    prompt = (
        f"Generate a podcast-like discussion between two speakers (Speaker A and Speaker B) about '{topic}'. "
        "Format each line as 'Speaker A: ...' or 'Speaker B: ...', and make it sound like a real conversation. "
        "Keep it concise (6-10 exchanges)."
    )
    print("Requesting Gemini to generate podcast script...")
    script = call_gemini_api(prompt)
    print("Gemini API response for script:", script)
    # Write the script to the file
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(script.strip())
    print(f"Generated Gemini podcast script for topic '{topic}' in {out_path}")

def main():
    prompt = "Explain how AI works in a few words"
    print("Prompting Gemini API...")
    gemini_response = call_gemini_api(prompt)
    print("Gemini API response:", gemini_response)
    topic = input("Enter a podcast topic (or leave blank to use existing script.txt): ").strip()
    if topic:
        generate_gemini_podcast_script(topic, SCRIPT_FILE)
    lines = parse_script(SCRIPT_FILE)
    audio_files = generate_all_audio(lines)
    concatenate_audio(audio_files, AUDIO_FILE)
    generate_srt(lines, audio_files, SRT_FILE)
    cleanup_temp()
    print(f"Generated {AUDIO_FILE} and {SRT_FILE}")

app = Flask(__name__)

@app.route('/')
def index():
    # Serve a simple HTML page with topic input, file upload, audio, and subtitles
    return render_template_string(r'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Podcast Generator</title>
      <link rel="stylesheet" href="/style.css">
    </head>
    <body>
      <h1>Podcast Generator</h1>
      <form id="topicForm" enctype="multipart/form-data">
        <input type="text" id="topic" name="topic" placeholder="Enter your topic">
        <span style="margin:0 1em;">or</span>
        <input type="file" id="scriptFile" name="scriptFile" accept=".txt">
        <button type="submit">Generate Podcast</button>
      </form>
      <div id="status"></div>
      <pre id="scriptBox" style="background:#f4f4f4;padding:1em;border-radius:8px;max-width:700px;margin:2em auto;white-space:pre-wrap;"></pre>
      <audio id="audio" controls style="display:none;">
        <source id="audioSource" src="" type="audio/wav">
        Your browser does not support the audio element.
      </audio>
      <div id="subtitles"></div>
      <script>
        document.getElementById('topicForm').onsubmit = async function(e) {
          e.preventDefault();
          const topic = document.getElementById('topic').value;
          const fileInput = document.getElementById('scriptFile');
          const file = fileInput.files[0];
          document.getElementById('status').textContent = 'Generating podcast...';
          document.getElementById('audio').style.display = 'none';
          document.getElementById('subtitles').textContent = '';
          document.getElementById('scriptBox').textContent = '';
          const formData = new FormData();
          formData.append('topic', topic);
          if (file) formData.append('scriptFile', file);
          const resp = await fetch('/generate', {
            method: 'POST',
            body: formData
          });
          const data = await resp.json();
          if (data.success) {
            document.getElementById('status').textContent = 'Podcast generated!';
            // Fetch and display the script
            fetch('/script.txt?' + Date.now())
              .then(r => r.text())
              .then(script => {
                document.getElementById('scriptBox').textContent = script;
              });
            document.getElementById('audioSource').src = '/output.wav?' + Date.now();
            document.getElementById('audio').load();
            document.getElementById('audio').style.display = 'block';
            fetch('/subtitles.srt?' + Date.now())
              .then(r => r.text())
              .then(srt => {
                // Simple SRT parser
                const pattern = /\d+\s+([\d:,]+) --> ([\d:,]+)\s+([\s\S]*?)(?=\n\d+|$)/g;
                let result = [], match;
                function toSeconds(time) {
                  const [h, m, s] = time.split(':');
                  const [sec, ms] = s.split(',');
                  return (+h) * 3600 + (+m) * 60 + (+sec) + (+ms) / 1000;
                }
                while ((match = pattern.exec(srt)) !== null) {
                  result.push({
                    start: toSeconds(match[1]),
                    end: toSeconds(match[2]),
                    text: match[3].replace(/\n/g, ' ')
                  });
                }
                const audio = document.getElementById('audio');
                const subsDiv = document.getElementById('subtitles');
                function updateSub() {
                  const t = audio.currentTime;
                  const current = result.find(s => t >= s.start && t <= s.end);
                  subsDiv.textContent = current ? current.text : '';
                }
                audio.addEventListener('timeupdate', updateSub);
              });
          } else {
            document.getElementById('status').textContent = 'Error: ' + data.error;
          }
        };
      </script>
    </body>
    </html>
    ''')

@app.route('/generate', methods=['POST'])
def generate():
    # Accept both topic and file upload
    topic = request.form.get('topic', '').strip()
    file = request.files.get('scriptFile')
    print(f"Received topic: {topic}, file: {file.filename if file else None}")
    try:
        if file and file.filename:
            # Use uploaded file as script
            script_text = file.read().decode('utf-8')
            with open(SCRIPT_FILE, 'w', encoding='utf-8') as f:
                f.write(script_text.strip())
            print("Using uploaded script file.")
        elif topic:
            # Use Gemini to generate script
            print("Calling Gemini to generate script...")
            prompt = (
                f"Generate a podcast-like discussion between two speakers (Speaker A and Speaker B) about '{topic}'. "
                "Format each line as 'Speaker A: ...' or 'Speaker B: ...', and make it sound like a real conversation. "
                "Keep it concise (6-10 exchanges)."
            )
            script = call_gemini_api(prompt)
            print("Gemini API response for script:", script)
            if script.startswith("Error:"):
                return jsonify({'success': False, 'error': script}), 500
            with open(SCRIPT_FILE, 'w', encoding='utf-8') as f:
                f.write(script.strip())
        else:
            return jsonify({'success': False, 'error': 'No topic or file provided.'}), 400
        print("Parsing script...")
        lines = parse_script(SCRIPT_FILE)
        print(f"Parsed lines: {lines}")
        print("Generating audio files...")
        audio_files = generate_all_audio(lines)
        print(f"Audio files: {audio_files}")
        print("Concatenating audio...")
        concatenate_audio(audio_files, AUDIO_FILE)
        print("Generating subtitles...")
        generate_srt(lines, audio_files, SRT_FILE)
        print("Cleaning up temp files...")
        cleanup_temp()
        print("Podcast generation complete!")
        if not (os.path.exists(AUDIO_FILE) and os.path.exists(SRT_FILE)):
            return jsonify({'success': False, 'error': 'Audio or subtitles not generated.'}), 500
        return jsonify({'success': True})
    except Exception as e:
        import traceback
        print("Error during podcast generation:")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/output.wav')
def serve_audio():
    return send_from_directory('.', 'output.wav')

@app.route('/subtitles.srt')
def serve_srt():
    return send_from_directory('.', 'subtitles.srt')

@app.route('/script.txt')
def serve_script():
    return send_from_directory('.', 'script.txt')

@app.route('/style.css')
def serve_css():
    return send_from_directory('.', 'style.css')

if __name__ == '__main__':
    import sys
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        app.run(debug=True, port=5000)
    else:
        main() 