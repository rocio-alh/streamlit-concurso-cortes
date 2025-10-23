import streamlit as st
import numpy as np
import pandas as pd

# =========================
# CONFIGURACIÓN INICIAL
# =========================
st.set_page_config(layout="wide")
st.title("Simulador completo de valoración - Modelo PA5/2025")

WEIGHTS = [0.58, 0.19, 0.23]  # L1, L2, L3

# ============================================================
# FUNCIONES DE UTILIDAD
# ============================================================
def calcular_puntuacion_precio(oferta, u1, u2, pmax):
    if oferta >= u1:
        return 0
    elif oferta <= u2:
        return pmax
    return pmax * (u1 - oferta) / (u1 - u2)

def calcular_puntuacion_garantia(garantia, u1, u2, pmax):
    if garantia <= u1:
        return 0
    elif garantia >= u2:
        return pmax
    return pmax * (garantia - u1) / (u2 - u1)

def simular_competidores(precio_min, precio_max, n, distribucion="Uniforme"):
    np.random.seed(42)
    if distribucion == "Uniforme":
        return np.random.uniform(precio_min, precio_max, n)
    elif distribucion == "Normal":
        media = (precio_min + precio_max) / 2
        std = (precio_max - precio_min) / 6
        precios = np.random.normal(media, std, n)
        return np.clip(precios, precio_min, precio_max)
    elif distribucion == "Triangular":
        return np.random.triangular(precio_min, (precio_min + precio_max) / 2, precio_max, n)
    return np.random.uniform(precio_min, precio_max, n)

# =========================
# DEFINICIÓN DE EMPRESAS (GLOBAL)
# =========================
st.header("🏢 Configuración de empresas participantes")

num_empresas = st.number_input(
    "Número total de empresas participantes (incluyéndote)",
    min_value=2, max_value=20, value=3, step=1, key="num_empresas"
)

empresas = []
for i in range(num_empresas):
    nombre_default = f"Empresa {chr(65 + i)}"  # Empresa A, B, C, ...
    nombre = st.text_input(f"Nombre de la empresa {i+1}", nombre_default, key=f"nombre_emp_{i}")
    empresas.append(nombre)

# Añadir usuario (EMCO) si no está
if "emco" not in empresas:
    empresas.append("emco")

# Guardar lista global en sesión (para usarla dentro de funciones)
st.session_state["empresas"] = empresas

def simulador_lote(nombre_lote, presupuesto_base, pmax_precio, pmax_garantia, p_tecnico_max):
    with st.expander(f"📦 {nombre_lote} - Simulación de tu puntuación (con competidores)", expanded=False):
        st.subheader(f"Simulador de puntuación - {nombre_lote}")

        u1_precio = presupuesto_base
        u2_precio = presupuesto_base * 0.8
        u1_garantia = 3
        u2_garantia = 5

        # --- Entradas usuario ---
        st.header("✍️ Introduce tu oferta")
        c1, c2 = st.columns(2)
        with c1:
            oferta = st.number_input(
                f"💰 Tu precio ofertado (€) - {nombre_lote}",
                min_value=0.0, step=100.0, format="%.2f", key=f"precio_{nombre_lote}"
            )
        with c2:
            garantia = st.number_input(
                "📆 Años de garantía extendida",
                min_value=0.0, step=0.5, key=f"garantia_{nombre_lote}"
            )

        # --- Cálculos (permitiendo 0) ---
        p_precio = calcular_puntuacion_precio(oferta, u1_precio, u2_precio, pmax_precio) if oferta > 0 else 0
        p_garantia = calcular_puntuacion_garantia(garantia, u1_garantia, u2_garantia, pmax_garantia) if garantia > 0 else 0

        # --- Criterios técnicos ---
        st.header("📋 Evaluación técnica subjetiva")

        if nombre_lote == "Lote 1":
            criterios = {
                "Conectividad": 8,
                "Rendimiento": 8,
                "Alta disponibilidad": 4,
                "Interoperabilidad": 6,
                "Seguridad": 4,
                "Mantenibilidad": 4,
                "Escalabilidad": 3,
                "Plan de puesta en marcha": 3,
                "Plan de formación": 2,
                "Soporte técnico": 3
            }
        elif nombre_lote == "Lote 2":
            criterios = {
                "Capacidades de conectividad de los puntos de acceso": 5,
                "Funcionalidad y prestaciones de la solución NAC": 8,
                "Funcionalidad y prestaciones del portal cautivo con esponsor": 2,
                "Rendimiento de la solución WiFi": 3,
                "Rendimiento de la solución NAC": 3,
                "Alta disponibilidad de la solución": 2,
                "Interoperabilidad de la solución": 6,
                "Seguridad de la solución": 4,
                "Mantenibilidad de la solución": 3,
                "Escalabilidad de la solución": 1,
                "Plan de implantación": 3,
                "Plan de formación": 2,
                "Soporte y asistencia técnica": 3
            }
        elif nombre_lote == "Lote 3":
            criterios = {"Criterios subjetivos": 45}
        else:
            criterios = {}

        puntos_tecnicos = 0
        for crit, max_pts in criterios.items():
            puntos_tecnicos += st.slider(
                f"{crit} (0 - {max_pts})", 0, max_pts, max_pts, key=f"{nombre_lote}_{crit}"
            )

        # --- Simulación de competidores ---
        st.header("🏁 Simulación de empresas competidoras")

        empresas_globales = st.session_state.get("empresas", [])
        if not empresas_globales:
            st.warning("No hay empresas configuradas. Configúralas arriba.")
            return

        distribucion = st.selectbox(
            "Distribución de precios simulados",
            ["Uniforme", "Normal", "Triangular"],
            key=f"dist_{nombre_lote}"
        )

        bajada_max = st.slider(
            "Bajada máxima esperada respecto al PL (%)",
            1, 50, 20,
            key=f"bajada_{nombre_lote}"
        )

        min_precio_sim = presupuesto_base * (1 - bajada_max / 100)

        # Excluimos "emco" para generar precios simulados solo de competidores
        competidores = [e for e in empresas_globales if e != "emco"]
        num_comp = len(competidores)

        # Generamos precios para competidores y añadimos tu oferta
        precios_comp = simular_competidores(min_precio_sim, presupuesto_base, num_comp, distribucion)
        precios_finales = np.append(precios_comp, oferta)

        # Lista completa ordenada (competidores + emco)
        nombres_empresas = competidores + ["emco"]

        # --- Calcular puntuaciones ---
        tabla = []
        for nombre, precio in zip(nombres_empresas, precios_finales):
            p_p = calcular_puntuacion_precio(precio, u1_precio, u2_precio, pmax_precio)
            g = garantia if nombre == "emco" else np.random.uniform(u1_garantia, u2_garantia + 1)
            p_g = calcular_puntuacion_garantia(g, u1_garantia, u2_garantia, pmax_garantia)
            p_t = puntos_tecnicos if nombre == "emco" else np.random.randint(20, p_tecnico_max + 1)
            total = p_p + p_g + p_t
            tabla.append({
                "Empresa": nombre,
                "Precio (€)": round(precio, 2),
                "Garantía (años)": round(g, 2),
                "Económico": round(p_p, 2),
                "Garantía": round(p_g, 2),
                "Técnicos": round(p_t, 2),
                "Total": round(total, 2)
            })

        df = pd.DataFrame(tabla).sort_values("Total", ascending=False).reset_index(drop=True)
        df.index += 1
        st.dataframe(df, use_container_width=True)

        # Guardar resultados por lote (para comparador)
        st.session_state[f"empresas_{nombre_lote}"] = df["Empresa"].tolist()
        st.session_state[f"puntos_{nombre_lote}"] = df["Total"].tolist()

        # Tu total en el lote
        if "emco" in df["Empresa"].values:
            total_usuario = df.loc[df["Empresa"] == "emco", "Total"].values[0]
            st.success(f"🎯 Tu puntuación final en {nombre_lote}: **{total_usuario} puntos**")
            st.session_state[f"total_{nombre_lote}"] = total_usuario
        else:
            st.warning("No se encontró 'emco' en el ranking de este lote.")

# ============================================================
# SIMULADORES DE LOS 3 LOTES
# ============================================================
simulador_lote("Lote 1", 460000, 45, 10, 37)
simulador_lote("Lote 2", 150000, 45, 10, 45)
simulador_lote("Lote 3", 90000, 45, 10, 40)

# ============================================================
# COMPARADOR FINAL
# ============================================================
st.header("📊 Comparador final por empresa")

empresas_globales = st.session_state.get("empresas", ["emco", "Empresa A", "Empresa B"])
num_empresas_cmp = len(empresas_globales)

# Ajustar longitudes
def ajustar_longitud(lista, n):
    if len(lista) < n:
        return lista + [0.0] * (n - len(lista))
    elif len(lista) > n:
        return lista[:n]
    return lista

lote1_vals = ajustar_longitud(st.session_state.get("puntos_Lote 1", [0.0]*num_empresas_cmp), num_empresas_cmp)
lote2_vals = ajustar_longitud(st.session_state.get("puntos_Lote 2", [0.0]*num_empresas_cmp), num_empresas_cmp)
lote3_vals = ajustar_longitud(st.session_state.get("puntos_Lote 3", [0.0]*num_empresas_cmp), num_empresas_cmp)

cols = st.columns([4, 2, 2, 2])
cols[0].markdown("**Empresa**")
cols[1].markdown("**Lote 1**")
cols[2].markdown("**Lote 2**")
cols[3].markdown("**Lote 3**")

for i, emp in enumerate(empresas_globales):
    cols[0].markdown(emp)
    lote1_vals[i] = cols[1].number_input("", key=f"L1_{i}", value=float(lote1_vals[i]), step=1.0, format="%.2f")
    lote2_vals[i] = cols[2].number_input("", key=f"L2_{i}", value=float(lote2_vals[i]), step=1.0, format="%.2f")
    lote3_vals[i] = cols[3].number_input("", key=f"L3_{i}", value=float(lote3_vals[i]), step=1.0, format="%.2f")

df_comparador = pd.DataFrame({
    "Empresa": empresas_globales,
    "Lote 1": lote1_vals,
    "Lote 2": lote2_vals,
    "Lote 3": lote3_vals
})
st.dataframe(df_comparador, use_container_width=True)

# ============================================================
# OFERTAS INTEGRADORAS
# ============================================================
st.header("🔗 Ofertas integradoras (modelo PA5/2025)")
st.caption("Define qué empresas presentan ofertas integradoras y qué lotes incluyen. Se generarán todas las combinaciones posibles.")

ofertas_integradoras = []
for emp in empresas_globales:
    with st.expander(f"⚙️ Oferta integradora de {emp}", expanded=False):
        incluye = st.multiselect(
            f"Lotes incluidos en la oferta integradora de {emp}",
            ["L1", "L2", "L3"], default=[], key=f"int_incluye_{emp}"
        )
        if incluye:
            st.markdown("Introduce la puntuación por lote dentro de esta integradora:")
            l1_i = st.number_input("Lote 1", 0.0, 100.0, step=1.0, key=f"{emp}_int_l1") if "L1" in incluye else None
            l2_i = st.number_input("Lote 2", 0.0, 100.0, step=1.0, key=f"{emp}_int_l2") if "L2" in incluye else None
            l3_i = st.number_input("Lote 3", 0.0, 100.0, step=1.0, key=f"{emp}_int_l3") if "L3" in incluye else None
            ofertas_integradoras.append({"empresa": emp, "incluye": incluye, "L1": l1_i, "L2": l2_i, "L3": l3_i})

if ofertas_integradoras:
    st.markdown("### 🧩 Combinaciones posibles de ofertas (individuales + integradoras)")
    empresas_base = empresas_globales
    puntuaciones_ind = {emp: {"L1": lote1_vals[i], "L2": lote2_vals[i], "L3": lote3_vals[i]} for i, emp in enumerate(empresas_globales)}

    from itertools import product
    combinaciones = []

    # Combinaciones individuales
    for l1_emp, l2_emp, l3_emp in product(empresas_base, repeat=3):
        combinaciones.append({
            "nombre": f"{l1_emp} L1 + {l2_emp} L2 + {l3_emp} L3",
            "L1": puntuaciones_ind[l1_emp]["L1"],
            "L2": puntuaciones_ind[l2_emp]["L2"],
            "L3": puntuaciones_ind[l3_emp]["L3"]
        })

    # Combinaciones integradoras
    for oferta in ofertas_integradoras:
        emp_int = oferta["empresa"]
        lotes_int = set(oferta["incluye"])
        if lotes_int == {"L1", "L2"}:
            for emp3 in empresas_base:
                combinaciones.append({
                    "nombre": f"{emp_int} integradora L1+L2 + {emp3} L3",
                    "L1": oferta["L1"], "L2": oferta["L2"],
                    "L3": puntuaciones_ind[emp3]["L3"]
                })
        elif lotes_int == {"L1", "L2", "L3"}:
            combinaciones.append({
                "nombre": f"{emp_int} integradora L1+L2+L3",
                "L1": oferta["L1"], "L2": oferta["L2"], "L3": oferta["L3"]
            })

    # Calcular totales ponderados
    resultados = []
    for c in combinaciones:
        total = WEIGHTS[0]*c["L1"] + WEIGHTS[1]*c["L2"] + WEIGHTS[2]*c["L3"]
        resultados.append({
            "Combinación": c["nombre"], "L1": c["L1"], "L2": c["L2"], "L3": c["L3"],
            "Total ponderado": round(total, 2)
        })

    df_combos = pd.DataFrame(resultados).sort_values("Total ponderado", ascending=False).reset_index(drop=True)
    df_combos.index += 1
    st.dataframe(df_combos, use_container_width=True)
else:
    st.info("⚠️ No se han definido ofertas integradoras todavía.")
