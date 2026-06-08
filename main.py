from math import sin, sqrt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def convert_for_download(d, columns):
    csv = pd.DataFrame(d, columns=columns).to_csv(index=False, sep=";")
    return csv.encode("utf-8-sig")


st.title("Calcul de hauteur d'une lave boueuse en régime permanent uniforme (Coussot 1992)")

col1, col2, col3 = st.columns([3,4,3])

with col2:
    st.image("images/onf.png", width="stretch")

"""
Cet outil a été conçu pour calculer des hauteurs de corps de lave boueuse en régime permanent uniforme à partir d'une formule *rhéologique* de type **Herschel-Bulkley** (Coussot 1992) par une approche paramétrique.

**L’utilisation de cette application implique l’acceptation pleine et entière des conditions accessibles en bas de cette page.**
"""

st.header("Paramètres")

# st.header("Géométrie de la section")

with st.expander("Géométrie de la section"):

    geom = st.selectbox(
        "Géométrie de la section",
        ("Rectangulaire", "Trapézoïdale"),
        )

    L = st.number_input(
        label="Largeur en fond de section [$m$]",
        value=6.,
        min_value=0.01,
        step=0.05,
        format="%0.2f"
        )

    h_max = st.number_input(
            label="Hauteur max. [$m$]",
            value=6.,
            min_value=0.01,
            step=0.05,
            format="%0.2f"
            )

    if geom == "Rectangulaire":
        if h_max > L:
            st.warning("$h_{max} > L$", icon="⚠️")
    else:
        if h_max > 4 * L:
            st.warning("$h_{max} > 4 \\times L$", icon="⚠️")

# st.header("Paramètres fixés")

with st.expander("Paramètres fixés"):

    dh = st.number_input(
        label="Pas de discrétisation en hauteur [$m$]",
        value=0.05,
        min_value=0.01,
        format="%0.2f"
        )

    if dh > h_max:
        st.warning("$\\Delta h > h_{max}$", icon="⚠️")

    rho = st.number_input(
        label="Masse volumique [$kg/m^3$]",
        value=2200,
        min_value=1000
        )

    K_tauc = st.number_input(
            label="Rapport $\\frac{K}{\\tau_c}$",
            value=0.30,
            min_value=0.01,
            format="%0.2f"
            )

    g = st.number_input(
        label="Accélération de la pesanteur [$m/s^2$]",
        value=9.81,
        min_value=0.01,
        format="%0.2f"
        )

# st.header("Valeurs des contraintes seuil")

with st.expander("Seuils de contrainte"):

    constraints_dict = {}

    n_constraints = st.number_input(
        "Nombre de seuils de contrainte",
        value=3,
        min_value=1,
        max_value=10
    )

    for i in range(int(n_constraints)):
        value = st.number_input(
            f"Seuil de contrainte n°{i+1} [$Pa$]",
            value=1000 + (i+1) * 500,
            min_value=1000,
            max_value=6000,
            key=f"constraint_{i}"
        )
        constraints_dict[i] = value
        st.write("$\\frac{\\tau_c}{\\rho}$" + " = " + f"{round(value / rho, 2)} m²/s²")

    # st.write(constraints_dict)

# st.header("Valeurs des débits")

with st.expander("Débits"):

    discharges_dict = {}

    n_discharges = st.number_input(
        "Nombre de débits",
        value=3,
        min_value=1,
        max_value=6
    )

    for i in range(int(n_discharges)):
        value = st.number_input(
            f"Débit n°{i+1} [$m^3/s$]",
            value= (i+1) * 50,
            min_value=1,
            max_value=1000,
            key=f"discharge_{i}"
        )
        discharges_dict[i] = value

    # st.write(discharges_dict)

# st.header("Pentes")

with st.expander("Pentes"):

    slope_min, slope_max = st.slider(
        "Intervalle de pentes [%]",
        min_value=0.1,
        max_value=50.0,
        value=(5.5, 15.5),
        format="%0.1f"
    )

    slope_step = st.number_input(
        label="Pas de discrétisation en pente [%]",
        value=0.05,
        min_value=0.01,
        max_value=50.,
        format="%0.2f"
        )

st.write("")

# if st.button("Calculer !"):

# hauteurs
heights = np.arange(0., float(h_max), float(dh))
if float(h_max) not in heights:
    heights = np.append(heights, h_max)

# coefficients géométriques
if str(geom) == "Rectangulaire":
    A = 1.93 - 0.43 * np.atan((10. * heights / float(L))**20)
else:
    A = 1.93 - 0.6 * np.atan((0.4 * heights / float(L))**20)

# surfaces mouillées
if str(geom) == "Rectangulaire":
    S = float(L) * heights
else:
    S = (heights * (float(L) + heights))

# rayons hydrauliques
if str(geom) == "Rectangulaire":
    Rh = float(L) * heights / (float(L) + 2. * heights)
else:
    Rh = (heights * (float(L) + heights)) / (float(L) + 2. * sqrt(2) * heights)

# contraintes seuil
constraints = [int(tau_c) for tau_c in list(constraints_dict.values())]
constraints.sort()

# discharges
discharges = [int(q) for q in list(discharges_dict.values())]
discharges.sort()

# pentes
slopes = np.arange(float(slope_min), float(slope_max), float(slope_step))
if slope_max not in slopes:
    slopes = np.append(slopes, slope_max)

# résultats
results = np.zeros((len(slopes), 1 + len(constraints)*len(discharges)), dtype=np.float64)

# boucle principale
for i, s in enumerate(slopes):
    results[i, 0] = s
    I = np.atan(s/100.)
    for j, tau_c in enumerate(constraints):
        with np.errstate(invalid='ignore'):
            Q = S * float(K_tauc)**(-3.) * heights * ((1. / A) * (((float(rho) * float(g) * Rh * sin(I)) / tau_c) - 1.))**(10./3.)
            for k, q in enumerate(discharges):
                h = np.interp(q, Q, heights, left=np.nan, right=np.nan)
                results[i, j * len(discharges) + (k + 1)] = h

st.header("Résultats")

# courbes
styles = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot"]

fig = go.Figure()

for i, tau_c in enumerate(constraints):
    color = px.colors.qualitative.Plotly[i]
    for j, Q in enumerate(discharges):
        y = results[:, i * len(discharges) + (j + 1)]

        indices = np.where(np.isnan(y) == False)
        y = y[indices[0]]
        x = results[indices[0], 0]
        
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=f"{str(tau_c)} Pa - {str(Q)} m<sup>3</sup>/s",
                # name=f"{str(tau_c)} Pa - {str(Q)} m3/s",
                line=dict(
                    color=color,
                    dash=styles[j]
                )
            )
        )

        fig.update_layout(
            title={
                "text": f"Section {geom} - L = {L} m - K/tau_c = {K_tauc} - rho = {rho} kg/m<sup>3</sup>",
                "x": 0.5,
                "xanchor": "center"
            },
            xaxis=dict(
                title="pente [%]"
            ),
            yaxis=dict(
                title="hauteur normale du corps de lave [m]"
            ),
            legend=dict(
                orientation="v"
            )
        )

        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)

st.plotly_chart(fig)

columns = ["pente [%]"]
for tau_c in constraints:
    for q in discharges:
        columns.append(f"tau_c = {tau_c} Pa - Q = {q} m3/s")

csv = convert_for_download(results, columns)

st.download_button(label="Télécharger les résultats dans un fichier .csv",
                   data=csv,
                   file_name="herschel-bulkley.csv")


st.header("Documentation")

with st.expander("Guide d'utilisation"):
    st.markdown(
        """
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. In hendrerit augue a urna vehicula iaculis. Curabitur pharetra laoreet ultrices. Vivamus a suscipit velit. Mauris quis faucibus velit. Pellentesque aliquet, est in tincidunt suscipit, dui elit luctus velit, convallis tristique ipsum ante et ante. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque rutrum ipsum id molestie venenatis. Nulla dictum eros id sem congue, non lacinia risus rutrum. Morbi semper et mi non facilisis. Suspendisse gravida est sed justo congue, nec vulputate mauris dignissim. Morbi vel lorem id dolor tempus aliquet pellentesque vitae diam. Duis sit amet tincidunt nulla, id consequat orci. Proin id luctus magna.
        """
    )

with st.expander("Formulaire"):
    st.markdown(
        """
        #### Coefficient géométrique

        **Section Rectangulaire :**

        $\\boxed{A = 1.93 - 0.43 \\times \\arctan{\\left[\\left(\\frac{10 \\times h}{L}\\right)^{20}\\right]}}$

        **Section Trapézoïdale :**

        $\\boxed{A = 1.93 - 0.60 \\times \\arctan{\\left[\\left(\\frac{0.4 \\times h}{L}\\right)^{20}\\right]}}$

        - $A$ : coefficient géométrique ;
        - $h$ : hauteur de la section [$m$] ;
        - $L$ : largeur en fond de la section [$m$].

        #### Vitesse moyenne

        $\\boxed{U = \\left(\\frac{\\tau_c}{K}\\right)^3 \\times h \\times \\left[\\frac{1}{A} \\times \\left(\\frac{\\rho g R_H \\sin{i}}{\\tau_c} - 1\\right)\\right]^{\\frac{10}{3}}}$

        - $U$ : vitesse moyenne [$m/s$] ;
        - $\\tau_c$ : seuil de contrainte [$Pa$] ;
        - $K$ : consistance [$Pa.s^{\\frac{1}{3}}$] ;
        - $h$ : hauteur de la section [$m$] ;
        - $A$ : coefficient géométrique ;
        - $\\rho$ : masse volumique [$kg/m^3$] ;
        - $g$ : accélération de la pesanteur [$m/s^2$] ;
        - $R_H$ : rayon hydraulique [$m$] ;
        - $i$ : pente du bief [$rad$].
        """
    )

st.header("Avertissement – Clause de non-responsabilité")
st.markdown(
    """
    Cette application est fournie à titre informatif et pédagogique. Les calculs, estimations et résultats produits par ce logiciel sont basés sur des modèles, hypothèses et données qui peuvent comporter des approximations ou des simplifications.

    Malgré le soin apporté à son développement et à sa validation, aucune garantie n’est donnée quant à l’exactitude, l’exhaustivité ou l’actualité des informations et résultats fournis.

    En conséquence, les auteurs, développeurs et distributeurs de cette application ne sauraient être tenus responsables des erreurs, omissions ou des conséquences directes ou indirectes résultant de l’utilisation des informations, résultats ou recommandations fournis par ce logiciel.

    L’utilisateur demeure seul responsable de l’interprétation des résultats et de l’usage qu’il en fait. Il lui appartient notamment de vérifier la pertinence des hypothèses, des paramètres d’entrée et des résultats obtenus au regard de son contexte d’utilisation.

    Cette application ne se substitue en aucun cas à une expertise technique, scientifique ou professionnelle. Toute décision fondée sur les résultats fournis par ce logiciel relève de la seule responsabilité de l’utilisateur.

    L’utilisation de cette application implique l’acceptation pleine et entière des présentes conditions.
    """
)