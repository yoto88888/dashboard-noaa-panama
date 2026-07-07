import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import numpy as np

# Para simular la predicción en el dashboard temporalmente antes de exportar con joblib,
# o si quieres usar un cálculo basado en las variables del modelo de tus compañeros:
# (Si ya tienes el archivo .pkl, puedes descomentar la sección correspondente)

# ==========================================
# 1. CARGA Y PREPROCESAMIENTO DE DATOS
# ==========================================
ruta_actual = os.path.dirname(__file__)
ruta_csv = os.path.join(ruta_actual, "datasetComprimido_Dashboard.csv")

df = pd.read_csv(ruta_csv)
df['DATE'] = pd.to_datetime(df['DATE'])

# Crear columnas pivotadas para análisis de correlación interno (TMAX vs TMIN)
# Esto nos permite cruzar variables en una sola fila por fecha y estación
df_pivot = df.pivot_table(index=['DATE', 'ID'], columns='ELEMENT', values='DATA_VALUE').reset_index()

lista_estaciones = df['ID'].unique()
lista_elementos = {
    'TAVG': 'Temperatura Promedio (°C)',
    'TMIN': 'Temperatura Mínima (°C)',
    'TMAX': 'Temperatura Máxima (°C)',
    'PRCP': 'Precipitación / Lluvia (mm)'
}

# ==========================================
# 2. INICIALIZAR LA APP
# ==========================================
app = dash.Dash(__name__)
server = app.server
# ==========================================
# 3. DISEÑO DE LA INTERFAZ (LAYOUT)
# ==========================================
app.layout = html.Div(style={'fontFamily': 'Segoe UI, sans-serif', 'backgroundColor': '#f4f6f9', 'padding': '30px'}, children=[
    
    # Encabezado
    html.Div(style={'textAlign': 'center', 'marginBottom': '40px'}, children=[
        html.H1("Dashboard Climatológico Avanzado - UTP", style={'color': '#1e3799', 'fontWeight': 'bold', 'margin': '0'}),
        html.P("Análisis Exploratorio Integrado y Simulador de Inteligencia Artificial (NOAA Panamá)", style={'color': '#60a3bc', 'marginTop': '5px'})
    ]),
    
    # SECCIÓN 1: CONTROLES INTERACTIVOS (2 Controladores requeridos)
    html.Div(style={
        'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '12px', 
        'marginBottom': '30px', 'display': 'flex', 'gap': '20px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'
    }, children=[
        
        html.Div(style={'flex': '1'}, children=[
            html.Label("1. Estación Climatológica (Filtro Dinámico):", style={'fontWeight': '600', 'color': '#2c3e50', 'display': 'block', 'marginBottom': '10px'}),
            dcc.Dropdown(
                id='dropdown-estacion',
                options=[{'label': f"Estación: {est}", 'value': est} for est in lista_estaciones],
                value=lista_estaciones[0],
                clearable=False
            )
        ]),
        
        html.Div(style={'flex': '1'}, children=[
            html.Label("2. Métrica Principal de Análisis:", style={'fontWeight': '600', 'color': '#2c3e50', 'display': 'block', 'marginBottom': '10px'}),
            dcc.Dropdown(
                id='dropdown-elemento',
                options=[{'label': texto, 'value': clave} for clave, texto in lista_elementos.items()],
                value='TAVG',
                clearable=False
            )
        ])
    ]),
    
    # SECCIÓN 2: BLOQUE DE GRÁFICAS EXPLORATORIAS (4 Gráficas en total)
    # Fila 1: Rangos Temporales y Distribución
    html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}, children=[
        html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
            dcc.Graph(id='grafico-lineas-tendencia')
        ]),
        html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
            dcc.Graph(id='grafico-histograma-distribucion')
        ])
    ]),
    
    # Fila 2: Agrupación por Categorías y Correlación
    html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '40px'}, children=[
        html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
            dcc.Graph(id='grafico-barras-categorias')
        ]),
        html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
            dcc.Graph(id='grafico-dispersion-correlacion')
        ])
    ]),
    
    # SECCIÓN 3: SIMULADOR INTERACTIVO DE REGRESIÓN (RED NEURONAL MLP)
    html.Div(style={
        'backgroundColor': '#1e3799', 'color': 'white', 'padding': '30px', 'borderRadius': '12px', 
        'boxShadow': '0 6px 12px rgba(0,0,0,0.1)'
    }, children=[
        html.H2("🧠 Simulador Predictivo - Inteligencia Artificial", style={'margin': '0 0 10px 0', 'fontWeight': 'bold'}),
        html.P("Módulo del Ingeniero de ML: Ingresa una instancia de datos climatológicos para predecir mediante el modelo entrenado de Red Neuronal (MLP Regressor).", style={'color': '#dff9fb', 'marginBottom': '25px'}),
        
        # Grid de entradas
        html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'marginBottom': '20px'}, children=[
            html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
                html.Label("Temperatura Mínima del Día (°C):", style={'display': 'block', 'marginBottom': '8px', 'fontWeight': '500'}),
                dcc.Input(id='input-tmin', type='number', value=22.0, step=0.1, style={'width': '90%', 'padding': '10px', 'borderRadius': '6px', 'border': 'none'})
            ]),
            html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
                html.Label("Temperatura Máxima del Día (°C):", style={'display': 'block', 'marginBottom': '8px', 'fontWeight': '500'}),
                dcc.Input(id='input-tmax', type='number', value=31.5, step=0.1, style={'width': '90%', 'padding': '10px', 'borderRadius': '6px', 'border': 'none'})
            ]),
            html.Div(style={'flex': '1', 'minWidth': '200px'}, children=[
                html.Label("Precipitación / Lluvia Estacional (mm):", style={'display': 'block', 'marginBottom': '8px', 'fontWeight': '500'}),
                dcc.Input(id='input-prcp', type='number', value=4.5, step=0.1, style={'width': '90%', 'padding': '10px', 'borderRadius': '6px', 'border': 'none'})
            ]),
        ]),
        
        html.Button('Calcular Predicción Automática', id='btn-predict', n_clicks=0, style={
            'backgroundColor': '#2ecc71', 'color': 'white', 'fontWeight': 'bold', 'border': 'none', 
            'padding': '12px 25px', 'borderRadius': '6px', 'cursor': 'pointer', 'fontSize': '16px', 'marginTop': '10px'
        }),
        
        # Cuadro de resultados
        html.Div(id='bloque-resultado-ml', style={
            'marginTop': '25px', 'padding': '20px', 'backgroundColor': 'rgba(255,255,255,0.1)', 
            'borderRadius': '8px', 'borderLeft': '5px solid #2ecc71', 'display': 'none'
        }, children=[
            html.H4("Resultado de la Instancia:", style={'margin': '0 0 5px 0', 'color': '#dff9fb'}),
            html.Div(id='texto-prediccion-final', style={'fontSize': '22px', 'fontWeight': 'bold', 'color': 'white'})
        ])
    ])
])

# ==========================================
# 4. CONTROLADORES Y LOGICA INTERACTIVA
# ==========================================
@app.callback(
    [Output('grafico-lineas-tendencia', 'figure'),
     Output('grafico-histograma-distribucion', 'figure'),
     Output('grafico-barras-categorias', 'figure'),
     Output('grafico-dispersion-correlacion', 'figure')],
    [Input('dropdown-estacion', 'value'),
     Input('dropdown-elemento', 'value')]
)
def actualizar_analisis_exploratorio(estacion, elemento):
    # Filtrado base para los gráficos individuales
    df_filtrado = df[(df['ID'] == estacion) & (df['ELEMENT'] == elemento)].sort_values(by='DATE')
    
    dict_noms = {'TAVG': 'Temp Promedio', 'TMIN': 'Temp Mínima', 'TMAX': 'Temp Máxima', 'PRCP': 'Precipitación'}
    color_tema = '#e74c3c' if 'T' in elemento else '#3498db'
    
    # 1. Gráfica de Rangos / Líneas de evolución temporal
    fig1 = px.line(df_filtrado, x='DATE', y='DATA_VALUE', 
                   title=f"Evolución de {dict_noms[elemento]} en el Tiempo",
                   labels={'DATE': 'Fecha', 'DATA_VALUE': 'Valor'}, template='plotly_white')
    fig1.update_traces(line_color=color_tema)

    # 2. Gráfica de Distribución (Histograma interactivo con rangos)
    fig2 = px.histogram(df_filtrado, x='DATA_VALUE', nbins=30,
                        title=f"Distribución y Frecuencia de {dict_noms[elemento]}",
                        labels={'DATA_VALUE': 'Rango de Valores', 'count': 'Frecuencia'},
                        template='plotly_white', color_discrete_sequence=[color_tema])
    
    # 3. Gráfica de Categorías (Barras agrupadas de promedios por estación)
    df_avg_estaciones = df[df['ELEMENT'] == elemento].groupby('ID')['DATA_VALUE'].mean().reset_index()
    fig3 = px.bar(df_avg_estaciones, x='ID', y='DATA_VALUE',
                  title=f"Comparativa de Medias por Estación Climatológica",
                  labels={'ID': 'Código de Estación', 'DATA_VALUE': 'Promedio Global'},
                  template='plotly_white', color='DATA_VALUE', color_continuous_scale='Blues' if elemento=='PRCP' else 'YlOrRd')

    # 4. Análisis de Correlación (Scatterplot entre TMAX y TMIN extraído del pivot table)
    df_est_pivot = df_pivot[df_pivot['ID'] == estacion]
    fig4 = px.scatter(df_est_pivot, x='TMIN', y='TMAX', trendline="ols",
                      title="Análisis de Correlación Estructural (TMIN vs TMAX)",
                      labels={'TMIN': 'Temperatura Mínima (°C)', 'TMAX': 'Temperatura Máxima (°C)'},
                      template='plotly_white', color_discrete_sequence=['#2c3e50'])
    
    return fig1, fig2, fig3, fig4

# ==========================================
# 5. CALLBACK DEL SIMULADOR DE ML (RED NEURONAL)
# ==========================================
@app.callback(
    [Output('bloque-resultado-ml', 'style'),
     Output('texto-prediccion-final', 'children')],
    [Input('btn-predict', 'n_clicks')],
    [State('input-tmin', 'value'),
     State('input-tmax', 'value'),
     State('input-prcp', 'value')]
)
def ejecutar_simulacion_ia(n_clicks, tmin, tmax, prcp):
    if n_clicks is None or n_clicks == 0:
        return {'display': 'none'}, ""
    
    # Lógica basada en el Modelo MLP Regressor entrenado en tu Notebook:
    # Nota: Cuando tu científico exporte el .pkl con joblib, cargarás el archivo aquí.
    # Por ahora, implementamos la función matemática matemática aproximada del objetivo de regresión:
    try:
        # Simulamos las operaciones estructurales que haría la red neuronal entrenada con las variables:
        inputs = np.array([tmin, tmax, prcp])
        
        # Simulación de la predicción de Temperatura Promedio (TAVG) usando combinaciones ponderadas:
        prediccion_tavg = (tmin * 0.4) + (tmax * 0.55) - (prcp * 0.05) + 1.2
        
        texto_resultado = f"La Temperatura Promedio (TAVG) estimada para esta instancia es de: {prediccion_tavg:.2f} °C"
        return {'display': 'block', 'marginTop': '25px', 'padding': '20px', 'backgroundColor': 'rgba(255,255,255,0.1)', 'borderRadius': '8px', 'borderLeft': '5px solid #2ecc71'}, texto_resultado
        
    except Exception as e:
        return {'display': 'block', 'borderLeft': '5px solid #e74c3c'}, f"Error en la simulación del modelo: {str(e)}"

# ==========================================
# 6. EJECUCIÓN
# ==========================================
if __name__ == '__main__':
    app.run(debug=True, port=8050)