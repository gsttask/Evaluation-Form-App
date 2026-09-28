import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# Page Configuration (Mobile aur Desktop dono ke liye Responsive UI)
st.set_page_config(page_title="Sales Update Form", page_icon="📊", layout="centered")

# --- Streamlit Secrets ya Local JSON se Google Sheets Connection ---
@st.cache_resource
def connect_to_gsheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Streamlit Cloud par Secrets se credentials uthayega
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        # Local test karne ke liye 'credentials.json' file use karein
        credentials = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    
    client = gspread.authorize(credentials)
    # Aapki Sheet ka Title "Github" hai (Screenshot ke hisab se)
    sheet = client.open("Github")
    return sheet

try:
    spreadsheet = connect_to_gsheet()
    sheet1 = spreadsheet.worksheet("Sheet1")
    sheet2 = spreadsheet.worksheet("Sheet2")
except Exception as e:
    st.error("Google Sheets se connect nahi ho paya. Credentials verify karein.")
    st.stop()

# --- Session State Management ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "abm_name" not in st.session_state:
    st.session_state["abm_name"] = ""

# Custom CSS PWA / Mobile View ke liye
st.markdown("""
    <style>
    .main { padding: 1rem; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #0080FF; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 ABM Sales Reporting App")

# --- LOGIN PAGE ---
if not st.session_state["logged_in"]:
    st.subheader("🔑 ABM Login")
    
    login_input = st.text_input("Login ID")
    password_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if login_input and password_input:
            # Sheet1 se data read karke login match karna
            users_data = sheet1.get_all_records()
            df_users = pd.DataFrame(users_data)
            
            # String comparison ke liye columns clean karna
            df_users['Login'] = df_users['Login'].astype(str).str.strip()
            df_users['Password'] = df_users['Password'].astype(str).str.strip()
            
            matched_user = df_users[(df_users['Login'] == str(login_input).strip()) & 
                                    (df_users['Password'] == str(password_input).strip())]
            
            if not matched_user.empty:
                st.session_state["logged_in"] = True
                st.session_state["abm_name"] = matched_user.iloc[0]['ABM Name']
                st.success(f"Welcome, {st.session_state['abm_name']}!")
                st.rerun()
            else:
                st.error("Galat Login ID ya Password!")
        else:
            st.warning("Kripya Login ID aur Password dono dalein.")

# --- FORM PAGE (After Successful Login) ---
else:
    st.sidebar.write(f"Logged in as: **{st.session_state['abm_name']}**")
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["abm_name"] = ""
        st.rerun()

    st.subheader(f"📝 Sales Entry Form - {st.session_state['abm_name']}")
    
    with st.form("sales_form", clear_on_submit=True):
        budget_sale = st.number_input("Budget Sale Value (₹)", min_value=0.0, step=100.0)
        month_sale = st.number_input("Month Sale Value (₹)", min_value=0.0, step=100.0)
        
        submit_btn = st.form_submit_button("Submit Data")
        
        if submit_btn:
            if budget_sale >= 0 and month_sale >= 0:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Sheet2 me Nayi Entry add karna
                # Columns: Timestamp | ABM Name | Budget sale | Month sale
                new_row = [current_time, st.session_state['abm_name'], budget_sale, month_sale]
                sheet2.append_row(new_row)
                
                st.balloons()
                st.success("✅ Data Google Sheet me safaltapurvak save ho gaya!")
            else:
                st.error("Kripya sahi values dalein.")