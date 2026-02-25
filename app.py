import streamlit as st
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

st.markdown("""
<style>

/* Maak kolommen dichter bij elkaar */
.block-container {
    padding-top: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* Maak kaarten compacter */
.kanban-card {
    background-color: #111827;
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 12px;
    border: 1px solid #2D3748;
}

/* Titel kleiner */
.kanban-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 6px;
}

/* Kleine tekst */
.kanban-meta {
    font-size: 14px;
    margin-bottom: 4px;
}

/* Status badge */
.status-badge {
    font-size: 12px;
    padding: 4px 8px;
    border-radius: 6px;
    font-weight: 600;
    display: inline-block;
    margin-bottom: 8px;
}

</style>
""", unsafe_allow_html=True)

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
if "editing_house" not in st.session_state:
    st.session_state.editing_house = None
def page_overview():
    st.title("🏗️ Kanban Overzicht")

    # ---------- Global font fix ----------
    st.markdown("""
    <style>
    * {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

    data = get_all_houses()

    if not data:
        st.info("Geen data beschikbaar.")
        return

    df = pd.DataFrame(data)

    kanban_columns = {
        "🆕 Nieuw": ["nieuw"],
        "👀 Bezichtiging": [
            "bezichtiging gepland",
            "bericht gestuurd",
            "bezichtiging geweest"
        ],
        "💰 Bieden": ["bod gedaan"],
        "❌ Afgevallen": [
            "niet geïnteresseerd",
            "niet geboden",
            "bod niet geaccepteerd"
        ],
        "🏆 JAVA PALACE": ["bod geaccepteerd"]
    }

    # ---------- Sorting rule for bezichtiging ----------
    def bezichtiging_sort_key(status):
        priority = {
            "bezichtiging gepland": 0,
            "bericht gestuurd": 1,
            "bezichtiging geweest": 2
        }
        return priority.get(status, 99)

    cols = st.columns([1,1,1,1,1], gap="small")

    for col, (column_name, statuses) in zip(cols, kanban_columns.items()):
        with col:
            st.subheader(column_name)

            filtered = df[df["status"].isin(statuses)]

            # Sort only in bezichtiging column
            if column_name == "👀 Bezichtiging":
                filtered = filtered.sort_values(
                    by="status",
                    key=lambda x: x.map(bezichtiging_sort_key)
                )

            for _, house in filtered.iterrows():

                badge_color = status_color(house["status"])

                card_html = f"""
                <a href="{house['url']}" target="_blank" style="text-decoration:none;">
                    <div style="
                        position: relative;
                
                        background: rgba(255,255,255,0.55);
                        backdrop-filter: blur(14px);
                        -webkit-backdrop-filter: blur(14px);
                
                        border-radius: 18px;
                        border: 1px solid rgba(229,231,235,0.6);
                
                        padding: 16px;
                
                        cursor: pointer;
                        transition: all 0.25s ease;
                
                        font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                
                        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
                    "
                    onmouseover="this.style.transform='translateY(-4px)'"
                    onmouseout="this.style.transform='translateY(0px)'">
                
                        <!-- Status badge rechtsboven -->
                        <div style="
                            position:absolute;
                            top:12px;
                            right:12px;
                
                            font-size:11px;
                            font-weight:600;
                
                            padding:4px 8px;
                            border-radius:8px;
                
                            background:{badge_color};
                            color:black;
                        ">
                            {house["status"]}
                        </div>
                
                        <div style="
                            font-size:16px;
                            font-weight:600;
                            margin-bottom:10px;
                            margin-top:6px;
                            color:#111827;
                            line-height:1.35;
                            padding-right:60px;
                        ">
                            {house["address"]}
                        </div>
                
                        <div style="
                            font-size:14px;
                            color:#374151;
                            line-height:1.4;
                        ">
                            💰 € {house["price"]} · 📏 {house["surface_m2"]} m² · {house["bedrooms"]} slpk
                        </div>
                
                    </div>
                </a>
                """

                components.html(card_html, height=140, scrolling=False)

                # ---------- Klikbare status badge ----------
                if st.button(
                    house["status"],
                    key=f"badge_{house['id']}",
                    help="Klik om status te wijzigen"
                ):
                    st.session_state.editing_house = house["id"]


                # ---------- Popup status selector ----------
                if st.session_state.editing_house == house["id"]:
                
                    new_status = st.selectbox(
                        "Wijzig status",
                        STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(house["status"]),
                        key=f"popup_status_{house['id']}"
                    )

                    # Auto-save zonder flash rerun
                    if new_status != house["status"]:
                    
                        update_status(house["id"], new_status)

                        # Update session state lokaal zodat UI niet flasht
                        house["status"] = new_status

                        st.toast("✅ Status opgeslagen", icon="✅")

                        st.session_state.editing_house = None
                # st.selectbox(
                #     "",
                #     STATUS_OPTIONS,
                #     index=STATUS_OPTIONS.index(house["status"]),
                #     key=f"kanban_{house['id']}",
                #     label_visibility="collapsed"
                # )
                

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