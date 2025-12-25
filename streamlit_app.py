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

# --- FUNKTIONER FÖR ATT LÄSA/SKRIVA ---
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
    # Gör om datum till strängar innan vi sparar till JSON
    df_to_save = df.copy()
    df_to_save['Datum'] = df_to_save['Datum'].astype(str)
    json_data = df_to_save.to_dict(orient="records")
    requests.put(URL, headers=HEADERS, json=json_data)

# --- AUTO-GENERERA FREDAGAR ---
df = load_data()
today = datetime.now().date()

# Skapa lista på 52 fredagar framåt
fridays = []
current = today + timedelta(days=(4 - today.weekday() + 7) % 7)
for _ in range(52):
    fridays.append(current)
    current += timedelta(days=7)

# Kolla om datum saknas
existing_dates = set(df['Datum']) if not df.empty else set()
missing = [f for f in fridays if f not in existing_dates]

if missing:
    new_rows = pd.DataFrame([{"Datum": f, "Khatib": "Ej bokat"} for f in missing])
    df = pd.concat([df, new_rows]).sort_values("Datum").reset_index(drop=True)
    save_data(df)
    st.rerun()

# --- DESIGN ---
st.title("🕌 Khutba-schema")
st.markdown("---")

df_view = df[df['Datum'] >= today].sort_values("Datum")

def style_row(row):
    val = row['Khatib']
    if val == ORDINARIE[0]: return ['background-color: #1d314f'] * 2
    if val == ORDINARIE[1]: return ['background-color: #064724'] * 2
    if val == ORDINARIE[2]: return ['background-color: #540141'] * 2
    if val == "Ej bokat": return ['color: #999'] * 2
    return ['background-color: #784302'] * 2 # Gäst

st.dataframe(
    df_view.style.apply(style_row, axis=1),
    use_container_width=True,
    hide_index=True,
    column_config={"Datum": st.column_config.DateColumn("Fredag", format="D MMM"), "Khatib": "Talare"}
)

# --- ADMIN ---
with st.expander("Admin-inloggning"):
    kod = st.text_input("Kod", type="password")
    if kod == PIN_KOD:
        date_select = st.selectbox("Välj datum", df_view['Datum'])
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
