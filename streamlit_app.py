import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- KONFIGURATION ---
# Se till att dessa är tillagda i din .streamlit/secrets.toml eller på Streamlit Cloud
BIN_ID = st.secrets["JSONBIN_BIN_ID"]
API_KEY = st.secrets["JSONBIN_API_KEY"]
PIN_KOD = st.secrets["PIN_KOD"]
URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {"X-Master-Key": API_KEY, "Content-Type": "application/json"}

ORDINARIE = ["Mohammad Adlouni", "Hajj Adnan", "Akram"]

st.set_page_config(page_title="Khutba-schema", layout="centered")

# --- FUNKTIONER FÖR ATT LÄSA/SKRIVA ---
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
    # Konvertera datum till strängar för JSON-kompatibilitet
    df_to_save = df.copy()
    df_to_save['Datum'] = df_to_save['Datum'].astype(str)
    json_data = df_to_save.to_dict(orient="records")
    requests.put(URL, headers=HEADERS, json=json_data)

# --- LOGIK FÖR ATT GENERERA FREDAGAR ---
df = load_data()
today = datetime.now().date()

# Skapa lista på 52 fredagar framåt
fridays = []
# Hitta nästa fredag
current = today + timedelta(days=(4 - today.weekday() + 7) % 7)
for _ in range(52):
    fridays.append(current)
    current += timedelta(days=7)

# Uppdatera databasen om datum saknas
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
    st.write("Bekräfta med PIN-kod för att ändra bokning.")
    input_kod = st.text_input("PIN-kod", type="password")
    
    if input_kod == PIN_KOD:
        st.divider()
        # Endast framtida datum går att redigera
        df_future = df[df['Datum'] >= today].sort_values("Datum")
        date_select = st.selectbox("Välj fredag", df_future['Datum'])
        
        mode = st.radio("Typ av bokning", ["Ordinarie", "Gäst", "Rensa"])
        
        if mode == "Ordinarie":
            name = st.selectbox("Välj talare", ORDINARIE)
        elif mode == "Gäst":
            name = st.text_input("Skriv namn på gäst")
        else:
            name = "Ej bokat"
            
        if st.button("Spara ändringar"):
            # Uppdatera huvud-dataframe
            df.loc[df['Datum'] == date_select, 'Khatib'] = name
            save_data(df)
            st.success(f"Bokningen för {date_select} är nu sparad!")
            st.rerun()
    elif input_kod != "":
        st.error("Felaktig kod. Försök igen.")

# --- UI DESIGN ---
st.title("🕌 Khutba-schema")

# Header-rad med Edit-knapp
col1, col2 = st.columns([0.85, 0.15])
with col1:
    st.subheader("Schema för fredagsbön")
with col2:
    if st.button("✎ Edit"):
        edit_schema_dialog()

st.markdown("---")

# Förbered visnings-data
df_view = df[df['Datum'] >= today].sort_values("Datum").copy()
# Formatera datumet för snyggare visning (t.ex. "27 Dec")
df_view['Fredag'] = df_view['Datum'].apply(lambda x: x.strftime("%d %b"))
display_table = df_view[['Fredag', 'Khatib']]

# CSS för att dölja index-numreringen och göra tabellen snygg
st.markdown("""
    <style>
    /* Döljer första kolumnen (numreringen) i tabellen */
    thead tr th:first-child {display:none}
    tbody tr th:first-child {display:none}
    
    /* Tvingar tabellen att ta upp hela bredden */
    div[data-testid="stTable"] {
        width: 100%;
    }
    
    /* Gör texten lite tydligare */
    td {
        padding: 10px !important;
        font-size: 16px;
    }
    th {
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

# Visa tabellen (st.table skapar ingen scrollbar utan visar allt direkt)
st.table(display_table)
