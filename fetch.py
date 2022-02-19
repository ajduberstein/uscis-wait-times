import copy
import datetime
import json
import logging
import os
import time
from pathlib import Path
import sys

import requests as r
import pandas as pd

logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-fetch-dest": "empty",
    "user-agent": "https://github.com/ajduberstein/uscis-wait-times",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "Referer": "https://egov.uscis.gov/processing-times/",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

FORMS = [
    "I-102",
    "I-129",
    "I-129CW",
    "I-129F",
    "I-130",
    "I-131",
    "I-140",
    "I-212",
    "I-360",
    "I-407",
    "I-485",
    "I-526",
    "I-539",
    "I-600",
    "I-600A",
    "I-601",
    "I-601A",
    "I-612",
    "I-730",
    "I-751",
    "I-765",
    "I-765V",
    "I-800",
    "I-800A",
    "I-817",
    "I-821",
    "I-821D",
    "I-824",
    "I-829",
    "I-90",
    "I-914",
    "I-918",
    "I-929",
    "N-400",
    "N-565",
    "N-600",
    "N-600K",
]


def query(uri):
    response = r.get(uri, headers=HEADERS)
    json = response.json()
    return json


def query_forms():
    return query("https://egov.uscis.gov/processing-times/api/forms")


def query_center(form_code):
    res = query(f"https://egov.uscis.gov/processing-times/api/formoffices/{form_code}")
    return res["data"]["form_offices"]["offices"]


def query_wait_time(form_code, center_code):
    res = query(
        f"https://egov.uscis.gov/processing-times/api/processingtime/{form_code}/{center_code}"
    )
    return res


def transform_wait_time(json, office_name):
    record = {}
    json = json["processing_time"]
    record["form"] = json["form_name"]
    record["subtype_form"] = None
    record["office_code"] = json["office_code"]
    record["office_name"] = office_name
    try:
        record["range_start_value"] = json["range"][1]["value"]
        record["range_start_units"] = json["range"][1]["unit"]
        record["range_end_value"] = json["range"][0]["value"]
        record["range_end_units"] = json["range"][0]["unit"]
        record["processed_at"] = (
            datetime.datetime.now().replace(microsecond=0).isoformat()
        )
        return [record]
    except TypeError:  # Range is null, use subtype form
        records = []
        for subform in json["subtypes"]:
            record["subtype_form"] = subform["form_type"]
            record["range_start_value"] = subform["range"][1]["value"]
            record["range_start_units"] = subform["range"][1]["unit"]
            record["range_end_value"] = subform["range"][0]["value"]
            record["range_end_units"] = subform["range"][0]["unit"]
            records.append(copy.copy(record))
        return records


def today():
    return datetime.datetime.today().strftime("%Y-%m-%d")


def fetch_wait_times():
    datestr = today()
    output = []
    for form_code in FORMS:
        offices = query_center(form_code)
        time.sleep(1)
        for office in offices:
            office_code = office["office_code"]
            wait_time = query_wait_time(form_code, office_code)
            path = Path(f"./data/{form_code}/{office_code}")
            path.mkdir(
                parents=True, exist_ok=True
            )
            with open(path / f'{datestr}.json', 'w') as f:
                f.write(json.dumps(wait_time, sort_keys=True, indent=4))
            time.sleep(1)
    return output


def main():
    logging.info("Starting...")
    fetch_wait_times()
    logging.info("Task complete")


if __name__ == "__main__":
    main()
