import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- KONFIGURATION (Ändra dessa) ---
ORDINARIE = ["Mohammad Adlouni", "Hajj Adnan", "Akram"] # Dina tre ordinarie
PIN_KOD = "3090" # Din fyrsiffriga kod

st.set_page_config(page_title="Khutba-schema", layout="centered")

# --- ANSLUTNING TILL GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # Hämtar data och ser till att Datum-kolumnen är i rätt format
    df = conn.read(ttl=0) 
    if not df.empty:
        df['Datum'] = pd.to_datetime(df['Datum']).dt.date
    return df

# --- LOGIK FÖR ATT FYLLA PÅ FREDAGAR ---
def fill_missing_fridays(df):
    today = datetime.now().date()
    # Skapa lista på alla fredagar 1 år framåt
    all_fridays = []
    # Hitta nästa fredag
    current = today + timedelta(days=(4 - today.weekday() + 7) % 7)
    for _ in range(52):
        all_fridays.append(current)
        current += timedelta(days=7)
    
    existing_dates = set(df['Datum']) if not df.empty else set()
    new_entries = []
    
    for friday in all_fridays:
        if friday not in existing_dates:
            new_entries.append({"Datum": friday, "Khatib": "Ej bokat"})
    
    if new_entries:
        new_df = pd.concat([df, pd.DataFrame(new_entries)], ignore_index=True)
        new_df = new_df.sort_values("Datum")
        conn.update(data=new_df)
        return new_df
    return df

# --- HÄMTA OCH UPPDATERA DATA ---
try:
    df = get_data()
except:
    # Om arket är helt tomt, skapa en start-dataframe
    df = pd.DataFrame(columns=["Datum", "Khatib"])

df = fill_missing_fridays(df)

# --- DESIGN OCH VISNING ---
st.title("🕌 Khutba-schema")
st.write("Schema för fredagsbönen (Khutba)")

# Filtrera så vi bara ser dagens datum och framåt
today = datetime.now().date()
df_view = df[df['Datum'] >= today].sort_values("Datum")

# Färgkodningsfunktion
def apply_color(row):
    val = row['Khatib']
    if val == ORDINARIE[0]:
        return ['background-color: #d1e7dd'] * len(row) # Grön
    elif val == ORDINARIE[1]:
        return ['background-color: #cfe2ff'] * len(row) # Blå
    elif val == ORDINARIE[2]:
        return ['background-color: #fff3cd'] * len(row) # Gul
    elif val == "Ej bokat":
        return ['color: #adb5bd'] * len(row)           # Grå text
    else:
        return ['background-color: #f8d7da'] * len(row) # Röd (Gäster)

# Visa tabellen
st.dataframe(
    df_view.style.apply(apply_color, axis=1),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Datum": st.column_config.DateColumn("Datum", format="D MMM YYYY"),
        "Khatib": "Khatib / Talare"
    }
)

# --- ADMIN SEKTION ---
st.markdown("---")
with st.expander("🔐 Admin: Redigera schema"):
    input_pin = st.text_input("Ange pinkod", type="password")
    
    if input_pin == PIN_KOD:
        st.success("Inloggad")
        
        # Välj datum från listan (endast de som visas i tabellen)
        date_to_update = st.selectbox("Välj fredag", df_view['Datum'])
        
        choice = st.radio("Vem ska hålla khutba?", ["Ordinarie", "Gäst", "Nollställ"])
        
        if choice == "Ordinarie":
            selected_khatib = st.selectbox("Välj namn", ORDINARIE)
        elif choice == "Gäst":
            selected_khatib = st.text_input("Skriv gästens namn")
        else:
            selected_khatib = "Ej bokat"
            
        if st.button("Spara ändring"):
            # Uppdatera i huvud-dataframe
            df.loc[df['Datum'] == date_to_update, 'Khatib'] = selected_khatib
            conn.update(data=df)
            st.toast(f"Uppdaterat {date_to_update}!")
            st.rerun()
    elif input_pin != "":
        st.error("Fel pinkod")
