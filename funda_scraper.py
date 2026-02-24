import os
import json
from supabase import create_client
from dotenv import load_dotenv
from funda import Funda

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

funda = Funda()

# ---- CONFIG ----
LOCATION="amsterdam"
OFFERING_TYPE="buy"
PRICE_MAX=570000
PRICE_MIN=400000
AREA_MIN=55
AREA_MAX=None
PLOT_MIN=None
PLOT_MAX=None
OBJECT_TYPE=None
ENERGY_LABEL=None

def get_existing_ids():
    response = supabase.table("houses").select("id").execute()
    return {row["id"] for row in response.data}


def fetch_funda_listings(
        LOCATION=None,
        OFFERING_TYPE='buy',
        PRICE_MAX=None,
        PRICE_MIN=None,
        AREA_MIN=None,
        AREA_MAX=None,
        PLOT_MIN=None,
        PLOT_MAX=None,
        OBJECT_TYPE=None,
        ENERGY_LABEL=None):

    all_results = []
    for page in range(5):
        results = funda.search_listing(
            location=LOCATION,           # City or area name
            offering_type=OFFERING_TYPE,            # 'buy' or 'rent'
            price_min=PRICE_MIN,               # Minimum price
            price_max=PRICE_MAX,               # Maximum price
            area_min=AREA_MIN,                    # Minimum living area (m²)
            area_max=AREA_MAX,                   # Maximum living area (m²)
            plot_min=PLOT_MIN,                   # Minimum plot area (m²)
            plot_max=PLOT_MAX,                   # Maximum plot area (m²)
            object_type=OBJECT_TYPE ,        # Property types (default: house, apartment)
            energy_label=ENERGY_LABEL,       # Energy labels to filter
            sort='newest',                  # Sort order (see below)
            page=page,     
        )
        all_results.extend(results)
    return all_results


def is_within_ring(postal_code):
    """
    Simpele benadering:
    Binnen ring globaal: 1011–1098 
    """
    if not postal_code:
        return False

    try:
        prefix = int(postal_code[:4])
        return 1011 <= prefix <= 1098
    except:
        return False


def is_available(listing):
    """
    Filter onder bod / verkocht
    """
    status = listing.get("status", "")
    if not status:
        return False
    status = status.strip().lower()
    return "beschikbaar" in status or "available" in status



def transform_listing(listing):
    return {
        "id": listing.getID(),
        "address": listing['title'],
        "neighbourhood": listing.get("neighbourhood"),
        "city": listing.get("city"),
        "price": listing.get("price"),
        "surface_m2": listing.get("living_area"),
        "bedrooms": listing.get("bedrooms"),
        "url": f"funda.nl{listing.get('detail_url')}",
        "status": "nieuw"
    }

def main():
    print("Fetching existing houses...")
    existing_ids = get_existing_ids()

    print("Fetching listings from Funda...")
    listings = fetch_funda_listings(LOCATION,
                                        OFFERING_TYPE,
                                        PRICE_MAX,
                                        PRICE_MIN,
                                        AREA_MIN,
                                        AREA_MAX,
                                        PLOT_MIN,
                                        PLOT_MAX,
                                        OBJECT_TYPE,
                                        ENERGY_LABEL )

    new_count = 0
    list_count = 0

    for listing in listings:
        print(f"Listing number {list_count}: {vars(listing)}")  # Print volledige listing data
        list_count += 1

        # ---- Extra filtering in Python ----
        if listing['price'] > PRICE_MAX:
            print("Filtered: Asking price too high")
            print(listing['price'])
            continue

        if listing["living_area"] < AREA_MIN:
            print("Filtered: Living area too small")
            print(listing["living_area"])
            continue

        if not is_within_ring(listing['postcode']):
            print("Filtered: Not within ring")
            print(listing['postcode'])
            continue

        # if not is_available(listing):
        #     print("not available")
        #     print("Status:", listing.get("status", ""))
        #     continue

        if listing.getID() in existing_ids:
            print("Filtered: Already exists in database")
            continue


        house_data = transform_listing(listing)
        print("Inserting new house:", house_data)
        supabase.table("houses").insert(house_data).execute()
        new_count += 1

    print(f"Inserted {new_count} new houses.")


if __name__ == "__main__":
    main()