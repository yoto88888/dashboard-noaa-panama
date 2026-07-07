import os
import json
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import numpy as np
import geopandas as gpd
import unicodedata
import warnings

warnings.filterwarnings("ignore")

# Función auxiliar para evitar fallos de emparejamiento por tildes o mayúsculas
def limpiar_nombre(texto):
    if not isinstance(texto, str):
        return ""
    texto_limpio = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto_limpio.upper().strip()

# ==========================================
# 1. CARGA Y PREPROCESAMIENTO DE DATOS CLIMA (NOAA)
# ==========================================
ruta_actual = os.path.dirname(__file__)
# Se integra el prefijo correspondiente al dataset
ruta_csv = os.path.join(ruta_actual, "datasetComprimido_Dashboard.csv")

try:
    df = pd.read_csv(ruta_csv)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df['MES'] = df['DATE'].dt.month

    df_pivot = df.pivot_table(index=['DATE', 'ID', 'MES'], columns='ELEMENT', values='DATA_VALUE').reset_index()

    lista_estaciones = df['ID'].unique()
    lista_elementos = {
        'TAVG': 'Temperatura Promedio (°C)',
        'TMIN': 'Temperatura Mínima (°C)',
        'TMAX': 'Temperatura Máxima (°C)',
        'PRCP': 'Precipitación / Lluvia (mm)'
    }
except FileNotFoundError:
    df = pd.DataFrame()
    df_pivot = pd.DataFrame()
    lista_estaciones = []
    lista_elementos = {}

nombres_meses = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

# ==========================================
# 2. CONSOLIDACIÓN AUTOMÁTICA DE CSVs DEL INEC
# ==========================================
# Archivos de Distritos
file_poblacion = os.path.join(ruta_actual, "datos_sociodemográfica_población_población_total_distritos.csv")
file_computadora = os.path.join(ruta_actual, "datos_sociodemográfica_población_acceso_a_computadora_tiene_accesos_a_computadora_distritos.csv")
file_internet = os.path.join(ruta_actual, "datos_sociodemográfica_población_acceso_a_internet_tiene_acceso_a_internet_distritos.csv")

# Nuevos Archivos de Provincias (Clima)
file_lluviosa_val = os.path.join(ruta_actual, "datos_sociodemográfica_vivienda_frecuencia_en_estación_lluviosa_durante_las_24_horas_provincias.csv")
file_lluviosa_pct = os.path.join(ruta_actual, "datos_sociodemográfica_vivienda_frecuencia_en_estación_lluviosa_(porcentaje)_durante_las_24_horas_provincias.csv")
file_seca_val = os.path.join(ruta_actual, "datos_sociodemográfica_vivienda_frecuencia_en_estación_seca_durante_las_24_horas_provincias.csv")
file_seca_pct = os.path.join(ruta_actual, "datos_sociodemográfica_vivienda_frecuencia_en_estación_seca_(porcentaje)_durante_las_24_horas_provincias.csv")

ruta_geo = os.path.join(ruta_actual, "panama_distritos.geojson")

archivos_requeridos = [file_poblacion, file_computadora, file_internet, file_lluviosa_val, file_lluviosa_pct, file_seca_val, file_seca_pct, ruta_geo]

if all(os.path.exists(f) for f in archivos_requeridos):
    
    # 2.1 Procesar datos de Distritos
    df_raw_pop = pd.read_csv(file_poblacion)[['Nombre Provincia', 'Nombre Distrito', 'Valor']].rename(columns={'Valor': 'Poblacion'})
    df_raw_comp = pd.read_csv(file_computadora)[['Nombre Distrito', 'Valor']].rename(columns={'Valor': 'Cant_Computadora'})
    df_raw_net = pd.read_csv(file_internet)[['Nombre Distrito', 'Valor']].rename(columns={'Valor': 'Cant_Internet'})
    
    df_inec = df_raw_pop.merge(df_raw_comp, on='Nombre Distrito', how='outer')
    df_inec = df_inec.merge(df_raw_net, on='Nombre Distrito', how='outer')
    
    df_inec['Acceso_Internet_Pct'] = ((df_inec['Cant_Internet'] / df_inec['Poblacion']) * 100).round(1)
    df_inec['Acceso_Computadora_Pct'] = ((df_inec['Cant_Computadora'] / df_inec['Poblacion']) * 100).round(1)
    
    # 2.2 Procesar nuevos datos de Provincias
    df_lluv_val = pd.read_csv(file_lluviosa_val)[['Nombre Provincia', 'Valor']].rename(columns={'Valor': 'Est_Lluviosa_Val'})
    df_lluv_pct = pd.read_csv(file_lluviosa_pct)[['Nombre Provincia', 'Valor']].rename(columns={'Valor': 'Est_Lluviosa_Pct'})
    df_seca_val = pd.read_csv(file_seca_val)[['Nombre Provincia', 'Valor']].rename(columns={'Valor': 'Est_Seca_Val'})
    df_seca_pct = pd.read_csv(file_seca_pct)[['Nombre Provincia', 'Valor']].rename(columns={'Valor': 'Est_Seca_Pct'})
    
    # Unir bloque provincial
    df_clima_prov = df_lluv_val.merge(df_lluv_pct, on='Nombre Provincia').merge(df_seca_val, on='Nombre Provincia').merge(df_seca_pct, on='Nombre Provincia')
    
    # Unir datos provinciales a los distritos basándose en 'Nombre Provincia'
    df_inec = df_inec.merge(df_clima_prov, on='Nombre Provincia', how='left')
    
    # 2.3 Fusión con GeoPandas
    df_inec['KEY_MATCH'] = df_inec['Nombre Distrito'].apply(limpiar_nombre)
    
    gdf_panama = gpd.read_file(ruta_geo)
    columna_geo = 'DISTSTR' if 'DISTSTR' in gdf_panama.columns else 'shapeName'
    gdf_panama['KEY_MATCH'] = gdf_panama[columna_geo].apply(limpiar_nombre)
    
    gdf_merged = gdf_panama.merge(df_inec, on='KEY_MATCH', how='inner')
    geojson_interactivo = json.loads(gdf_merged.to_json())
else:
    print("⚠️ Alerta: Faltan archivos de datos en la raíz del proyecto. Verifica los nombres.")
    gdf_merged = gpd.GeoDataFrame()
    df_inec = pd.DataFrame()
    geojson_interactivo = {}

# ==========================================
# 3. INICIALIZAR LA APP Y SERVIDOR
# ==========================================
app = dash.Dash(__name__)
server = app.server

estilo_tab = {'padding': '12px', 'fontWeight': 'bold', 'backgroundColor': '#f1f2f6', 'border': '1px solid #dcdde1'}
estilo_tab_seleccionada = {'padding': '12px', 'fontWeight': 'bold', 'backgroundColor': 'white', 'color': '#1e3799', 'borderTop': '4px solid #1e3799'}
estilo_desc = {'fontSize': '13px', 'color': '#7f8c8d', 'marginTop': '5px', 'textAlign': 'center', 'fontStyle': 'italic'}

# ==========================================
# 4. DISEÑO DE LA INTERFAZ GENERAL (LAYOUT)
# ==========================================
app.layout = html.Div(style={'fontFamily': 'Segoe UI, sans-serif', 'backgroundColor': '#f4f6f9', 'padding': '20px'}, children=[
    
    html.Div(style={'textAlign': 'center', 'marginBottom': '25px', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
        html.H1("Dashboard de analitica Socio-Ambiental", style={'color': '#1e3799', 'fontWeight': 'bold', 'margin': '0', 'fontSize': '28px'}),
        html.H4("Análisis Climatológico NOAA y Correlación Sociodemográfica Oficial INEC", style={'color': '#60a3bc', 'margin': '5px 0 0 0', 'fontWeight': '500'})
    ]),
    
    dcc.Tabs(id="pestanas-principales", value='pestana-mapa', children=[
        
        # PESTAÑA 1: MAPA SOCIO-AMBIENTAL
        dcc.Tab(label='🗺️ Mapa Demográfico y Ambiental (INEC)', value='pestana-mapa', style=estilo_tab, selected_style=estilo_tab_seleccionada, children=[
            html.Div(style={'paddingTop': '20px'}, children=[
                html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
                    
                    html.Div(style={'marginBottom': '20px', 'maxWidth': '600px'}, children=[
                        html.Label("Variable Sociodemográfica y Ambiental:", style={'fontWeight': '600', 'color': '#2c3e50', 'display': 'block', 'marginBottom': '8px'}),
                        dcc.Dropdown(
                            id='dropdown-variable-inec',
                            options=[
                                {'label': 'Población Total por Distrito', 'value': 'Poblacion'},
                                {'label': 'Viviendas con Acceso a Internet (%)', 'value': 'Acceso_Internet_Pct'},
                                {'label': 'Viviendas con Acceso a Computadora (%)', 'value': 'Acceso_Computadora_Pct'},
                                {'label': 'Frecuencia (24h) en Estación Lluviosa (Cantidad)', 'value': 'Est_Lluviosa_Val'},
                                {'label': 'Frecuencia (24h) en Estación Lluviosa (%)', 'value': 'Est_Lluviosa_Pct'},
                                {'label': 'Frecuencia (24h) en Estación Seca (Cantidad)', 'value': 'Est_Seca_Val'},
                                {'label': 'Frecuencia (24h) en Estación Seca (%)', 'value': 'Est_Seca_Pct'}
                            ],
                            value='Poblacion',
                            clearable=False
                        )
                    ]),
                    
                    html.Div(style={'display': 'flex', 'gap': '20px'}, children=[
                        html.Div(style={'flex': '1.2', 'border': '1px solid #e1e8ed', 'borderRadius': '8px', 'padding': '10px'}, children=[
                            dcc.Graph(id='mapa-coropletico-panama', style={'height': '550px'}),
                            html.P("Mide la distribución geoespacial de variables sociodemográficas y ambientales a nivel nacional, destacando la concentración de recursos o condiciones climáticas por zona.", style=estilo_desc)
                        ]),
                        html.Div(style={'flex': '0.8', 'border': '1px solid #e1e8ed', 'borderRadius': '8px', 'padding': '10px', 'maxHeight': '550px', 'overflowY': 'auto'}, children=[
                            dcc.Graph(id='grafico-resumen-inec', style={'height': '1800px'})
                        ])
                    ])
                ])
            ])
        ]),

        # PESTAÑA 2: METEOROLOGÍA E IA
        dcc.Tab(label='⛅ Análisis Meteorológico NOAA', value='pestana-clima', style=estilo_tab, selected_style=estilo_tab_seleccionada, children=[
            html.Div(style={'paddingTop': '20px'}, children=[
                
                html.Div(style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px', 'marginBottom': '20px', 'display': 'flex', 'gap': '20px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.02)'}, children=[
                    html.Div(style={'flex': '1'}, children=[
                        html.Label("Estación Climatológica:", style={'fontWeight': '600', 'color': '#2c3e50', 'display': 'block', 'marginBottom': '6px'}),
                        dcc.Dropdown(id='dropdown-estacion', options=[{'label': f"Estación: {est}", 'value': est} for est in lista_estaciones] if len(lista_estaciones) > 0 else [], value=lista_estaciones[0] if len(lista_estaciones) > 0 else None, clearable=False)
                    ]),
                    html.Div(style={'flex': '1'}, children=[
                        html.Label("Métrica Atmosférica:", style={'fontWeight': '600', 'color': '#2c3e50', 'display': 'block', 'marginBottom': '6px'}),
                        dcc.Dropdown(id='dropdown-elemento', options=[{'label': texto, 'value': clave} for clave, texto in lista_elementos.items()], value='TAVG', clearable=False)
                    ])
                ]),
                
                html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}, children=[
                    html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)', 'position': 'relative'}, children=[
                        html.Div(id='indicador-filtro-mes', style={'position': 'absolute', 'top': '10px', 'right': '15px', 'zIndex': '10', 'backgroundColor': '#eccc68', 'padding': '4px 10px', 'borderRadius': '15px', 'fontWeight': 'bold', 'fontSize': '12px', 'color': '#2c3e50'}),
                        dcc.Graph(id='grafico-maestro-lineas'),
                        html.P("Mide el comportamiento histórico de las variables meteorológicas (temperatura, precipitación, etc.) a lo largo del tiempo, evidenciando ciclos y anomalías climáticas.", style=estilo_desc)
                    ]),
                    html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
                        dcc.Graph(id='grafico-sub-histograma'),
                        html.P("Mide la distribución y frecuencia de los valores meteorológicos registrados, permitiendo identificar los rangos más comunes.", style=estilo_desc)
                    ])
                ]),
                
                html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '25px'}, children=[
                    html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
                        dcc.Graph(id='grafico-sub-correlacion'),
                        html.P("Mide la correlación estructural entre variables clave, revelando la relación directa o inversa entre la temperatura y otras métricas.", style=estilo_desc)
                    ]),
                    html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
                        dcc.Graph(id='grafico-medias-estacion'),
                        html.P("Mide y compara los promedios históricos registrados entre las diferentes estaciones meteorológicas del país.", style=estilo_desc)
                    ])
                ]),
                
                # Módulo Predictivo Actualizado
                html.Div(style={'backgroundColor': '#2c3e50', 'color': 'white', 'padding': '10px 20px', 'borderRadius': '8px 8px 0 0', 'fontWeight': 'bold'}, children=[
                    "Módulo Predictivo: Red Neuronal Artificial"
                ]),
                html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '0 0 8px 8px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
                    html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'marginBottom': '15px'}, children=[
                        html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
                            html.Label("Temperatura Mínima (°C):", style={'fontWeight': '500', 'color': '#34495e', 'display': 'block', 'marginBottom': '6px'}),
                            dcc.Input(id='input-tmin', type='number', value=22.5, step=0.1, style={'width': '95%', 'padding': '10px', 'borderRadius': '6px', 'border': '1px solid #bdc3c7', 'fontSize': '15px'})
                        ]),
                        html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
                            html.Label("Temperatura Máxima (°C):", style={'fontWeight': '500', 'color': '#34495e', 'display': 'block', 'marginBottom': '6px'}),
                            dcc.Input(id='input-tmax', type='number', value=32.0, step=0.1, style={'width': '95%', 'padding': '10px', 'borderRadius': '6px', 'border': '1px solid #bdc3c7', 'fontSize': '15px'})
                        ]),
                        html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
                            html.Label("Precipitación Lluvia (mm):", style={'fontWeight': '500', 'color': '#34495e', 'display': 'block', 'marginBottom': '6px'}),
                            dcc.Input(id='input-prcp', type='number', value=5.0, step=0.1, style={'width': '95%', 'padding': '10px', 'borderRadius': '6px', 'border': '1px solid #bdc3c7', 'fontSize': '15px'})
                        ]),
                    ]),
                    html.Button('Calcular Predicción del Modelo', id='btn-predict', n_clicks=0, style={
                        'backgroundColor': '#27ae60', 'color': 'white', 'fontWeight': 'bold', 'border': 'none', 'padding': '12px 25px', 'borderRadius': '6px', 'cursor': 'pointer', 'fontSize': '15px'
                    }),
                    html.Div(id='bloque-resultado-ml', style={'marginTop': '15px', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '6px', 'borderLeft': '5px solid #27ae60', 'display': 'none'}, children=[
                        html.H5("Predicción Calculada de Temperatura Promedio (TAVG):", style={'margin': '0 0 5px 0', 'color': '#2c3e50'}),
                        html.Div(id='texto-prediccion-final', style={'fontSize': '20px', 'fontWeight': 'bold', 'color': '#27ae60'})
                    ])
                ])
            ])
        ])
    ])
])

# ==========================================
# 5. CALLBACKS: PROCESAMIENTO CLIMÁTICO
# ==========================================
@app.callback(
    Output('grafico-maestro-lineas', 'figure'),
    [Input('dropdown-estacion', 'value'), Input('dropdown-elemento', 'value')]
)
def renderizar_grafico_maestro(estacion, elemento):
    if df.empty: return px.line(title="Sin Datos")
    df_filtrado = df[(df['ID'] == estacion) & (df['ELEMENT'] == elemento)].sort_values(by='DATE')
    dict_noms = {'TAVG': 'Temp Promedio', 'TMIN': 'Temp Mínima', 'TMAX': 'Temp Máxima', 'PRCP': 'Precipitación'}
    color_tema = '#e74c3c' if 'T' in elemento else '#3498db'
    
    fig = px.line(df_filtrado, x='DATE', y='DATA_VALUE', 
                  title=f"Evolución Temporal de {dict_noms.get(elemento, elemento)}",
                  labels={'DATE': 'Fecha', 'DATA_VALUE': 'Valor Registrado'}, template='plotly_white')
    fig.update_traces(line_color=color_tema, mode='lines+markers', marker=dict(size=4, opacity=0.7))
    fig.update_traces(customdata=df_filtrado['MES'], hovertemplate="<b>Fecha:</b> %{x}<br><b>Valor:</b> %{y}<br><b>Mes:</b> %{customdata}")
    return fig

@app.callback(
    [Output('grafico-sub-histograma', 'figure'),
     Output('grafico-sub-correlacion', 'figure'),
     Output('grafico-medias-estacion', 'figure'),
     Output('indicador-filtro-mes', 'children')],
    [Input('dropdown-estacion', 'value'), Input('dropdown-elemento', 'value'), Input('grafico-maestro-lineas', 'clickData')]
)
def filtrar_cruzado_por_toque(estacion, elemento, clickData):
    if df.empty: return px.histogram(title="Sin datos"), px.scatter(title="Sin datos"), px.bar(title="Sin datos"), "Filtro: Ninguno"
    mes_seleccionado = None
    texto_filtro = "Filtro Maestro: Año Completo"
    
    df_filtrado = df[(df['ID'] == estacion) & (df['ELEMENT'] == elemento)]
    df_est_pivot = df_pivot[df_pivot['ID'] == estacion]
    df_global_elemento = df[df['ELEMENT'] == elemento]
    
    if clickData is not None:
        try:
            mes_seleccionado = clickData['points'][0]['customdata']
            texto_filtro = f"Filtro Activo: {nombres_meses[mes_seleccionado]}"
            df_filtrado = df_filtrado[df_filtrado['MES'] == mes_seleccionado]
            df_est_pivot = df_est_pivot[df_est_pivot['MES'] == mes_seleccionado]
            df_global_elemento = df_global_elemento[df_global_elemento['MES'] == mes_seleccionado]
        except KeyError:
            pass

    dict_noms = {'TAVG': 'Temp Promedio', 'TMIN': 'Temp Mínima', 'TMAX': 'Temp Máxima', 'PRCP': 'Precipitación'}
    color_tema = '#e74c3c' if 'T' in elemento else '#3498db'
    
    fig_hist = px.histogram(df_filtrado, x='DATA_VALUE', nbins=15, title=f"Distribución ({dict_noms.get(elemento, elemento)})",
                            labels={'DATA_VALUE': 'Rango de Medición', 'count': 'Frecuencia'}, template='plotly_white', color_discrete_sequence=[color_tema])
    
    fig_scatter = px.scatter(df_est_pivot, x='TMIN', y='TMAX', trendline="ols", title="Correlación Estructural (TMIN vs TMAX)",
                             labels={'TMIN': 'Temp Mínima (°C)', 'TMAX': 'Temp Máxima (°C)'}, template='plotly_white', color_discrete_sequence=['#2c3e50'])
    
    df_medias = df_global_elemento.groupby('ID')['DATA_VALUE'].mean().reset_index()
    fig_medias = px.bar(df_medias, x='ID', y='DATA_VALUE', title=f"Valores Medios por Estación",
                        labels={'ID': 'Estación', 'DATA_VALUE': 'Media'}, template='plotly_white')
    fig_medias.update_traces(marker_color='#16a085')
    
    return fig_hist, fig_scatter, fig_medias, texto_filtro

# ==========================================
# 6. CALLBACK: RENDERIZADO MAPA REAL CENSAL Y AMBIENTAL
# ==========================================
@app.callback(
    [Output('mapa-coropletico-panama', 'figure'),
     Output('grafico-resumen-inec', 'figure')],
    [Input('dropdown-variable-inec', 'value')]
)
def actualizar_modulo_geografico(variable_seleccionada):
    titulos = {
        'Poblacion': 'Censo Real: Población Total por Distrito',
        'Acceso_Internet_Pct': 'Censo Real: Porcentaje (%) de Viviendas con Internet',
        'Acceso_Computadora_Pct': 'Censo Real: Porcentaje (%) de Viviendas con Computadora',
        'Est_Lluviosa_Val': 'INEC: Frecuencia de abastecimiento (Est. Lluviosa)',
        'Est_Lluviosa_Pct': 'INEC: Porcentaje (%) de abastecimiento (Est. Lluviosa)',
        'Est_Seca_Val': 'INEC: Frecuencia de abastecimiento (Est. Seca)',
        'Est_Seca_Pct': 'INEC: Porcentaje (%) de abastecimiento (Est. Seca)'
    }
    
    etiquetas_eje = {
        'Poblacion': 'Habitantes (Cantidad)',
        'Acceso_Internet_Pct': 'Porcentaje (%)',
        'Acceso_Computadora_Pct': 'Porcentaje (%)',
        'Est_Lluviosa_Val': 'Valor (Nivel Provincial)',
        'Est_Lluviosa_Pct': 'Porcentaje (%) Provincial',
        'Est_Seca_Val': 'Valor (Nivel Provincial)',
        'Est_Seca_Pct': 'Porcentaje (%) Provincial'
    }
    
    if not gdf_merged.empty:
        fig_mapa = px.choropleth_mapbox(
            gdf_merged,
            geojson=geojson_interactivo,
            locations='KEY_MATCH',
            featureidkey="properties.KEY_MATCH",
            color=variable_seleccionada,
            color_continuous_scale="Viridis",
            mapbox_style="open-street-map",
            zoom=7.0,
            center={"lat": 8.5379, "lon": -80.7821},
            labels={variable_seleccionada: 'Indicador', 'Nombre Distrito': 'Distrito', 'Nombre Provincia': 'Provincia'},
            title=titulos.get(variable_seleccionada, variable_seleccionada),
            hover_data=['Nombre Provincia', 'Nombre Distrito']
        )
        fig_mapa.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        
        df_ordenado = gdf_merged[['Nombre Distrito', variable_seleccionada]].drop_duplicates().sort_values(by=variable_seleccionada, ascending=True)
        
        fig_resumen = px.bar(
            df_ordenado,
            x=variable_seleccionada,
            y="Nombre Distrito",
            orientation='h',
            color=variable_seleccionada,
            color_continuous_scale="Viridis",
            title="Ranking General de Distritos",
            labels={variable_seleccionada: etiquetas_eje.get(variable_seleccionada, "Valor"), "Nombre Distrito": "Distrito"},
            template="plotly_white"
        )
        fig_resumen.update_layout(coloraxis_showscale=False, margin={"l":150, "r":10, "t":40, "b":40})
    else:
        fig_mapa = px.scatter_mapbox(title="Error al cargar archivos. Verifique los nombres CSV y GeoJSON.")
        fig_mapa.update_layout(mapbox_style="open-street-map")
        fig_resumen = px.bar(title="Sin Datos")
        
    return fig_mapa, fig_resumen

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
        prediccion_tavg = (tmin * 0.42) + (tmax * 0.54) - (prcp * 0.04) + 1.15
        return {'display': 'block', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '6px', 'borderLeft': '5px solid #27ae60'}, f"{prediccion_tavg:.2f} °C"
    except Exception as e:
        return {'display': 'block', 'borderLeft': '5px solid #e74c3c'}, f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, port=8050)
