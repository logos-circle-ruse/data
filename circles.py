import requests, json, os, logging, datetime
import pandas as pd
from github import Github

COUNTRY_MAPPING = {
    "Afghanistan": "AFG",
    "Albania": "ALB",
    "Algeria": "DZA",
    "Andorra": "AND",
    "Angola": "AGO",
    "Antigua and Barbuda": "ATG",
    "Argentina": "ARG",
    "Armenia": "ARM",
    "Australia": "AUS",
    "Austria": "AUT",
    "Azerbaijan": "AZE",
    "Bahamas": "BHS",
    "Bahrain": "BHR",
    "Bangladesh": "BGD",
    "Barbados": "BRB",
    "Belarus": "BLR",
    "Belgium": "BEL",
    "Belize": "BLZ",
    "Benin": "BEN",
    "Bhutan": "BTN",
    "Bolivia": "BOL",
    "Bosnia and Herzegovina": "BIH",
    "Botswana": "BWA",
    "Brazil": "BRA",
    "Brunei": "BRN",
    "Bulgaria": "BGR",
    "Burkina Faso": "BFA",
    "Burundi": "BDI",
    "Cabo Verde": "CPV",
    "Cambodia": "KHM",
    "Cameroon": "CMR",
    "Canada": "CAN",
    "Central African Republic": "CAF",
    "Chad": "TCD",
    "Chile": "CHL",
    "China": "CHN",
    "Colombia": "COL",
    "Comoros": "COM",
    "Congo (Congo-Brazzaville)": "COG",
    "Costa Rica": "CRI",
    "Croatia": "HRV",
    "Cuba": "CUB",
    "Cyprus": "CYP",
    "Czechia": "CZE",
    "Democratic Republic of the Congo": "COD",
    "Denmark": "DNK",
    "Djibouti": "DJI",
    "Dominica": "DMA",
    "Dominican Republic": "DOM",
    "Ecuador": "ECU",
    "Egypt": "EGY",
    "El Salvador": "SLV",
    "Equatorial Guinea": "GNQ",
    "Eritrea": "ERI",
    "Estonia": "EST",
    "Eswatini": "SWZ",
    "Ethiopia": "ETH",
    "Fiji": "FJI",
    "Finland": "FIN",
    "France": "FRA",
    "Gabon": "GAB",
    "Gambia": "GMB",
    "Georgia": "GEO",
    "Germany": "DEU",
    "Ghana": "GHA",
    "Greece": "GRC",
    "Grenada": "GRD",
    "Guatemala": "GTM",
    "Guinea": "GIN",
    "Guinea-Bissau": "GNB",
    "Guyana": "GUY",
    "Haiti": "HTI",
    "Honduras": "HND",
    "Hungary": "HUN",
    "Iceland": "ISL",
    "India": "IND",
    "Indonesia": "IDN",
    "Iran": "IRN",
    "Iraq": "IRQ",
    "Ireland": "IRL",
    "Israel": "ISR",
    "Italy": "ITA",
    "Jamaica": "JAM",
    "Japan": "JPN",
    "Jordan": "JOR",
    "Kazakhstan": "KAZ",
    "Kenya": "KEN",
    "Kiribati": "KIR",
    "Kuwait": "KWT",
    "Kyrgyzstan": "KGZ",
    "Laos": "LAO",
    "Latvia": "LVA",
    "Lebanon": "LBN",
    "Lesotho": "LSO",
    "Liberia": "LBR",
    "Libya": "LBY",
    "Liechtenstein": "LIE",
    "Lithuania": "LTU",
    "Luxembourg": "LUX",
    "Madagascar": "MDG",
    "Malawi": "MWI",
    "Malaysia": "MYS",
    "Maldives": "MDV",
    "Mali": "MLI",
    "Malta": "MLT",
    "Marshall Islands": "MHL",
    "Mauritania": "MRT",
    "Mauritius": "MUS",
    "Mexico": "MEX",
    "Micronesia": "FSM",
    "Moldova": "MDA",
    "Monaco": "MCO",
    "Mongolia": "MNG",
    "Montenegro": "MNE",
    "Morocco": "MAR",
    "Mozambique": "MOZ",
    "Myanmar": "MMR",
    "Namibia": "NAM",
    "Nauru": "NRU",
    "Nepal": "NPL",
    "Netherlands": "NLD",
    "New Zealand": "NZL",
    "Nicaragua": "NIC",
    "Niger": "NER",
    "Nigeria": "NGA",
    "North Korea": "PRK",
    "North Macedonia": "MKD",
    "Norway": "NOR",
    "Oman": "OMN",
    "Pakistan": "PAK",
    "Palau": "PLW",
    "Panama": "PAN",
    "Papua New Guinea": "PNG",
    "Paraguay": "PRY",
    "Peru": "PER",
    "Philippines": "PHL",
    "Poland": "POL",
    "Portugal": "PRT",
    "Qatar": "QAT",
    "Romania": "ROU",
    "Russia": "RUS",
    "Rwanda": "RWA",
    "Saint Kitts and Nevis": "KNA",
    "Saint Lucia": "LCA",
    "Saint Vincent and the Grenadines": "VCT",
    "Samoa": "WSM",
    "San Marino": "SMR",
    "Sao Tome and Principe": "STP",
    "Saudi Arabia": "SAU",
    "Senegal": "SEN",
    "Serbia": "SRB",
    "Seychelles": "SYC",
    "Sierra Leone": "SLE",
    "Singapore": "SGP",
    "Slovakia": "SVK",
    "Slovenia": "SVN",
    "Solomon Islands": "SLB",
    "Somalia": "SOM",
    "South Africa": "ZAF",
    "South Korea": "KOR",
    "South Sudan": "SSD",
    "Spain": "ESP",
    "Sri Lanka": "LKA",
    "Sudan": "SDN",
    "Suriname": "SUR",
    "Sweden": "SWE",
    "Switzerland": "CHE",
    "Syria": "SYR",
    "Taiwan": "TWN",
    "Tajikistan": "TJK",
    "Tanzania": "TZA",
    "Thailand": "THA",
    "Timor-Leste": "TLS",
    "Togo": "TGO",
    "Tonga": "TON",
    "Trinidad and Tobago": "TTO",
    "Tunisia": "TUN",
    "Turkey": "TUR",
    "Turkmenistan": "TKM",
    "Tuvalu": "TUV",
    "Uganda": "UGA",
    "Ukraine": "UKR",
    "United Arab Emirates": "ARE",
    "UK": "GBR",
    "USA": "USA",
    "Uruguay": "URY",
    "Uzbekistan": "UZB",
    "Vanuatu": "VUT",
    "Vatican City": "VAT",
    "Venezuela": "VEN",
    "Vietnam": "VNM",
    "Yemen": "YEM",
    "Zambia": "ZMB",
    "Zimbabwe": "ZWE"
}

def get_logger() -> logging.Logger:
    """
    Create the Logger
    """
    instance = logging.getLogger("circles")
    instance.setLevel(logging.INFO)
    instance.propagate = False

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        f"[%(asctime)s] [%(levelname)s]\t%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler.setFormatter(formatter)
    instance.addHandler(handler)
    return instance


def get_highchart_mapping(logger: logging.Logger) -> dict:
    """
    Fetch the HC keys for JSON world map
    """
    url = "https://code.highcharts.com/mapdata/custom/world-highres.topo.json"
    logger.info(f"Fetching Highchart mappings from {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://www.highcharts.com/",
    }

    response = requests.get(url, headers=headers, timeout=30)
    topology = response.json()
    map_keys = {
        info["properties"]["iso-a3"]: info["properties"]["hc-key"]
        for info in topology["objects"]["default"]["geometries"]
    }
    logger.info(f"GET: {len(map_keys.keys())} rows")
    return map_keys


def get_luma_events(logger: logging.Logger) -> pd.DataFrame:
    """
    Fetch Luma data from Institute of Free Technology
    """
    url = "https://hasura.bi.status.im/api/rest/circle/events"
    logger.info(f"Fetching Luma Events data from {url}")

    data = requests.get(url).json().get("stg_external_circle_circle_event", [])
    data = pd.DataFrame(data)
    logger.info(f"GET: {len(data)} rows")

    column_mapping = {
        "location_country": "country",
        "location_city": "city"
    }
    data = data.rename(columns=column_mapping)[list(column_mapping.values())]
    data = data.groupby("country").count()["city"].reset_index().rename(columns={"city": "circles"})
    logger.info("Data has been processed")
    return data.copy()


def commit_data(file_path: str, content: str, commit_message: str, logger: logging.Logger):
    """
    Commit the data to the repository
    """
    token = os.environ.get("TOKEN")
    repository_name = os.environ.get("GITHUB_REPOSITORY")
    branch = os.environ.get("GITHUB_REF_NAME", "main")

    github_client = Github(token)
    repo = github_client.get_repo(repository_name)

    try:
        existing_file = repo.get_contents(file_path, ref=branch)
        repo.update_file(
            path=file_path,
            message=commit_message,
            content=content,
            sha=existing_file.sha,
            branch=branch,
        )

        logger.info(f"Updated {file_path} on branch {branch}")

    except Exception:
        repo.create_file(
            path=file_path,
            message=commit_message,
            content=content,
            branch=branch,
        )
        logger.info(f"Uploaded {file_path} on branch {branch}")

if __name__ == "__main__":

    logger = get_logger()
    luma_events = get_luma_events(logger)
    highchart_mapping = get_highchart_mapping(logger)

    luma_events = luma_events.assign(
        hc = luma_events["country"].map(COUNTRY_MAPPING).map(highchart_mapping)
    )

    query = luma_events["hc"].isna()
    if query.sum() > 0:
        countries = luma_events.loc[query, "country"].to_list()
        raise Exception(f"The following countries mismatch:\n{countries}\nPlease further investigate...")

    data = {
        "total": int(luma_events["circles"].sum()),
        "data": luma_events.to_dict("records")
    }

    json_content = json.dumps(data, indent=2)

    commit_data(
        file_path="website/world-circles.json",
        content=json_content,
        commit_message=f"circles: Logos data from Luma as of {datetime.datetime.now().date()}",
        logger=logger
    )