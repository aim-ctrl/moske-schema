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
    res = requests.get(f"{URL}/latest", headers=HEADERS)
    if res.status_code == 200:
        data = res.json()["record"]
        df = pd.DataFrame(data)
        if not df.empty:
            df['Datum'] = pd.to_datetime(df['Datum']).dt.date
        return df
    return pd.DataFrame(columns=["Datum", "Khatib"])

def save_data(df):
    df_to_save = df.copy()
    df_to_save['Datum'] = df_to_save['Datum'].astype(str)
    json_data = df_to_save.to_dict(orient="records")
    requests.put(URL, headers=HEADERS, json=json_data)

# --- LOGIK FÖR DATUM ---
df = load_data()
today = datetime.now().date()

# Se till att vi har 52 veckor framåt
fridays = []
current = today + timedelta(days=(4 - today.weekday() + 7) % 7)
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
    st.write("Ange PIN-kod för att göra ändringar.")
    input_kod = st.text_input("Kod", type="password")
    
    if input_kod == PIN_KOD:
        st.divider()
        df_future = df[df['Datum'] >= today].sort_values("Datum")
        date_select = st.selectbox("Vilket datum vill du ändra?", df_future['Datum'])
        
        mode = st.radio("Vem talar?", ["Ordinarie", "Gäst", "Rensa"])
        name = ""
        
        if mode == "Ordinarie":
            name = st.selectbox("Välj namn", ORDINARIE)
        elif mode == "Gäst":
            name = st.text_input("Namn på gäst")
        else:
            name = "Ej bokat"
            
        if st.button("Spara ändring"):
            df.loc[df['Datum'] == date_select, 'Khatib'] = name
            save_data(df)
            st.success(f"Uppdaterat för {date_select}!")
            st.rerun()
    elif input_kod != "":
        st.error("Felaktig kod.")

# --- UI DESIGN ---
st.title(" 🕌 Khutba-schema")

# Rad med knapp för att öppna editering
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.subheader("Kommande fredagar")
with col2:
    if st.button("✎ Edit"):
        edit_schema_dialog()

st.markdown("---")

# Filtrera data för visning
df_view = df[df['Datum'] >= today].sort_values("Datum").copy()
df_view['Fredag'] = df_view['Datum'].apply(lambda x: x.strftime("%d %b"))
df_view = df_view[['Fredag', 'Khatib']]

# Visning med st.table för att undvika scrollbar (visar allt)
st.table(df_view)

# CSS för att snygga till tabellen lite (valfritt)
st.markdown("""
<style>
    div[data-testid="stTable"] {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)
