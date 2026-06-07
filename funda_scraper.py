import os
from supabase import create_client
from dotenv import load_dotenv
from funda import Funda

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

funda = Funda()

# ---- CONFIG ----
LOCATION = "amsterdam"
OFFERING_TYPE = "buy"
PRICE_MAX = 600000
PRICE_MIN = 400000
AREA_MIN = 60
AREA_MAX = None
PLOT_MIN = None
PLOT_MAX = None
OBJECT_TYPE = None
ENERGY_LABEL = None
MAX_PAGES = 2
ALLOWED_POSTCODES = {
    *range(1011, 1020),  # centrum/aan IJ: 1011–1019
    *range(1051, 1060),  # west:           1051–1059
    *range(1071, 1080),  # zuid:           1071–1079
    *range(1091, 1095),  # oost:           1091–1093
    *range(1096, 1099),  # oost:           1096–1098
}


def get_existing_ids():
    response = supabase.table("houses").select("id").execute()
    return {row["id"] for row in response.data}


def fetch_funda_listings(
        LOCATION=None,
        OFFERING_TYPE=None,
        PRICE_MAX=None,
        PRICE_MIN=None,
        AREA_MIN=None,
        AREA_MAX=None,
        PLOT_MIN=None,
        PLOT_MAX=None,
        OBJECT_TYPE=None,
        ENERGY_LABEL=None):

    all_results = []
    for page in range(MAX_PAGES):
        results = funda.search(
            location=LOCATION,
            category=OFFERING_TYPE,  
            min_price=PRICE_MIN,
            max_price=PRICE_MAX,
            min_area=AREA_MIN,
            max_area=AREA_MAX,
            min_plot=PLOT_MIN,
            max_plot=PLOT_MAX,
            object_type=OBJECT_TYPE,
            energy_label=ENERGY_LABEL,
            sort='newest',
            page=page,
        )
        all_results.extend(results)
    return all_results


def is_within_ring(postal_code: str, allowed_postcodes: set) -> bool:
    if not postal_code:
        return False
    try:
        prefix = int(postal_code[:4])
        return prefix in allowed_postcodes
    except Exception:
        return False


def is_available(listing) -> bool:
    status = listing.status or ""
    status = status.strip().lower()
    return "beschikbaar" in status or "available" in status


def transform_listing(listing):
    return {
        "id": listing.global_id,
        "address": listing.title,
        "neighbourhood": listing.address.neighbourhood,
        "city": listing.city,
        "price": listing.price.amount,
        "surface_m2": listing.living_area,
        "bedrooms": listing.bedrooms,
        "url": listing.url,
        "status": "nieuw",
        "publish_date": listing.publication_date,
    }


def main():
    print("Fetching existing houses...")
    existing_ids = get_existing_ids()

    print("Fetching listings from Funda...")
    listings = fetch_funda_listings(
        LOCATION, OFFERING_TYPE,
        PRICE_MAX, PRICE_MIN,
        AREA_MIN, AREA_MAX,
        PLOT_MIN, PLOT_MAX,
        OBJECT_TYPE, ENERGY_LABEL,
    )

    new_count = 0

    for list_count, listing in enumerate(listings):
        print(f"Listing number {list_count}: {listing}")

        # ---- Extra filtering in Python ----
        if listing.price.amount is None or listing.price.amount > PRICE_MAX:
            print("Filtered: Asking price too high")
            continue

        if listing.living_area is None or listing.living_area < AREA_MIN:
            print("Filtered: Living area too small")
            continue

        if not is_within_ring(listing.postcode, ALLOWED_POSTCODES):
            print("Filtered: Not within ring")
            print(listing.postcode)
            continue

        # if not is_available(listing):
        #     print("Filtered: Not available")
        #     continue

        if listing.global_id in existing_ids:
            print("Filtered: Already exists in database")
            continue

        house_data = transform_listing(listing)
        print("Inserting new house:", house_data)
        supabase.table("houses").insert(house_data).execute()
        new_count += 1

    print(f"Inserted {new_count} new houses.")


if __name__ == "__main__":
    main()