"""
Crear archivo de ejemplo para Portfolio Simple Analyzer
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def create_example_data():
    """Crear datos de ejemplo para testing"""
    
    # Configurar semilla para reproducibilidad
    np.random.seed(42)
    random.seed(42)
    
    # Fechas
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = pd.date_range(start, end, freq='D')
    
    # Activos de ejemplo
    assets = ['AL30', 'GD30', 'YPF', 'GGAL', 'MIRG']
    
    # Generar operaciones
    operaciones_data = []
    
    # Operaciones iniciales
    for asset in assets:
        operaciones_data.append({
            'Fecha': start_date,
            'Operacion': 'Compra',
            'Tipo de activo': 'Bono' if 'AL' in asset or 'GD' in asset else 'Accion',
            'Activo': asset,
            'Nominales': random.randint(100, 500),
            'Precio': random.uniform(90, 110) if 'AL' in asset or 'GD' in asset else random.uniform(1000, 2000),
            'Valor': 0  # Se calculará
        })
    
    # Generar operaciones aleatorias
    for _ in range(30):
        fecha = random.choice(date_range[30:])
        asset = random.choice(assets)
        tipo = random.choice(['Compra', 'Venta', 'Cupón', 'Dividendo'])
        
        if tipo in ['Compra', 'Venta']:
            cantidad = random.randint(50, 200)
            precio = random.uniform(90, 110) if 'AL' in asset or 'GD' in asset else random.uniform(1000, 2000)
            monto = cantidad * precio
        else:
            cantidad = 0
            precio = 0
            monto = random.randint(100, 1000)
        
        operaciones_data.append({
            'Fecha': fecha,
            'Operacion': tipo,
            'Tipo de activo': 'Bono' if 'AL' in asset or 'GD' in asset else 'Accion',
            'Activo': asset,
            'Nominales': cantidad,
            'Precio': precio,
            'Valor': monto
        })
    
    # Calcular montos para operaciones de compra/venta
    for op in operaciones_data:
        if op['Operacion'] in ['Compra', 'Venta'] and op['Valor'] == 0:
            op['Valor'] = op['Nominales'] * op['Precio']
    
    operaciones_df = pd.DataFrame(operaciones_data)
    operaciones_df = operaciones_df.sort_values('Fecha')
    
    # Generar precios
    precios_data = []
    for asset in assets:
        precio_inicial = random.uniform(90, 110) if 'AL' in asset or 'GD' in asset else random.uniform(1000, 2000)
        precio_actual = precio_inicial
        
        for fecha in date_range:
            # Generar retorno diario
            if 'AL' in asset or 'GD' in asset:
                retorno = np.random.normal(0.0002, 0.02)
            else:
                retorno = np.random.normal(0.0005, 0.03)
            
            precio_actual *= (1 + retorno)
            
            precios_data.append({
                'Fecha': fecha,
                asset: round(precio_actual, 2)
            })
    
    # Crear DataFrame de precios
    precios_df = pd.DataFrame(precios_data)
    precios_df = precios_df.drop_duplicates(subset=['Fecha'])
    
    return operaciones_df, precios_df

def save_example_excel():
    """Guardar datos de ejemplo en Excel"""
    operaciones, precios = create_example_data()
    
    with pd.ExcelWriter('ejemplo_cartera.xlsx', engine='openpyxl') as writer:
        operaciones.to_excel(writer, sheet_name='Operaciones', index=False)
        precios.to_excel(writer, sheet_name='Precios', index=False)
    
    print("✅ Archivo de ejemplo creado: ejemplo_cartera.xlsx")
    return operaciones, precios

if __name__ == "__main__":
    save_example_excel()
