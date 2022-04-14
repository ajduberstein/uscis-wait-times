import datetime
import glob
import json
import pathlib
import sys


def load_wait_times(form_code, office_code, data_directory="data"):
    # Identify the most recently scraped file.
    files = glob.glob(
        str(pathlib.Path(data_directory, form_code, office_code, "*.json"))
    )
    files.sort()
    most_recent = files[-1]

    # Parse JSON.
    with open(most_recent, "r") as f:
        return json.load(f)


def subtype_wait_time(wait_times, subtype_form_type):
    for subtype in wait_times["data"]["processing_time"]["subtypes"]:
        if subtype["form_type"] == subtype_form_type:
            return subtype
    return None


def parse_date(date_string):
    return datetime.datetime.strptime(date_string, "%B %d, %Y").date()


def compute_result_range(subtype, received_date):
    upper, lower = subtype["range"]
    assert upper["unit"] == "Months"
    assert lower["unit"] == "Months"
    MONTH = datetime.timedelta(days=365.0 / 12.0)
    return (
        received_date + MONTH * lower["value"],
        received_date + MONTH * upper["value"],
    )


def main(args):
    # Read applications.
    applications_filepath = args[0]
    with open(applications_filepath, "r") as f:
        applications = json.load(f)

    # Compute wait times.
    for application in applications:
        wait_times = load_wait_times(
            application["form_code"], application["office_code"]
        )
        subtype = subtype_wait_time(wait_times, application["subtype_form_type"])
        received_date = parse_date(application["received_date"])
        lower_date, upper_date = compute_result_range(subtype, received_date)
        print(
            f'{application["label"]}\t{application["form_code"]}\t{lower_date}\t{upper_date}\t({application["subtype_form_type"]})'
        )


if __name__ == "__main__":
    main(sys.argv[1:])
