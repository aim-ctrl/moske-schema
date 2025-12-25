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

# Se till att vi har 52 fredagar (starta med idag om det är fredag)
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

# --- FÄRGKODNING VIA CSS/HTML ---
def get_row_style(khatib):
    if khatib == ORDINARIE[0]: return "background-color: #1d314f; color: white;"
    if khatib == ORDINARIE[1]: return "background-color: #064724; color: white;"
    if khatib == ORDINARIE[2]: return "background-color: #540141; color: white;"
    if khatib == "Ej bokat": return "color: #999;"
    return "background-color: #784302; color: white;" # Gäst

# Filtrera och bygg HTML-tabell
df_view = df[df['Datum'] >= today].sort_values("Datum")

html_table = """
<style>
    .custom-table { width: 100%; border-collapse: collapse; font-family: sans-serif; }
    .custom-table th { text-align: left; padding: 12px; border-bottom: 2px solid #444; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #eee; }
</style>
<table class="custom-table">
    <thead>
        <tr>
            <th>Fredag</th>
            <th>Talare</th>
        </tr>
    </thead>
    <tbody>
"""

for _, row in df_view.iterrows():
    style = get_row_style(row['Khatib'])
    datum_str = row['Datum'].strftime("%d %b")
    html_table += f"""
        <tr style="{style}">
            <td>{datum_str}</td>
            <td>{row['Khatib']}</td>
        </tr>
    """

html_table += "</tbody></table>"

# Rendera den färgkodade tabellen
st.markdown(html_table, unsafe_allow_html=True)
