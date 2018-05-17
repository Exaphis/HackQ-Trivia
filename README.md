# HackQ-Trivia
Yet another HQ trivia bot, in Python. Automatically scrapes HQ Trivia questions without OCR and answers them.

## Getting Started
Requires Python 3.6+
### Dependencies
#### Required
```
aiohttp
bs4
lomond
nltk
unidecode
```
#### Optional
```
aiodns
cchardet
```
### Installation
```
git clone https://github.com/Exaphis/HackQ-Trivia.git
cd HackQ-Trivia
pip install -r requirements.txt
```

If on Mac, run: 
```
/Applications/"Python 3.6"/"Install Certificates.command"
```

In Python 3, run:
```
import nltk
nltk.download("all")
```
Enter your bearer token and user ID in the conn_settings.txt file. These values can be found by sniffing the traffic on your phone. The bearer token should be one line, without the word Bearer.

### Usage
```
python3 hq_main.py
```

If ```RuntimeError: Connection settings invalid``` appears, then your user ID/bearer token is invalid.
