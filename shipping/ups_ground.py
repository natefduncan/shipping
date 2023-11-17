import datetime as dt
import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image

from shipping.ups_ground_boxes import BOXES, COLORS


def download_file(url, user_agent):
    local_filename = url.split("/")[-1]
    headers = {"User-Agent": user_agent}
    with requests.get(url, stream=True, headers=headers) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename


def download_map(zip_code, user_agent):
    formatted_date = dt.datetime.today().strftime("%m%d%Y")
    headers = {
        "User-Agent": user_agent,
    }
    url = f"https://www.ups.com/maps/printerfriendly?loc=en_US&usmDateCalendar={formatted_date}&stype=O&zip={zip_code}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, features="html.parser")
        img = soup.find("img", attrs={"id": "imgMap"})
        if img:
            endpoint = img["src"]
            img_url = f"https://www.ups.com{endpoint}"
            download_file(img_url, user_agent)
            local_filename = endpoint.split("/")[-1]
            return local_filename
        else:
            imgs = soup.find_all("img")
            print(imgs)
            raise ValueError("Could not find img")
    else:
        raise ValueError("Request error")


def crop_to_state(img, state: str):
    x, y, x_offset, y_offset = BOXES[state]
    return img.crop((x, y, x + x_offset, y + y_offset))


def get_dominant_color(img):
    img = img.convert("RGB")
    dictc = {}
    for i in range(img.width):
        for j in range(img.height):
            h = img.getpixel((i, j))
            if h == (0, 0, 0) or h == (255, 255, 255):  # Filter black and white
                continue
            if h in dictc:
                dictc[h] = dictc[h] + 1
            else:
                dictc[h] = 1
    return sorted(dictc.items(), key=lambda x: x[1], reverse=True)[0][0]


def color_to_days(color) -> int:
    for key, value in COLORS.items():
        if value[0] == color[0] and value[1] == color[1]:  # Don't match on B
            return key
    raise ValueError(f"Could not find color {color}")


def ups_ground_days(from_zip: str, to_state: str, map_dir: str):
    maps = pd.read_csv(f"{map_dir}/maps.csv").to_dict(orient="records")
    from_file = next((i for i in maps if str(i["zip_code"]) == from_zip), None)["file_name"]
    if from_file:
        img = Image.open(f"{map_dir}/{from_file}")
        cropped_img = crop_to_state(img, to_state)
        dominant_color = get_dominant_color(cropped_img)
        return color_to_days(dominant_color)
