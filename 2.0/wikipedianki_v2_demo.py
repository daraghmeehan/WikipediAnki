from bs4 import BeautifulSoup
import requests

# # r = requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/Amsterdam")
# r = requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/Chinatown")
# page = r.json()
# print(page["extract"]) # Returns 'Amsterdam is the capital and...'

# BOSS https://www.jcchouinard.com/wikipedia-api/
# maybe good
# https://stackoverflow.com/questions/4460921/extract-the-first-paragraph-from-a-wikipedia-article-python

wikipedia_url = "https://en.wikipedia.org/wiki/Chinatown"

r = requests.get(wikipedia_url, allow_redirects=True)
# use original encoding of content!! instead of utf-8
# soup = BeautifulSoup(r.content, "html5lib", from_encoding="utf-8") ##!! this HTML parser is better apparently
soup = BeautifulSoup(r.content, "html.parser", from_encoding="utf-8")
redirected_address = soup.find("link", rel="canonical").get("href")
assert (
    wikipedia_url == redirected_address
)  # if choose "Barack", we get redirected to "Barack Obama". Assert equal to make sure user has desired page, and using consistent naming of pages