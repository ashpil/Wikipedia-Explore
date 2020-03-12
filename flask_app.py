import requests
import json
from bs4 import BeautifulSoup
from geopy.distance import geodesic
from flask import Flask, render_template, request

APP = Flask(__name__)
API = "https://en.wikipedia.org/w/api.php"
SES = requests.Session()


# Main index function
@APP.route('/', methods=['GET', 'POST'])
def index():
    # Get locations on screen and export as geojson
    if request.method == "POST":
        data = request.get_json()
        # Fetch from Wikipedia api based on screen location/size
        results = getNearbyPlaces(data['latitude'], data['longitude'], geodesic(reversed(data['ne']),reversed(data['sw'])).meters / 2)
        # Convert to geojson
        results = jsonToGeojson(results)
        with open('/home/ashpil/mysite/static/locations.geojson', 'w') as outfile:
            json.dump(results, outfile)
        print("got new geojson")
        return results

    return render_template('map.html')


def getNearbyPlaces(lat, lng, screensize):
    # Wikipedia API parameters
    params = {
        "action": "query",
        "format": "json",
        "colimit": "40",
        "generator": "search",
        "prop": "coordinates",
        "gsrsearch": "nearcoord:" + str(round(screensize)) + "m," + str(lat) + "," + str(lng),
        "gsrlimit": "40"
    }

    # I know there's a specific Wikipedia geosearch ability, but that's very limited in the fact that it can only search
    # in a maximum of 10km, which is very unhelpful for the scale I'm working on.
    # This is a neat workaround that allows searching for articles in a location of any size.
    res = SES.get(url=API, params=params)
    data = res.json()
    # Strip some of the junk, return
    places = data["query"]["pages"]
    return places

# Takes the json file receives from the Wikipedia API and converts it to a valid geojson file, keeping only the
# information that we are interested in
def jsonToGeojson(json):
    geojson = {
        'type': 'FeatureCollection',
        'features': []
    }
    for entry in json.items():
        try:
            feature = {
                'type': 'Feature',
                'properties': {},
                'geometry': {
                    'type': 'Point',
                    'coordinates': []
                }
            }
            feature['geometry']['coordinates'] = [entry[1]["coordinates"][0]["lon"],
                                                  entry[1]["coordinates"][0]["lat"]]
            feature['properties']['title'] = entry[1]['title']
            feature['properties']['id'] = entry[1]['pageid']
            geojson['features'].append(feature)
        except KeyError:
            continue
    return geojson

# Fetches raw html Wikipedia description of article from id, strips it of data we don't want.
@APP.route('/_get_description', methods=['GET', 'POST'])
def getDescription():
    if request.method == "POST":
        article = request.form['article_id']
        params = {
            "action": "query",
            "prop": "revisions",
            "format": "json",
            "pageids": article,
            "rvprop": "content",
            "rvparse": True,
            "rvlimit": 1,
            "rvsection": 0
        }

        res = SES.get(url=API, params=params)
        data = res.json()
        data = data["query"]["pages"][str(article)]["revisions"][0]["*"]

        # Uses BeautifulSoup html parser to remove unneeded elements
        soup = BeautifulSoup(data, "html.parser")

        #  Gets first non-infobox paragraph with text in it
        for x in soup.find_all('table', 'infobox geography vcard'):
            x.extract()
        for x in soup.find_all('span', id="coordinates"):
            x.extract()
        for x in soup.find_all('sup'):
            x.extract()
        paragraphs = soup.find_all("p")
        for paragraph in paragraphs:
            if len(paragraph.get_text(strip=True)) != 0:
                data = paragraph
                break
        data = str(data)

        # Replaces local links with links that would actually work
        data = data.replace("/wiki/", "//en.wikipedia.org/wiki/")

        # Makes those links open in new tab
        data = data.replace("<a ", '<a target="_blank" ')


if __name__ == '__main__':
    APP.run(debug=True)
