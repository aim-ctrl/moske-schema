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

# Förbered data för visning
df_view = df[df['Datum'] >= today].sort_values("Datum").copy()
df_view['Fredag'] = df_view['Datum'].apply(lambda x: x.strftime("%d %b"))
df_view = df_view[['Fredag', 'Khatib']]

# CSS för att dölja index-numreringen (första kolumnen i st.table)
st.markdown("""
    <style>
    /* Döljer den första kolumnen (index) i alla tabeller */
    thead tr th:first-child {display:none}
    tbody tr th:first-child {display:none}
    
    /* Gör tabellen full bredd */
    div[data-testid="stTable"] {
        width: 100%;
    }
    
    /* Valfritt: Gör texten i tabellen lite större */
    td {
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

# Visa tabellen
st.table(df_view)
