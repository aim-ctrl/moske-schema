import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- KONFIGURATION ---
BIN_ID = st.secrets["JSONBIN_BIN_ID"]
API_KEY = st.secrets["JSONBIN_API_KEY"]
PIN_KOD = st.secrets["PIN_KOD"]
URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {"X-Master-Key": API_KEY, "Content-Type": "application/json"}

ORDINARIE = ["Mohammad Adlouni", "Hajj Adnan", "Akram"]

st.set_page_config(page_title="Khutba-schema", layout="centered")

# --- FUNKTIONER ---
def load_data():
    try:
        res = requests.get(f"{URL}/latest", headers=HEADERS)
        if res.status_code == 200:
            data = res.json()["record"]
            df = pd.DataFrame(data)
            if not df.empty:
                df['Datum'] = pd.to_datetime(df['Datum']).dt.date
            return df
    except Exception as e:
        st.error(f"Kunde inte ladda data: {e}")
    return pd.DataFrame(columns=["Datum", "Khatib"])

def save_data(df):
    df_to_save = df.copy()
    df_to_save['Datum'] = df_to_save['Datum'].astype(str)
    json_data = df_to_save.to_dict(orient="records")
    requests.put(URL, headers=HEADERS, json=json_data)

# --- LOGIK FÖR DATUM ---
df = load_data()
today = datetime.now().date()

fridays = []
current = today + timedelta(days=(4 - today.weekday() + 7) % 7)
if today.weekday() == 4:
    current = today

for _ in range(52):
    fridays.append(current)
    current += timedelta(days=7)

existing_dates = set(df['Datum']) if not df.empty else set()
missing = [f for f in fridays if f not in existing_dates]

if missing:
    new_rows = pd.DataFrame([{"Datum": f, "Khatib": "Ej bokat"} for f in missing])
    df = pd.concat([df, new_rows]).sort_values("Datum").reset_index(drop=True)
    save_data(df)
    st.rerun()

# --- MODAL (POPUP) FÖR EDITERING ---
@st.dialog("Redigera schema ✎")
def edit_schema_dialog():
    st.write("Ange PIN-kod för att ändra.")
    input_kod = st.text_input("PIN-kod", type="password")
    
    if input_kod == PIN_KOD:
        st.divider()
        df_future = df[df['Datum'] >= today].sort_values("Datum")
        date_select = st.selectbox("Välj datum", df_future['Datum'])
        mode = st.radio("Vem talar?", ["Ordinarie", "Gäst", "Rensa"])
        
        if mode == "Ordinarie":
            name = st.selectbox("Namn", ORDINARIE)
        elif mode == "Gäst":
            name = st.text_input("Namn på gäst")
        else:
            name = "Ej bokat"
            
        if st.button("Spara"):
            df.loc[df['Datum'] == date_select, 'Khatib'] = name
            save_data(df)
            st.success("Sparat!")
            st.rerun()
    elif input_kod != "":
        st.error("Fel kod.")

# --- UI DESIGN ---
st.title("🕌 Khutba-schema")

col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.subheader("Aktuellt schema")
with col2:
    if st.button("✎ Edit"):
        edit_schema_dialog()

st.markdown("---")

# --- TABELL-STYLING ---
df_view = df[df['Datum'] >= today].sort_values("Datum").copy()
df_view['Fredag'] = df_view['Datum'].apply(lambda x: x.strftime("%d %b"))
display_df = df_view[['Fredag', 'Khatib']]

def apply_styles(row):
    val = row['Khatib']
    styles = [''] * len(row)
    if val == ORDINARIE[0]: bg = "background-color: #1d314f; color: white;"
    elif val == ORDINARIE[1]: bg = "background-color: #064724; color: white;"
    elif val == ORDINARIE[2]: bg = "background-color: #540141; color: white;"
    elif val == "Ej bokat": bg = "color: #999;"
    else: bg = "background-color: #784302; color: white;" # Gäst
    
    return [bg] * len(row)

# Skapa den stylade tabellen och dölj index
styled_html = (
    display_df.style
    .apply(apply_styles, axis=1)
    .hide(axis='index')
    .set_table_attributes('style="width:100%; border-collapse: collapse;"')
    .to_html()
)

# Lägg till lite extra CSS för att snygga till cellerna
st.markdown(f"""
    <style>
        table {{ width: 100%; }}
        th {{ text-align: left; padding: 10px; border-bottom: 2px solid #ccc; }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; }}
    </style>
    {styled_html}
""", unsafe_allow_html=True)
