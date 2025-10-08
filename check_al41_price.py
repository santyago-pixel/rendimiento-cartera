#!/usr/bin/env python3
import pandas as pd
import numpy as np

# Cargar precios
precios = pd.read_excel('operaciones.xlsx', sheet_name='Precios')
fecha_col = precios.columns[0]
precios = precios.rename(columns={fecha_col: 'Fecha'})

# Convertir a formato largo
precios_long = precios.melt(
    id_vars=['Fecha'], 
    var_name='Activo', 
    value_name='Precio'
)
precios_long = precios_long.dropna()

# Filtrar AL41
al41_prices = precios_long[precios_long['Activo'] == 'AL41'].copy()
al41_prices['Fecha'] = pd.to_datetime(al41_prices['Fecha'])

print("=== PRECIOS DE AL41 ===")
print(al41_prices.head(10))

# Buscar precio al 10/08/2025 (fecha de inicio del período)
fecha_inicio = pd.to_datetime('2025-08-10')
available_prices = al41_prices[al41_prices['Fecha'] <= fecha_inicio]

if not available_prices.empty:
    precio_inicio = available_prices.iloc[-1]['Precio']
    fecha_precio = available_prices.iloc[-1]['Fecha']
    print(f'\n=== PRECIO AL INICIO DEL PERÍODO ===')
    print(f'Fecha del precio: {fecha_precio.strftime("%d/%m/%Y")}')
    print(f'Precio: ${precio_inicio:.2f}')
    
    # También mostrar el precio al fin del período
    fecha_fin = pd.to_datetime('2025-10-08')
    available_prices_fin = al41_prices[al41_prices['Fecha'] <= fecha_fin]
    if not available_prices_fin.empty:
        precio_fin = available_prices_fin.iloc[-1]['Precio']
        fecha_precio_fin = available_prices_fin.iloc[-1]['Fecha']
        print(f'\n=== PRECIO AL FIN DEL PERÍODO ===')
        print(f'Fecha del precio: {fecha_precio_fin.strftime("%d/%m/%Y")}')
        print(f'Precio: ${precio_fin:.2f}')
else:
    print('No hay precios disponibles para AL41 antes del 10/08/2025')
