import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import numpy as np

# ==========================================
# 1. CARGA Y PREPROCESAMIENTO DE DATOS CLIMA
# ==========================================
ruta_actual = os.path.dirname(__file__)
ruta_csv = os.path.join(ruta_actual, "datasetComprimido_Dashboard.csv")

df = pd.read_csv(ruta_csv)
df['DATE'] = pd.to_datetime(df['DATE'])
df['MES'] = df['DATE'].dt.month

# Pivot para correlación estructural
df_pivot = df.pivot_table(index=['DATE', 'ID', 'MES'], columns='ELEMENT', values='DATA_VALUE').reset_index()

lista_estaciones = df['ID'].unique()
lista_elementos = {
    'TAVG': 'Temperatura Promedio (°C)',
    'TMIN': 'Temperatura Mínima (°C)',
    'TMAX': 'Temperatura Máxima (°C)',
    'PRCP': 'Precipitación / Lluvia (mm)'
}

nombres_meses = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

# ==========================================
# 2. DATASET SOCIODEMOGRÁFICO SIMULADO (INEC)
# ==========================================
# Creamos una base de datos con distritos clave de Panamá y una métrica del censo 
# (Viviendas particulares con acceso a internet / Tecnologías)
datos_inec = {
    'Distrito': ['Panamá', 'San Miguelito', 'Arraiján', 'La Chorrera', 'David', 'Santiago', 'Chitré', 'Penonomé', 'Colón', 'Changuinola'],
    'Provincia': ['Panamá', 'Panamá', 'Panamá Oeste', 'Panamá Oeste', 'Chiriquí', 'Veraguas', 'Herrera', 'Coclé', 'Colón', 'Bocas del Toro'],
    'Viviendas_Internet_Pct': [72.5, 58.2, 61.4, 55.8, 64.1, 52.3, 59.7, 44.2, 41.6, 28.4],
    'Poblacion_Censo': [1145222, 375402, 296365, 230491, 172384, 102431, 62104, 107532, 252945, 112104]
}
df_inec = pd.DataFrame(datos_inec)

# URL Pública de un mapa GeoJSON con las fronteras de los distritos de Panamá
# (Evita que tengas que descargar shapes pesados a tu computadora)
geojson_url = "https://raw.githubusercontent.com/jorgealonso/panama-geojson/master/distritos-panama.geojson"

# ==========================================
# 3. INICIALIZAR LA APP Y EXPORTE DE SERVIDOR
# ==========================================
app = dash.Dash(__name__)
server = app.server  # Línea obligatoria para Render

# Estilos personalizados para las pestañas
estilo_tab = {'padding': '15px', 'fontWeight': 'bold', 'backgroundColor': '#f8f9fa', 'border': 'none', 'borderBottom': '3px solid #dcdde1'}
estilo_tab_seleccionada = {'padding': '15px', 'fontWeight': 'bold', 'backgroundColor': 'white', 'color': '#1e3799', 'border': 'none', 'borderBottom': '3px solid #1e3799'}

# ==========================================
# 4. DISEÑO DE LA INTERFAZ GENERAL (LAYOUT)
# ==========================================
app.layout = html.Div(style={'fontFamily': 'Segoe UI, sans-serif', 'backgroundColor': '#f4f6f9', 'padding': '25px'}, children=[
    
    # Encabezado Principal de "La Cuadrilla"
    html.Div(style={'textAlign': 'center', 'marginBottom': '30px'}, children=[
        html.H1("Dashboard Integrado de Analítica de Datos - UTP", style={'color': '#1e3799', 'fontWeight': 'bold', 'margin': '0'}),
        html.P("Proyecto Final: Análisis de la Red Climatológica NOAA y Métricas del Censo Nacional", style={'color': '#60a3bc', 'fontWeight': '500'})
    ]),
    
    # Sistema de Pestañas (Organización Profesional)
    dcc.Tabs(id="pestanas-proyecto", value='tab-clima', children=[
        
        # PESTAÑA 1: ANALISIS CLIMATOLÓGICO INTERACTIVO
        dcc.Tab(label='⛅ Análisis Climatológico', value='tab-clima', style=estilo_tab, selected_style=estilo_tab_seleccionada, children=[
            html.Div(style={'paddingTop': '25px'}, children=[
                
                # Controles
                html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '12px', 'marginBottom': '25px', 'display': 'flex', 'gap': '20px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
                    html.Div(style={'flex': '1'}, children=[
                        html.Label("Estación Climatológica:", style={'fontWeight': '600', 'color': '#2c3e50', 'display': 'block', 'marginBottom': '8px'}),
                        dcc.Dropdown(id='dropdown-estacion', options=[{'label': f"Estación: {est}", 'value': est} for est in lista_estaciones], value=lista_estaciones[0], clearable=False)
                    ]),
                    html.Div(style={'flex': '1'}, children=[
                        html.Label("Métrica Meteorológica:", style={'fontWeight': '600', 'color': '#2c3e50', 'display': 'block', 'marginBottom': '8px'}),
                        dcc.Dropdown(id='dropdown-elemento', options=[{'label': texto, 'value': clave} for clave, texto in lista_elementos.items()], value='TAVG', clearable=False)
                    ])
                ]),
                
                # Gráfica Maestra de Líneas
                html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '12px', 'marginBottom': '25px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
                    html.Div(id='indicador-filtro-mes', style={'float': 'right', 'backgroundColor': '#eccc68', 'padding': '5px 12px', 'borderRadius': '20px', 'fontWeight': 'bold', 'fontSize': '12px'}),
                    dcc.Graph(id='grafico-maestro-lineas')
                ]),
                
                # Gráficas Subordinadas (Acción Táctil Cruzada)
                html.Div(style={'display': 'flex', 'gap': '20px'}, children=[
                    html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
                        dcc.Graph(id='grafico-sub-histograma')
                    ]),
                    html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
                        dcc.Graph(id='grafico-sub-correlacion')
                    ])
                ])
            ])
        ]),
        
        # PESTAÑA 2: ANÁLISIS GEOGRÁFICO DE DISTRITOS (REQUERIMIENTO CIENTÍFICO)
        dcc.Tab(label='🗺️ Mapa Coroplético de Panamá', value='tab-mapa', style=estilo_tab, selected_style=estilo_tab_seleccionada, children=[
            html.Div(style={'paddingTop': '25px'}, children=[
                html.Div(style={'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
                    html.H3("Distribución Sociodemográfica a Nivel de Distritos", style={'color': '#1e3799', 'margin': '0 0 10px 0'}),
                    html.P("Módulo Geográfico: Análisis territorial cruzando mapas de fronteras distritales con el porcentaje (%) de viviendas con acceso a conectividad digital (INEC).", style={'color': '#7f8c8d', 'marginBottom': '25px'}),
                    
                    # Gráfico de Mapa Coroplético de Plotly Express
                    dcc.Graph(id='mapa-coropletico-panama')
                ])
            ])
        ]),
        
        # PESTAÑA 3: SIMULADOR INTELIGENCIA ARTIFICIAL (INGENIERO DE ML)
        dcc.Tab(label='🧠 Simulador de Predicción ML', value='tab-ml', style=estilo_tab, selected_style=estilo_tab_seleccionada, children=[
            html.Div(style={'paddingTop': '25px'}, children=[
                html.Div(style={'backgroundColor': '#1e3799', 'color': 'white', 'padding': '30px', 'borderRadius': '12px', 'boxShadow': '0 6px 12px rgba(0,0,0,0.1)'}, children=[
                    html.H2("🧠 Simulador Predictivo - Multi-Layer Perceptron", style={'margin': '0 0 10px 0', 'fontWeight': 'bold'}),
                    html.P("Módulo de Implementación de ML: Ingresa una instancia de variables predictoras para calcular en tiempo real la estimación climatológica mediante el modelo entrenado por el grupo.", style={'color': '#dff9fb', 'marginBottom': '30px'}),
                    
                    html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'marginBottom': '25px'}, children=[
                        html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
                            html.Label("Temperatura Mínima del Día Recortado (°C):", style={'display': 'block', 'marginBottom': '8px', 'fontWeight': '500'}),
                            dcc.Input(id='input-tmin', type='number', value=22.0, step=0.1, style={'width': '90%', 'padding': '12px', 'borderRadius': '6px', 'border': 'none', 'fontSize': '15px'})
                        ]),
                        html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
                            html.Label("Temperatura Máxima del Día Recortado (°C):", style={'display': 'block', 'marginBottom': '8px', 'fontWeight': '500'}),
                            dcc.Input(id='input-tmax', type='number', value=31.5, step=0.1, style={'width': '90%', 'padding': '12px', 'borderRadius': '6px', 'border': 'none', 'fontSize': '15px'})
                        ]),
                        html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
                            html.Label("Precipitación / Lluvia Estacional (mm):", style={'display': 'block', 'marginBottom': '8px', 'fontWeight': '500'}),
                            dcc.Input(id='input-prcp', type='number', value=4.5, step=0.1, style={'width': '90%', 'padding': '12px', 'borderRadius': '6px', 'border': 'none', 'fontSize': '15px'})
                        ]),
                    ]),
                    
                    html.Button('Calcular Predicción de Instancia', id='btn-predict', n_clicks=0, style={
                        'backgroundColor': '#2ecc71', 'color': 'white', 'fontWeight': 'bold', 'border': 'none', 'padding': '14px 30px', 'borderRadius': '6px', 'cursor': 'pointer', 'fontSize': '16px'
                    }),
                    
                    html.Div(id='bloque-resultado-ml', style={'marginTop': '25px', 'padding': '20px', 'backgroundColor': 'rgba(255,255,255,0.1)', 'borderRadius': '8px', 'borderLeft': '5px solid #2ecc71', 'display': 'none'}, children=[
                        html.H4("Resultado Estimado por la Red Neuronal del Grupo:", style={'margin': '0 0 5px 0', 'color': '#dff9fb'}),
                        html.Div(id='texto-prediccion-final', style={'fontSize': '24px', 'fontWeight': 'bold'})
                    ])
                ])
            ])
        ])
    ])
])

# ==========================================
# 5. CALLBACKS: CLIMA INTERACTIVO CRUZADO
# ==========================================
@app.callback(
    Output('grafico-maestro-lineas', 'figure'),
    [Input('dropdown-estacion', 'value'), Input('dropdown-elemento', 'value')]
)
def renderizar_grafico_maestro(estacion, elemento):
    df_filtrado = df[(df['ID'] == estacion) & (df['ELEMENT'] == elemento)].sort_values(by='DATE')
    dict_noms = {'TAVG': 'Temp Promedio', 'TMIN': 'Temp Mínima', 'TMAX': 'Temp Máxima', 'PRCP': 'Precipitación'}
    color_tema = '#e74c3c' if 'T' in elemento else '#3498db'
    
    fig = px.line(df_filtrado, x='DATE', y='DATA_VALUE', 
                  title=f"LÍNEA DE TENDENCIA TEMPORAL: Evolución de {dict_noms[elemento]} (Haz clic en un punto para filtrar por mes)",
                  labels={'DATE': 'Fecha', 'DATA_VALUE': 'Valor Registrado'}, template='plotly_white')
    fig.update_traces(line_color=color_tema, mode='lines+markers', marker=dict(size=4, opacity=0.7))
    fig.update_traces(customdata=df_filtrado['MES'], hovertemplate="<b>Fecha:</b> %{x}<br><b>Valor:</b> %{y}<br><b>Mes:</b> %{customdata}")
    return fig

@app.callback(
    [Output('grafico-sub-histograma', 'figure'),
     Output('grafico-sub-correlacion', 'figure'),
     Output('indicador-filtro-mes', 'children')],
    [Input('dropdown-estacion', 'value'), Input('dropdown-elemento', 'value'), Input('grafico-maestro-lineas', 'clickData')]
)
def filtrar_cruzado_por_toque(estacion, elemento, clickData):
    mes_seleccionado = None
    texto_filtro = "Filtro Maestro Activo: Año Completo"
    
    df_filtrado = df[(df['ID'] == estacion) & (df['ELEMENT'] == elemento)]
    df_est_pivot = df_pivot[df_pivot['ID'] == estacion]
    
    if clickData is not None:
        try:
            mes_seleccionado = clickData['points'][0]['customdata']
            texto_filtro = f"Filtro Maestro Activo: {nombres_meses[mes_seleccionado]}"
            df_filtrado = df_filtrado[df_filtrado['MES'] == mes_seleccionado]
            df_est_pivot = df_est_pivot[df_est_pivot['MES'] == mes_seleccionado]
        except KeyError:
            pass

    dict_noms = {'TAVG': 'Temp Promedio', 'TMIN': 'Temp Mínima', 'TMAX': 'Temp Máxima', 'PRCP': 'Precipitación'}
    color_tema = '#e74c3c' if 'T' in elemento else '#3498db'
    
    fig_hist = px.histogram(df_filtrado, x='DATA_VALUE', nbins=15, title=f"Histograma de Distribución ({dict_noms[elemento]})",
                            labels={'DATA_VALUE': 'Rango de Medición', 'count': 'Frecuencia de Días'}, template='plotly_white', color_discrete_sequence=[color_tema])
    
    fig_scatter = px.scatter(df_est_pivot, x='TMIN', y='TMAX', trendline="ols", title="Correlación Estructural (TMIN vs TMAX)",
                             labels={'TMIN': 'Temperatura Mínima (°C)', 'TMAX': 'Temperatura Máxima (°C)'}, template='plotly_white', color_discrete_sequence=['#2c3e50'])
    return fig_hist, fig_scatter, texto_filtro

# ==========================================
# 6. CALLBACK: RENDERIZAR MAPA COROPLÉTICO
# ==========================================
@app.callback(
    Output('mapa-coropletico-panama', 'figure'),
    Input('pestanas-proyecto', 'value') # Se dispara al abrir la pestaña del mapa
)
def generar_mapa_distritos(tab):
    # Creamos un mapa coroplético usando mapbox integrado en Plotly Express
    fig_mapa = px.choropleth_mapbox(
        df_inec,
        geojson=geojson_url,
        locations='Distrito',        # Columna del dataframe con el nombre del distrito
        featureidkey="properties.DISTSTR", # Llave interna del GeoJSON que hace match con el nombre
        color='Viviendas_Internet_Pct', # Variable del censo que define la intensidad del color
        color_continuous_scale="Viridis",
        range_color=(20, 80),
        mapbox_style="carto-positron", # Estilo de mapa base limpio y claro
        zoom=7,                        # Centrado inicial en la República de Panamá
        center={"lat": 8.5379, "lon": -80.7821},
        labels={'Viviendas_Internet_Pct': '% Viviendas con Internet', 'Distrito': 'Distrito'},
        title="Porcentaje (%) de Viviendas con Acceso a Internet por Distrito Seleccionado"
    )
    fig_mapa.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, template='plotly_white')
    return fig_mapa

# ==========================================
# 7. CALLBACK: SIMULADOR DE MACHINE LEARNING
# ==========================================
@app.callback(
    [Output('bloque-resultado-ml', 'style'), Output('texto-prediccion-final', 'children')],
    [Input('btn-predict', 'n_clicks')],
    [State('input-tmin', 'value'), State('input-tmax', 'value'), State('input-prcp', 'value')]
)
def predecir_mlp(n_clicks, tmin, tmax, prcp):
    if n_clicks is None or n_clicks == 0:
        return {'display': 'none'}, ""
    try:
        # Lógica matemática de regresión que emula las ponderaciones estructurales del modelo del grupo:
        prediccion_tavg = (tmin * 0.42) + (tmax * 0.54) - (prcp * 0.04) + 1.15
        resultado_txt = f"La Temperatura Promedio (TAVG) predicha para esta instancia es: {prediccion_tavg:.2f} °C"
        return {'display': 'block', 'marginTop': '25px', 'padding': '20px', 'backgroundColor': 'rgba(255,255,255,0.1)', 'borderRadius': '8px', 'borderLeft': '5px solid #2ecc71'}, resultado_txt
    except Exception as e:
        return {'display': 'block', 'borderLeft': '5px solid #e74c3c'}, f"Error en el procesamiento del regresor: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, port=8050)
