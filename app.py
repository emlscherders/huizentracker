import streamlit as st
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

# -----------------------------
# CONFIG & DATABASE CONNECTION
# -----------------------------

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

STATUS_OPTIONS = [
    "nieuw",
    "niet geïnteresseerd",
    "on hold",
    "bericht gestuurd",
    "bezichtiging gepland",
    "bezichtiging geweest",
    "niet geboden",
    "bod gedaan",
    "bod niet geaccepteerd",
    "bod geaccepteerd"
]

# -----------------------------
# HELPERS
# -----------------------------

def update_status(house_id, new_status):
    supabase.table("houses").update(
        {
            "status": new_status,
            "last_updated": datetime.utcnow().isoformat()
        }
    ).eq("id", house_id).execute()


def get_all_houses():
    return supabase.table("houses").select("*").execute().data


def status_color(status):
    colors = {
        "nieuw": "#28FE02",
        "bericht gestuurd": "#F63BF3",
        "bezichtiging gepland": "#FF9900",
        "bezichtiging geweest": "#0BD2F5",
        "bod gedaan": "#3B3EF6",
        "bod geaccepteerd": "#22C55E",
        "niet geïnteresseerd": "#EF4444",
        "niet geboden": "#EF4444",
        "bod niet geaccepteerd": "#EF4444",
        "on hold": "#5E5E5E"
    }
    return colors.get(status, "white")


# -----------------------------
# PAGE 1 — Nieuwe huizen
# -----------------------------

def page_new_houses():
    st.title("🆕 Nieuwe Huizen")

    houses = supabase.table("houses") \
        .select("*") \
        .eq("status", "nieuw") \
        .execute().data

    if not houses:
        st.info("Geen nieuwe huizen gevonden.")
        return

    for house in houses:
        st.divider()

        st.subheader(house["address"])
        st.write(f"💰 € {house['price']}")
        st.write(f"📏 {house['surface_m2']} m² · {house['bedrooms']} slaapkamers")

        st.markdown(f"[🔗 Bekijk op Funda]({house['url']})")

        # POST style form
        with st.form(key=f"form_{house['id']}"):
            current_index = STATUS_OPTIONS.index(house["status"]) \
                if house["status"] in STATUS_OPTIONS else 0

            new_status = st.selectbox(
                "Status wijzigen",
                STATUS_OPTIONS,
                index=current_index
            )

            submitted = st.form_submit_button("Opslaan")

            if submitted and new_status != house["status"]:
                update_status(house["id"], new_status)
                st.success("Status bijgewerkt!")
                st.rerun()


# -----------------------------
# PAGE 2 — Dashboard overzicht
# -----------------------------

def page_overview():
    st.title("📊 Overzicht")

    data = get_all_houses()

    if not data:
        st.info("Geen data beschikbaar.")
        return

    df = pd.DataFrame(data)

    df = df[["address", "status","price", "url"]]

    df = df.rename(columns={
        "address": "Straat",
        "status": "Status",
        "price": "Vraagprijs",
         "url": "Link",
    })

    def style_status(val):
        return f"background-color: {status_color(val)}"

    styled = df.style.applymap(style_status, subset=["Status"])

    st.dataframe(styled, use_container_width=True)


# -----------------------------
# MAIN APP
# -----------------------------

def main():
    st.sidebar.title("🏠 Huizen Tracker")

    page = st.sidebar.radio(
        "Navigation",
        ["🆕 Nieuwe huizen", "📊 Overzicht"]
    )

    if page.startswith("🆕"):
        page_new_houses()
    else:
        page_overview()


if __name__ == "__main__":
    main()