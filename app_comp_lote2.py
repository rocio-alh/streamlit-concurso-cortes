# Simulador para el Lote 2 con análisis de sensibilidad
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Parámetros del lote 2 ---
presupuesto_base = 150000
PL = 150000
U1_precio = presupuesto_base
U2_precio = presupuesto_base * 0.80
P_max_precio = 45
P_max_garantia = 10
U1_garantia = 3
U2_garantia = 5

# --- Título ---
st.title("Simulador de puntuación - Lote 2 (Cortes de Castilla y León)")

# --- Entrada de oferta económica ---
st.header("1. Oferta económica")
oferta = st.number_input("Introduce tu oferta económica (€)", min_value=0.0, step=100.0)

# --- Entrada de garantía ---
st.header("2. Años de garantía extendida ofertada")
garantia = st.number_input("Introduce años de garantía extendida", min_value=0.0, step=0.5)

# --- Cálculo puntos por precio ---
if oferta <= U2_precio:
    P_precio = P_max_precio
elif oferta > U1_precio:
    P_precio = 0
else:
    P_precio = P_max_precio * (U1_precio - oferta) / (U1_precio - U2_precio)

# --- Cálculo puntos por garantía ---
if garantia <= U1_garantia:
    P_garantia = 0
elif garantia >= U2_garantia:
    P_garantia = P_max_garantia
else:
    P_garantia = P_max_garantia * (garantia - U1_garantia) / (U2_garantia - U1_garantia)

# --- Criterios técnicos con puntuación manual ---
st.header("3. Evaluación técnica (juicio de valor)")
criterios_tecnicos = {
    "a) Conectividad de puntos de acceso": 5,
    "b) NAC - Funcionalidad y prestaciones": 8,
    "c) Portal cautivo": 2,
    "d) Rendimiento WiFi": 3,
    "e) Rendimiento NAC": 3,
    "f) Alta disponibilidad": 2,
    "g) Interoperabilidad": 6,
    "h) Seguridad": 4,
    "i) Mantenibilidad": 3,
    "j) Escalabilidad": 1
}

puntos_tecnicos = 0
for crit, max_pts in criterios_tecnicos.items():
    puntos = st.slider(f"{crit} (0 - {max_pts} puntos)", 0, max_pts, int(max_pts / 2))
    puntos_tecnicos += puntos

# --- Otros criterios ---
st.subheader("Otros criterios subjetivos")
plan_implantacion = st.slider("Plan de implantación (0 - 3 puntos)", 0, 3, 1)
formacion = st.slider("Plan de formación (0 - 2 puntos)", 0, 2, 1)
soporte = st.slider("Soporte técnico (0 - 3 puntos)", 0, 3, 1)

otros_puntos = plan_implantacion + formacion + soporte

# --- Total ---
st.header("4. Resultado final")
total = P_precio + P_garantia + puntos_tecnicos + otros_puntos
st.success(f"Puntuación total estimada: {round(total, 2)} puntos")

# --- Análisis de sensibilidad ---
st.header("5. Análisis de sensibilidad del precio")
rango_analisis = st.number_input("Rango de variación (€)", min_value=500.0, value=5000.0, step=500.0)
paso = st.number_input("Paso (€)", min_value=10.0, value=100.0, step=10.0)

precios = np.arange(U2_precio - rango_analisis, U1_precio + paso, paso)
puntos = []
for p in precios:
    if p <= U2_precio:
        puntos.append(P_max_precio)
    elif p > U1_precio:
        puntos.append(0)
    else:
        puntos.append(P_max_precio * (U1_precio - p) / (U1_precio - U2_precio))

fig, ax = plt.subplots()
ax.plot(precios, puntos, color='blue')
ax.axvline(x=oferta, color='red', linestyle='--', label='Tu oferta')
ax.set_xlabel("Precio ofertado (€)")
ax.set_ylabel("Puntos (precio)")
ax.set_title("Análisis de sensibilidad del precio")
ax.grid(True)
ax.legend()
st.pyplot(fig)

# --- Simulación de presupuestos de competidores ---
st.header("6. Simulación de presupuestos de competidores")

num_ofertas = st.number_input("Número total de ofertas (incluyéndote)", min_value=2, value=5, step=1)
num_competidores = num_ofertas - 1

bajada_max = st.slider("Porcentaje máximo de bajada de la competencia (%)", 5, 50, 20)
distribucion = st.selectbox("Distribución de la bajada", ["Uniforme", "Normal", "Beta", "Triangular"])

# Calculamos los límites de bajada
rango = U1_precio - U2_precio
np.random.seed(42)

if distribucion == "Uniforme":
    simulados = np.random.uniform(low=U2_precio, high=U1_precio, size=num_competidores)
elif distribucion == "Normal":
    media = (U1_precio + U2_precio) / 2
    std = rango / 4
    simulados = np.random.normal(loc=media, scale=std, size=num_competidores)
    simulados = np.clip(simulados, U2_precio, U1_precio)
elif distribucion == "Beta":
    alpha = st.slider("Forma α (agresividad)", 1.0, 5.0, 2.0)
    beta_val = st.slider("Forma β (conservadurismo)", 1.0, 5.0, 2.0)
    beta_samples = np.random.beta(alpha, beta_val, size=num_competidores)
    simulados = U2_precio + beta_samples * rango
elif distribucion == "Triangular":
    modo = st.slider("Valor más probable (€)", float(U2_precio), float(U1_precio), float((U2_precio + U1_precio)/2))
    simulados = np.random.triangular(left=U2_precio, mode=modo, right=U1_precio, size=num_competidores)


presupuestos_simulados = [oferta] + list(simulados)
presupuestos_simulados.sort()


# Info al pie
st.caption("Simulación basada en criterios del Pliego - Lote 2.")
# --- Simulación de presupuestos de competidores ---

# --- Cálculo de puntuación total por empresa (precio + técnica aleatoria) ---
st.subheader("📈 Comparativa de puntuación total")

# Calcula puntuaciones económicas
def puntuacion_economica(p):
    if p <= U2_precio:
        return P_max_precio
    elif p > U1_precio:
        return 0
    else:
        return P_max_precio * (U1_precio - p) / (U1_precio - U2_precio)

puntos_economicos = [puntuacion_economica(p) for p in presupuestos_simulados]

# Simula puntuaciones técnicas para competidores (tú usas la tuya)
puntos_tecnicos_simulados = [puntos_tecnicos + otros_puntos if p == oferta else np.random.uniform(30, 45) for p in presupuestos_simulados]

# Total
puntuaciones_totales = [e + t for e, t in zip(puntos_economicos, puntos_tecnicos_simulados)]

# Mostrar tabla resumen
import pandas as pd
df_resultados = pd.DataFrame({
    "Oferta (€)": presupuestos_simulados,
    "Puntos económicos": puntos_economicos,
    "Puntos técnicos": puntos_tecnicos_simulados,
    "Puntuación total": puntuaciones_totales
})

st.dataframe(df_resultados)

# Gráfico
fig, ax = plt.subplots()
ax.scatter(df_resultados["Oferta (€)"], df_resultados["Puntuación total"], color='blue', label='Competidores')
ax.axvline(oferta, color='red', linestyle='--', label='Tu oferta')
ax.set_title("Puntuación total vs Precio ofertado")
ax.set_xlabel("Precio ofertado (€)")
ax.set_ylabel("Puntuación total")
ax.grid(True)
ax.legend()
st.pyplot(fig)
