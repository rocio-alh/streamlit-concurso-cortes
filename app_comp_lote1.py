import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Simulador de puntuación - Cortes Castilla y León (Lote 1)")

# === Parámetros del lote ===
PL = 460000  # Presupuesto base sin IVA
U1_precio = PL
U2_precio = 0.8 * PL
P_max_precio = 45

U1_garantia = 3
U2_garantia = 5
P_max_garantia = 10

P_tecnicos_max = 37

# === Entradas del usuario ===
st.header("✍️ Introduce tu oferta")

col1, col2 = st.columns(2)
with col1:
    precio_ofertado = st.number_input("💰 Tu precio ofertado (€)", min_value=0.0, step=100.0, format="%.2f")
with col2:
    garantia = st.number_input("📆 Años de garantía extendida", min_value=0.0, step=0.5)

# === Validación ===
if precio_ofertado == 0:
    st.warning("Introduce un precio ofertado válido.")
    st.stop()

# === Cálculo puntuación económica ===
if precio_ofertado >= U1_precio:
    P_precio = 0
elif precio_ofertado <= U2_precio:
    P_precio = P_max_precio
else:
    P_precio = P_max_precio * (U1_precio - precio_ofertado) / (U1_precio - U2_precio)

# === Cálculo puntuación garantía ===
if garantia <= U1_garantia:
    P_garantia = 0
elif garantia >= U2_garantia:
    P_garantia = P_max_garantia
else:
    P_garantia = P_max_garantia * (garantia - U1_garantia) / (U2_garantia - U1_garantia)

# === Criterios técnicos subjetivos ===
st.header("📋 Evaluación técnica subjetiva")

criterios = {
    "a) Conectividad": 8,
    "b) Rendimiento": 8,
    "c) Alta disponibilidad": 4,
    "d) Interoperabilidad": 6,
    "e) Seguridad": 4,
    "f) Mantenibilidad": 4,
    "g) Escalabilidad": 3,
    "h) Plan de puesta en marcha": 3,
    "i) Plan de formación": 2,
    "j) Compromisos soporte técnico": 3
}

puntos_tecnicos = 0
for crit, max_pts in criterios.items():
    puntos_tecnicos += st.slider(crit, 0, max_pts, max_pts)

# === Simulación de ofertas de competidores ===
st.header("🏁 Simulación de empresas competidoras")

col1, col2 = st.columns(2)
with col1:
    num_empresas = st.number_input("Número total de ofertas (incluyéndote)", min_value=2, value=5, step=1)
with col2:
    distribucion = st.selectbox("Distribución de precios simulados", ["Uniforme", "Normal", "Triangular"])

bajada_max = st.slider("Bajada máxima esperada respecto al PL (%)", 1, 50, 20)
min_precio_sim = PL * (1 - bajada_max / 100)

# Simulaciones
num_competidores = num_empresas - 1
np.random.seed(42)

if distribucion == "Uniforme":
    precios_comp = np.random.uniform(min_precio_sim, PL, size=num_competidores)
elif distribucion == "Normal":
    media = (PL + min_precio_sim) / 2
    std_dev = (PL - min_precio_sim) / 6
    precios_comp = np.random.normal(loc=media, scale=std_dev, size=num_competidores)
    precios_comp = np.clip(precios_comp, min_precio_sim, PL)
elif distribucion == "Triangular":
    precios_comp = np.random.triangular(min_precio_sim, (min_precio_sim + PL) / 2, PL, size=num_competidores)

# Juntar precios
precios_finales = np.append(precios_comp, precio_ofertado)
nombres_empresas = [f"Empresa {i+1}" for i in range(num_empresas - 1)] + ["Tú"]

# === Puntuaciones para cada empresa ===
tabla = []

for nombre, precio in zip(nombres_empresas, precios_finales):
    # Económica
    if precio >= U1_precio:
        p_precio = 0
    elif precio <= U2_precio:
        p_precio = P_max_precio
    else:
        p_precio = P_max_precio * (U1_precio - precio) / (U1_precio - U2_precio)

    # Garantía
    if nombre == "Tú":
        g = garantia
    else:
        g = np.random.uniform(U1_garantia, U2_garantia + 1)

    if g <= U1_garantia:
        p_garantia = 0
    elif g >= U2_garantia:
        p_garantia = P_max_garantia
    else:
        p_garantia = P_max_garantia * (g - U1_garantia) / (U2_garantia - U1_garantia)

    # Técnicos (solo para ti, el resto aleatorio)
    if nombre == "Tú":
        p_tecnico = puntos_tecnicos
    else:
        p_tecnico = np.random.randint(20, P_tecnicos_max + 1)

    total = p_precio + p_garantia + p_tecnico

    tabla.append({
        "Empresa": nombre,
        "Precio ofertado (€)": round(precio, 2),
        "Garantía (años)": round(g, 2),
        "Económico": round(p_precio, 2),
        "Garantía": round(p_garantia, 2),
        "Técnicos": round(p_tecnico, 2),
        "Total": round(total, 2)
    })

# === Mostrar tabla ordenada ===
df = pd.DataFrame(tabla).sort_values("Total", ascending=False).reset_index(drop=True)
df.index += 1
st.dataframe(df, use_container_width=True)

# === Resultado final destacado para ti ===
st.subheader("🎯 Tu puntuación final")
st.success(f"**Total: {round(P_precio + P_garantia + puntos_tecnicos, 2)} puntos sobre 100.**")
