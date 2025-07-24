Podcast Generator - BTech Project
==================================

This project lets you generate a podcast (audio + subtitles) from a topic prompt (using Gemini AI) or by uploading your own podcast script file. You can use it from your web browser!

---

## Project Architecture

```
+-------------------+         +-------------------+         +-------------------+
|  Web Browser UI   | <-----> |   Flask Web App   | <-----> |  Podcast Engine   |
+-------------------+         +-------------------+         +-------------------+
        |                          |                                 |
        | 1. User enters topic     |                                 |
        |    or uploads script     |                                 |
        |------------------------->|                                 |
        |                          | 2. If topic: call Gemini API    |
        |                          |    If file: use uploaded script |
        |                          |-------------------------------->|
        |                          |                                 | 3. Parse script
        |                          |                                 | 4. Generate audio (TTS)
        |                          |                                 | 5. Generate subtitles (SRT)
        |                          |<--------------------------------|
        | 6. Serve audio & subs    |                                 |
        |<-------------------------|                                 |
        | 7. Play audio & show     |                                 |
        |    subtitles in browser  |                                 |
```

### **Components**
- **Web Browser UI:**
  - Enter a topic or upload a script file
  - See generated script, play podcast audio, view subtitles
- **Flask Web App:**
  - Receives user input
  - Calls Gemini API (for topic prompt)
  - Handles file uploads
  - Orchestrates podcast generation
  - Serves audio, subtitles, and script to browser
- **Podcast Engine (Python):**
  - Parses script (supports flexible formats)
  - Uses pyttsx3 for TTS (audio)
  - Uses pydub for audio concatenation
  - Generates SRT subtitles
  - Cleans up temp files

### **Flow**
1. User enters a topic or uploads a `.txt` script in the browser.
2. Flask receives the request.
3. If a topic is given, Flask calls Gemini API to generate a podcast script. If a file is uploaded, Flask uses its contents as the script.
4. The script is parsed into speaker lines.
5. Each line is converted to audio using TTS (pyttsx3).
6. All audio lines are concatenated into a single podcast audio file (`output.wav`).
7. Subtitles are generated in SRT format (`subtitles.srt`).
8. The browser displays the script, plays the audio, and shows subtitles in sync.

---

## Requirements
- Python 3.8+
- pip (Python package manager)
- ffmpeg (for audio processing)

---

## Gemini API Key Setup (IMPORTANT)

To use the Gemini AI features, you need your own Gemini API key from Google:

1. **Get your Gemini API key:**
   - Go to: https://aistudio.google.com/app/apikey
   - Sign in with your Google account.
   - Click "Create API key" and copy the key shown.

2. **Update the API key in the code:**
   - Open `main.py` in the `podcast_player` folder.
   - Find this line (near the top):
     ```python
     'X-goog-api-key': 'YOUR_GEMINI_API_KEY_HERE'
     ```
   - Replace `'YOUR_GEMINI_API_KEY_HERE'` with your actual API key (keep the quotes).
   - Example:
     ```python
     'X-goog-api-key': 'AIzaSy...yourkey...'
     ```

3. **Keep your API key private!**
   - Do not share your API key publicly or commit it to public repositories.

---

## Installation Steps

1. **Clone or Download the Project**
   - Place all files in a folder (e.g., `gemini-2-tts`).

2. **Open a terminal/command prompt**
   - Navigate to the `podcast_player` folder:
     ```
     cd path/to/gemini-2-tts/podcast_player
     ```

3. **Install Python dependencies**
   ```
   pip install -r requirements.txt
   pip install flask requests pydub pyttsx3 srt
   ```

4. **Install ffmpeg**
   - **Windows:**
     - Easiest: Use Chocolatey, Scoop, or Winget:
       - `choco install ffmpeg-full`  (if you have Chocolatey)
       - `scoop install ffmpeg`       (if you have Scoop)
       - `winget install ffmpeg`      (if you have Winget)
     - Or download from https://ffmpeg.org/download.html and add the `bin` folder to your PATH.
   - **Linux:**
     - `sudo apt install ffmpeg`
   - **Mac:**
     - `brew install ffmpeg`
   - After install, run `ffmpeg -version` to check it works.

---

## How to Run the Web App

1. **Open a terminal and go to the podcast_player folder:**
   ```
   cd path/to/gemini-2-tts/podcast_player
   ```

2. **Start the web server:**
   ```
   python main.py web
   ```
   - You should see: `Running on http://127.0.0.1:5000`

3. **Open your browser and go to:**
   ```
   http://localhost:5000
   ```

4. **Use the app:**
   - Enter a topic and click "Generate Podcast" **or** upload a `.txt` script file and click "Generate Podcast".
   - Listen to the audio and see subtitles in your browser!

---

## Notes
- All generated files (audio, subtitles, script) will be in the `podcast_player` folder.
- If you have any errors, check your terminal for messages.
- If you need help, ask your teammates or your guide!

---

**Team Members:**
- [Add your names here]

Good luck with your BTech project! 


    