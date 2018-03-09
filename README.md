# HackQ-Trivia
Yet another HQ trivia bot, in Python. Automatically scrapes HQ Trivia questions without OCR and answers them.

## Getting Started
Requires Python 3.6+
### Dependencies
```
bs4
nltk
aiohttp
unidecode
```
### Installation
```
git clone https://github.com/Exaphis/HackQ-Trivia.git
cd HackQ-Trivia
```
In Python 3, run:
```
import nltk
nltk.download("stopwords")
nltk.download("averaged_perceptron_tagger")
```
Enter your bearer token and user ID in the conn_settings.txt file. These values can be found by sniffing the traffic on your phone. The bearer token should be one line, without the word Bearer.

### Usage
```
python3 hq-main.py
```
