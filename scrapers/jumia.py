import requests
from bs4 import BeautifulSoup
import pandas as pd
import sys
import os
from datetime import datetime
from utils.minio_client import upload_df
from config import BRONZE_BUCKET

def scrape(date_str):

    url = "https://www.jumia.ma/smartphones/"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    products = soup.find_all("article", class_="prd")

    data = []

    for p in products:
        name = p.find("h3", class_="name")
        price = p.find("div", class_="prc")

        if name and price:
            data.append({
                "name": name.text.strip(),
                "price": price.text.strip(),
                "source": "jumia",
                "date": date_str
            })

    df = pd.DataFrame(data)

    print("Nombre de produits scrapés :", len(df))
    print(df.head())

    # upload to MINIO (bronze)
    filename = f"jumia/jumia_raw_{date_str}.csv"
    upload_df(BRONZE_BUCKET, filename, df)

    print(f"✅ Upload Bronze : {filename}")


if __name__ == "__main__":
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.today().strftime("%Y-%m-%d")
    scrape(date_str)