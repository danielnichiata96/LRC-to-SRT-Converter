from flask import Flask, request, send_file, render_template_string
import os
import re

app = Flask(__name__)

def parse_lrc_timestamp(timestamp):
    try:
        minutes, seconds = timestamp.split(':')
        seconds, milliseconds = seconds.split('.')
        minutes, seconds, milliseconds = int(minutes), int(seconds), int(milliseconds)
        return minutes * 60 + seconds + milliseconds / 100
    except ValueError:
        return None

def replace_notes(text):
    # Replace ♪ with ♫ in the text
    return text.replace('♪', '♫')

def censor_text(text):
    # Define curse words and their replacements
    curse_words = {
        'ass': 'a**',
        'bitch': 'b****',
        'bitches': 'b******',
        'boob': 'b***',
        'boobs': 'b****',
        'butt': 'b***',
        'bullshit': 'bulls****',
        'cock': 'c***',
        'damn': 'd***',
        'dick': 'd***',
        'boobs': 'b****',
        'faggot': 'f*****',
        'fuck': 'f***',
        'fucker': 'f*****',
        'fuckin': 'f*****',
        'fucked': 'f*****',
        'motherfuckin': 'motherf*****',
        'motherfucking': 'motherf******',
        'motherfuckers': 'motherf******',
        'motherfucker': 'motherf*****',
        'shit': 's***',
        'shits': 's****',
        'shitty': 's****',
        'tit': 't**',
        'tits': 't***',
        'nigga': 'n****',
        'niggas': 'n*****',
        'pussy': 'p****',
        'hoe': 'h**',
        'hoes': 'h***',
        'gangbang': 'g*******',
        'jizz': 'j***',
        'vagina': 'v*****',
        'mierda': 'm*****',
        'cabrón': 'c*****',
        'cojone': 'c*****',
        'carajo': 'c*****',
        'culo': 'c***',
        'chinga': 'c*****',
        'chingar': 'c******',
        'chingamo': 'c*******',
        'pendejo': 'p******',
        'puta': 'p***',
        'puñeta': 'p*****'
    }
    # Replace curse words with censored versions
    for word, censored_word in curse_words.items():
        text = re.sub(rf'\b{word}\b', censored_word, text, flags=re.IGNORECASE)
    return text

def lrc_to_srt(lrc_content):
    subs = []
    pattern = r'\[(\d+:\d+\.\d+)\](.*)'
    matches = re.findall(pattern, lrc_content)
    for idx, match in enumerate(matches):
        timestamp, text = match
        start_time = parse_lrc_timestamp(timestamp)
        
        # If text is empty, add an instrumental break symbol
        if not text.strip():
            text = '♫'
        else:
            # Replace ♪ with ♫ and censor text
            text = censor_text(replace_notes(text))
        
        if start_time is not None:
            end_time = parse_lrc_timestamp(matches[idx + 1][0]) if idx + 1 < len(matches) else start_time + 1
            subs.append(f"{len(subs) + 1}\n{format_time(start_time)} --> {format_time(end_time)}\n{text.strip()}\n")

    # Remove last entry if it is an instrumental break (♫) at the end of the song
    if subs and "♫" in subs[-1]:
        subs.pop()

    return '\n'.join(subs)

def format_time(seconds):
    hours = int(seconds) // 3600
    minutes = (int(seconds) % 3600) // 60
    seconds = int(seconds) % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part", 400
        file = request.files['file']
        if file.filename == '' or not file.filename.endswith('.lrc'):
            return "No selected file or file type is not .lrc", 400
        
        lrc_content = file.read().decode('utf-8')
        srt_content = lrc_to_srt(lrc_content)
        
        srt_file_path = os.path.join("temp.srt")
        with open(srt_file_path, 'w', encoding='utf-8') as srt_file:
            srt_file.write(srt_content)
        
        return send_file(srt_file_path, as_attachment=True, download_name=file.filename.replace('.lrc', '.srt'))

    # Simple HTML form to upload the file
    html_form = '''
    <!doctype html>
    <title>Upload LRC File</title>
    <h1>Upload an .lrc file to convert to .srt</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Convert>
    </form>
    '''
    return render_template_string(html_form)

if __name__ == "__main__":
    app.run(debug=True)
