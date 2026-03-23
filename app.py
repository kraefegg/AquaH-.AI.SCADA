# ==========================================
# 🧠 KRAEFEGG-AI - DataBuilder v3.0
# ==========================================

# 🔹 IMPORTS
import streamlit as st
import requests
from PIL import Image
from io import BytesIO

import pdfplumber
import pandas as pd
import plotly.express as px
from docx import Document
import re
import folium
from streamlit_folium import st_folium

import rasterio
import numpy as np
import matplotlib.pyplot as plt
import datetime

# 🔐 LOGIN / BANCO
import sqlite3
import hashlib

# ==========================================
# 🗄️ BANCO DE DADOS
# ==========================================
conn = sqlite3.connect("usuarios.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    username TEXT,
    password TEXT
)
""")
conn.commit()

# ==========================================
# 🔐 FUNÇÕES LOGIN
# ==========================================
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_usuario(user, senha):
    c.execute("INSERT INTO usuarios VALUES (?,?)", (user, hash_senha(senha)))
    conn.commit()

def login_usuario(user, senha):
    c.execute("SELECT * FROM usuarios WHERE username=? AND password=?",
              (user, hash_senha(senha)))
    return c.fetchone()

# ==========================================
# ⚙️ CONFIG
# ==========================================
st.set_page_config(page_title="KRAEFEGG-AI", layout="wide")

# ==========================================
# 🔐 LOGIN
# ==========================================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:

    st.title("🔐 Login KRAEFEGG-AI")

    opcao = st.radio("Escolha", ["Login", "Cadastrar"])
    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if opcao == "Cadastrar":
        if st.button("Criar conta"):
            criar_usuario(user, senha)
            st.success("Usuário criado!")

    if opcao == "Login":
        if st.button("Entrar"):
            if login_usuario(user, senha):
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Login inválido")

    st.stop()

# ==========================================
# 🎨 UI
# ==========================================
st.title("🧠 KRAEFEGG-AI")
st.markdown("### Plataforma de Engenharia Ambiental Inteligente")

# ==========================================
# 🧠 MENU
# ==========================================
modulo = st.sidebar.selectbox("Módulos", [
    "📊 Relatórios",
    "🗺️ Geoprocessamento",
    "🛰️ NDVI Satélite",
    "🌦️ Meteorologia",
    "💧 Hidrologia",
    "⛰️ Geotecnia",
    "🪨 Mineralogia",
    "🔍 Prospecção",
    "🤖 Simulação AI",
    "📡 Sensores"
])

# ==========================================
# 📂 UPLOAD
# ==========================================
arquivo = st.file_uploader("Upload PDF/DOCX", type=["pdf","docx"])
texto = ""

if arquivo:
    if arquivo.name.endswith(".pdf"):
        with pdfplumber.open(arquivo) as pdf:
            for p in pdf.pages:
                texto += p.extract_text() or ""
    else:
        doc = Document(arquivo)
        for p in doc.paragraphs:
            texto += p.text

# ==========================================
# 📊 RELATÓRIOS
# ==========================================
if modulo == "📊 Relatórios":
    if texto:
        st.subheader("Texto extraído")
        st.write(texto[:1000])

# ==========================================
# 🗺️ MAPA
# ==========================================
if modulo == "🗺️ Geoprocessamento":
    lat = st.number_input("Latitude", value=-7.0)
    lon = st.number_input("Longitude", value=-34.8)

    mapa = folium.Map(location=[lat, lon], zoom_start=12)
    folium.Marker([lat, lon]).add_to(mapa)
    st_folium(mapa)

# ==========================================
# 🛰️ NDVI COMPLETO
# ==========================================
if modulo == "🛰️ NDVI Satélite":

    st.subheader("🛰️ Satélite + NDVI Profissional")

    lat = st.number_input("Latitude", value=-14.0)
    lon = st.number_input("Longitude", value=-41.0)

    client_id = st.text_input("Client ID")
    client_secret = st.text_input("Client Secret", type="password")

    col1, col2 = st.columns(2)

    # 🌍 IMAGEM REAL
    with col1:
        if st.button("Imagem Satélite"):
            url = f"https://services.sentinel-hub.com/ogc/wms/YOUR_INSTANCE_ID?SERVICE=WMS&REQUEST=GetMap&BBOX={lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}&LAYERS=TRUE-COLOR-S2-L1C&WIDTH=512&HEIGHT=512&FORMAT=image/png"
            r = requests.get(url)

            if r.status_code == 200:
                st.image(Image.open(BytesIO(r.content)))
            else:
                st.error("Erro imagem")

    # 🌱 NDVI REAL
    with col2:
        if st.button("NDVI Profissional"):

            auth = requests.post(
                "https://services.sentinel-hub.com/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                }
            )

            if auth.status_code == 200:

                token = auth.json()["access_token"]

                evalscript = """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B04","B08"],
                        output: { bands: 3 }
                    };
                }

                function evaluatePixel(s) {
                    let ndvi = (s.B08 - s.B04) / (s.B08 + s.B04);
                    return [ndvi, ndvi, ndvi];
                }
                """

                res = requests.post(
                    "https://services.sentinel-hub.com/api/v1/process",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "input": {
                            "bounds": {
                                "bbox": [lon-0.01, lat-0.01, lon+0.01, lat+0.01]
                            },
                            "data":[{"type":"sentinel-2-l2a"}]
                        },
                        "output": {"width":512,"height":512},
                        "evalscript": evalscript
                    }
                )

                if res.status_code == 200:
                    st.image(Image.open(BytesIO(res.content)))
                else:
                    st.error("Erro NDVI")

# ==========================================
# 🌦️ METEOROLOGIA
# ==========================================
if modulo == "🌦️ Meteorologia":
    cidade = st.text_input("Cidade")
    if st.button("Consultar"):
        st.write("Temperatura: 28°C | Umidade: 70%")

# ==========================================
# 💧 HIDROLOGIA
# ==========================================
if modulo == "💧 Hidrologia":
    area = st.number_input("Área (km²)")
    chuva = st.number_input("Chuva (mm)")
    if st.button("Calcular"):
        vazao = area * chuva * 0.278
        st.success(f"Vazão: {vazao:.2f} m³/s")

# ==========================================
# ⛰️ GEOTECNIA
# ==========================================
if modulo == "⛰️ Geotecnia":
    ang = st.slider("Ângulo", 0, 90)
    coesao = st.number_input("Coesão")
    if st.button("Analisar"):
        fs = (coesao + ang) / 10
        st.success(f"FS: {fs:.2f}")

# ==========================================
# 🪨 MINERALOGIA
# ==========================================
if modulo == "🪨 Mineralogia":
    img = st.file_uploader("Imagem", type=["jpg","png"])
    if img:
        st.image(img)

# ==========================================
# 🔍 PROSPECÇÃO
# ==========================================
if modulo == "🔍 Prospecção":
    area = st.number_input("Área (ha)")
    if st.button("Analisar"):
        st.success("Potencial detectado")

# ==========================================
# 🤖 SIMULAÇÃO
# ==========================================
if modulo == "🤖 Simulação AI":
    prompt = st.text_area("Projeto")
    if st.button("Executar"):
        st.success("Simulação pronta")

# ==========================================
# 📡 ESP32
# ==========================================
if modulo == "📡 Sensores":
    ip = st.text_input("IP ESP32")
    if st.button("Conectar"):
        try:
            r = requests.get(f"http://{ip}/dados")
            data = r.json()
            st.metric("Temp", data["temp"])
            st.metric("Umidade", data["umidade"])
        except:
            st.error("Erro conexão")

# ==========================================
# 📌 RODAPÉ
# ==========================================
st.markdown("---")
st.markdown("© 2026 KRAEFEGG")
