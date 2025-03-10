import streamlit as st
import requests
from openai import OpenAI
import os
from dotenv import load_dotenv
import pandas as pd

def get_ngrok_url():
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels")
        data = response.json()
        public_url = data["tunnels"][0]["public_url"]  # Ambil URL pertama
        if not public_url.startswith(("http://", "https://")):
            public_url = f"https://{public_url}"  # Tambahkan skema jika tidak ada
        return public_url
    except Exception as e:
        st.error(f"Error mengambil URL ngrok: {e}")
        return None

BACKEND_URL = get_ngrok_url()

if not BACKEND_URL:
    st.error("Tidak dapat mengambil URL backend. Pastikan ngrok berjalan.")
    st.stop()  # Hentikan aplikasi Streamlit jika URL tidak valid

def register_user(username, password):
    try:
        response = requests.post(f"{BACKEND_URL}/register", json={"username": username, "password": password})
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat menghubungi backend: {e}")
        return None

def login_user(username, password):
    try:
        auth = (username, password)
        response = requests.post(f"{BACKEND_URL}/login", auth=auth)
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat menghubungi backend: {e}")
        return None


def predict_risk(data, username, password):
    auth = (username, password)
    response = requests.post(f"{BACKEND_URL}/predict", json=data, auth=auth)
    return response

def get_logs(username, password):
    auth = (username, password)
    response = requests.get(f"{BACKEND_URL}/log", auth=auth)
    return response

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "password" not in st.session_state:
    st.session_state["password"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

st.title("Aplikasi Prediksi Risiko Kredit dan Chat dengan AI")

menu = st.sidebar.selectbox("Menu", ["Register", "Login", "Predict", "Logs", "Chat with AI"])

if menu == "Register":
    st.header("Daftar Pengguna Baru")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if username and password:
            response = register_user(username, password)
            if response.status_code == 200:
                st.success("User registered successfully")
            else:
                st.error(f"Terjadi kesalahan saat mendaftarkan pengguna: {response.text}")
        else:
            st.error("Username dan password harus diisi")

elif menu == "Login":
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username and password:
            response = login_user(username, password)
            if response.status_code == 200:
                data = response.json()
                if "message" in data and data["message"] == "Login successful":
                    st.success("Login berhasil!")
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.session_state["password"] = password
                    st.session_state["user_id"] = data["user_id"]
                else:
                    st.error("Login gagal. Periksa username dan password Anda.")
            else:
                st.error(f"Login gagal: {response.text}")
        else:
            st.error("Username dan password harus diisi")

elif menu == "Predict":
    st.header("Prediksi Risiko Kredit")
    if not st.session_state.get("logged_in"):
        st.warning("Silakan login terlebih dahulu.")
    else:
        income = st.number_input("Income", min_value=0)
        age = st.number_input("Age", min_value=0)
        experience = st.number_input("Experience", min_value=0)
        married_single = st.selectbox("Married/Single", ["married", "single"])
        house_ownership = st.selectbox("House Ownership", ["rented", "norent_noown", "owned"])
        car_ownership = st.selectbox("Car Ownership", ["no", "yes"])
        profession = st.text_input("Profession")
        city = st.text_input("City")
        state = st.text_input("State")
        current_job_yrs = st.number_input("Current Job Years", min_value=0)
        current_house_yrs = st.number_input("Current House Years", min_value=0)
        
        if st.button("Predict"):
            data = {
                "Income": income,
                "Age": age,
                "Experience": experience,
                "Married_Single": married_single,
                "House_Ownership": house_ownership,
                "Car_Ownership": car_ownership,
                "Profession": profession,
                "CITY": city,
                "STATE": state,
                "CURRENT_JOB_YRS": current_job_yrs,
                "CURRENT_HOUSE_YRS": current_house_yrs
            }
            response = predict_risk(data, st.session_state["username"], st.session_state["password"])
            if response.status_code == 200:
                data = response.json()
                if "Risk_Flag" in data:
                    st.success(f"Predicted Risk Flag: {data['Risk_Flag']}")
                else:
                    st.error(data.get("detail", "Terjadi kesalahan saat melakukan prediksi"))
            else:
                st.error(f"Terjadi kesalahan saat melakukan prediksi: {response.text}")

elif menu == "Logs":
    st.header("Log Prediksi")
    if not st.session_state.get("logged_in"):
        st.warning("Silakan login terlebih dahulu.")
    else:
        if st.button("Get Logs"):
            response = get_logs(st.session_state["username"], st.session_state["password"])
            if response.status_code == 200:
                logs = response.json()
                if isinstance(logs, list):
                    df = pd.DataFrame(logs)
                    st.subheader("Tabel Log Prediksi (Interaktif)")
                    st.dataframe(df)
                else:
                    st.error(logs.get("detail", "Terjadi kesalahan saat mengambil log"))
            else:
                st.error(f"Terjadi kesalahan saat mengambil log: {response.text}")
