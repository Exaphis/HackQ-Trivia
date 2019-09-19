# HackQ-Trivia
Yet another HQ trivia bot, in Python. Automatically scrapes HQ Trivia questions without OCR and answers them.

## Getting Started
Requires Python 3.7 or above.
### Dependencies
```
colorama
lomond
requests
aiohttp
bs4
nltk
google-api-python-client
unidecode
aiodns
cchardet
pyjwt
```
### Installation
```
git clone https://github.com/Exaphis/HackQ-Trivia.git
cd HackQ-Trivia
pip install -r requirements.txt
```
#### Bearer token
It can be found by sniffing the traffic on your phone. The bearer token is easily found on an emulator, since they are easy to root and most use Android versions without certificate pinning. Popular tools used to obtain bearer tokens are Charles, Fiddler, and Burp Suite.
 
Paste your bearer token after `Bearer` in `hq_config.conf`, all within one line.

#### Google Custom Search Engine API key
CAUTION — First 100 queries per day are free, additional requests cost $5 per 1000 queries.
* Obtain an API key from https://developers.google.com/custom-search/v1/overview
* Paste it after `GoogleApiKey` in `hq_config.conf`


#### Google Custom Search Engine ID
* Create a new custom search engine at https://cse.google.com/cse/
* Name your custom search engine and type in any valid URL in `Sites to search`
* Click `Control Panel`
* Enable `Search the entire web`
* Delete the site you added initially in `Sites to search`
* Copy the `Search engine ID` to clipboard
* Paste it after `GoogleCseId` in `hq_config.conf`


### Usage
```
cd HackQ-Trivia
python3 -m hackq_trivia.hq_main
```
