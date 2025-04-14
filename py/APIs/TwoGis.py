import requests

def clamp(n, lower, upper):
    return max(lower, min(upper, n))


class TwoGis(object):
    def __init__(self, api_key):
        self.api_key = api_key

    class StaticBuilder(object):
        def __init__(self):
            self.url = "https://static.maps.2gis.com/1.0?locale=en_RU"

        def size(self, w, h, scale=None):
            self.url += f"&s={w}x{h}"
            if scale is not None:
                self.url += f"@{clamp(scale, 1, 2)}x"
            return self

        def center(self, lat, lon):
            self.url += f"&c={lat},{lon}"
            return self

        def zoom(self, value):
            self.url += f"&z={clamp(value, 1, 18)}"
            return self

        def marker(self, lat, lon, circle=False, color="be", big_size=False):
            self.url += f"&pt={lat},{lon}~k:{'c' if circle else 'p'}~c:{color}~s:{'s' if big_size else 'l'}"
            return self

        def url(self):
            return self.url

        def request(self):
            response = requests.get(self.url)

            if response.status_code != 200:
                return None
            return response.content

    def find_region_id(self, regin):
        response = requests.get(f"https://catalog.api.2gis.com/2.0/region/search?q={regin}&key={self.api_key}&locale=en_RU")

        json = response.json()
        status_code = json["meta"]["code"]
        if status_code == 200:
            return int(json["result"]["items"][0]["id"])
        else:
            return 0

    def find_place(self, target, location=None):
        url = f"https://catalog.api.2gis.com/3.0/items?key={self.api_key}&q={target}&locale=en_RU"
        if location is not None:
            url += f"&location={location}"
        response = requests.get(url)

        json = response.json()
        status_code = json["meta"]["code"]
        if status_code == 200:
            return json
        else:
            return {"error": "Fail to find place",
                    "content": json["meta"]["error"]["message"]}

    def find_places_in_region(self, target, location=None, region_id=23):
        url = f"https://catalog.api.2gis.com/2.0/catalog/rubric/search?q={target}&region_id={region_id}&key={self.api_key}&locale=en_RU"
        response = requests.get(url)

        json = response.json()
        status_code = json["meta"]["code"]
        if status_code != 200:
            return {"error": "Fail to find rubric in region",
                    "content": json["meta"]["error"]["message"]}

        print( json["result"]["items"])
        best_match_id = json["result"]["items"][0]["id"]

        url = f"https://catalog.api.2gis.com/3.0/items?rubric_id={best_match_id}&key={self.api_key}&locale=en_RU&fields=items.point"
        if location is not None:
            url += f"&location={location}"
        response = requests.get(url)

        json = response.json()
        status_code = json["meta"]["code"]
        if status_code == 200:
            return json["result"]["items"]
        else:
            return {"error": "Fail to find rubric",
                    "content": json["meta"]["error"]["message"]}

    def get_item_info_by_id(self, item_id):
        url = f"https://catalog.api.2gis.com/3.0/items/byid?id={item_id}&key={self.api_key}&locale=en_RU"
        response = requests.get(url)

        json = response.json()
        status_code = json["meta"]["code"]
        if status_code == 200:
            return json
        else:
            return {"error": "Fail to find rubric",
                    "content": json["meta"]["error"]["message"]}
        pass