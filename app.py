import streamlit as st
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

st.title("🏠 Huizen Tracker")

data = supabase.table("houses").select("*").execute()

for house in data.data:
    with st.container():
        st.subheader(house["address"])
        st.write(f"€ {house['price']}")
        st.write(f"{house['surface_m2']} m² · {house['bedrooms']} slaapkamers")
        st.markdown(f"[Bekijk op Funda]({house['url']})")

        new_status = st.selectbox(
            "Status",
            [
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
            ],
            index=0,
            key=house["id"]
        )

        if new_status != house["status"]:
            supabase.table("houses").update(
                {"status": new_status}
            ).eq("id", house["id"]).execute()