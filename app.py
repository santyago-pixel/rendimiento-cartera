"""
Portfolio Simple Analyzer
=========================

Aplicación simple para analizar la composición actual de carteras de inversión.
Muestra activos con nominales positivos después del último reset a cero.

Autor: Santiago Aronson
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="Portfolio Simple Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .positive {
        color: #00C851;
    }
    .negative {
        color: #ff4444;
    }
</style>
""", unsafe_allow_html=True)

def load_data(filename='operaciones.xlsx'):
    """Cargar datos automáticamente desde operaciones.xlsx o archivo especificado"""
    try:
        # Cargar operaciones
        operaciones = pd.read_excel(filename, sheet_name='Operaciones')
        
        # Mapear columnas a formato esperado
        operaciones_mapped = pd.DataFrame()
        operaciones_mapped['Fecha'] = operaciones['Fecha']
        operaciones_mapped['Tipo'] = operaciones['Operacion']
        operaciones_mapped['Activo'] = operaciones['Activo']
        operaciones_mapped['Cantidad'] = operaciones['Nominales']
        operaciones_mapped['Precio'] = operaciones['Precio']
        operaciones_mapped['Monto'] = operaciones['Valor']
        
        # Limpiar datos
        operaciones_mapped['Tipo'] = operaciones_mapped['Tipo'].str.strip()
        operaciones_mapped['Activo'] = operaciones_mapped['Activo'].str.strip()
        operaciones_mapped = operaciones_mapped.dropna(subset=['Fecha', 'Tipo', 'Activo', 'Monto'])
        
        # Cargar precios
        precios = pd.read_excel(filename, sheet_name='Precios')
        
        # Convertir a formato largo
        fecha_col = precios.columns[0]
        precios = precios.rename(columns={fecha_col: 'Fecha'})
        
        precios_long = precios.melt(
            id_vars=['Fecha'], 
            var_name='Activo', 
            value_name='Precio'
        )
        precios_long = precios_long.dropna()
        
        return operaciones_mapped, precios_long
        
    except FileNotFoundError:
        st.error(f"No se encontró el archivo '{filename}' en la carpeta del proyecto")
        return None, None
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        return None, None

def calculate_current_portfolio(operaciones, precios, fecha_actual):
    """Calcular composición actual de la cartera con lógica de reseteo"""
    
    # Convertir fechas
    operaciones['Fecha'] = pd.to_datetime(operaciones['Fecha'])
    precios['Fecha'] = pd.to_datetime(precios['Fecha'])
    
    # Obtener activos únicos
    assets = operaciones['Activo'].unique()
    assets = [asset for asset in assets if pd.notna(asset)]
    
    portfolio_data = []
    
    for asset in assets:
        # Obtener operaciones del activo ordenadas por fecha
        asset_ops = operaciones[operaciones['Activo'] == asset].sort_values('Fecha')
        
        # Filtrar operaciones hasta la fecha actual
        asset_ops_until_date = asset_ops[asset_ops['Fecha'] <= pd.to_datetime(fecha_actual)]
        
        if asset_ops_until_date.empty:
            continue
        
        # Encontrar el ÚLTIMO reset a cero (cuando los nominales pasan de positivo a cero o negativo)
        running_nominals = 0
        last_reset_date = None
        
        # Recorrer todas las operaciones para encontrar el último reset
        for _, op in asset_ops_until_date.iterrows():
            previous_nominals = running_nominals
            
            if op['Tipo'].strip() == 'Compra':
                running_nominals += op['Cantidad']
            elif op['Tipo'].strip() == 'Venta':
                running_nominals -= op['Cantidad']
            
            # Si los nominales pasan de positivo a cero o negativo, es un reset
            if previous_nominals > 0 and running_nominals <= 0:
                last_reset_date = op['Fecha']
                running_nominals = 0  # Reset a cero
        
        # Determinar operaciones a procesar
        if last_reset_date is None:
            # Si no hay ningún reset, usar todas las operaciones desde el inicio
            ops_since_reset = asset_ops_until_date
        else:
            # Si hay reset, usar solo las operaciones DESPUÉS del último reset
            ops_since_reset = asset_ops_until_date[asset_ops_until_date['Fecha'] > last_reset_date]
        
        # Calcular nominales actuales desde el reset
        current_nominals = 0
        total_invested = 0
        total_sales = 0
        total_dividends_coupons = 0
        
        for _, op in ops_since_reset.iterrows():
            if op['Tipo'].strip() == 'Compra':
                current_nominals += op['Cantidad']
                total_invested += op['Monto']
            elif op['Tipo'].strip() == 'Venta':
                current_nominals -= op['Cantidad']
                total_sales += op['Monto']
            elif any(keyword in op['Tipo'].strip().lower() for keyword in ['dividendo', 'cupon', 'dividend', 'coupon', 'amortizacion', 'amortización']):
                total_dividends_coupons += op['Monto']
        
        # Solo incluir activos con nominales positivos
        if current_nominals > 0:
            # Obtener precio actual
            asset_prices = precios[precios['Activo'] == asset]
            if not asset_prices.empty:
                # Buscar precio más reciente hasta la fecha actual
                available_prices = asset_prices[asset_prices['Fecha'] <= pd.to_datetime(fecha_actual)]
                if not available_prices.empty:
                    current_price = available_prices.iloc[-1]['Precio']
                    current_value = current_nominals * current_price
                    
                    # Ganancia total = (Valor Actual - Inversión) + Dividendos/Cupones + Ventas
                    # Las ventas son capital recibido, por lo tanto se suman
                    total_gain = (current_value - total_invested) + total_dividends_coupons + total_sales
                    
                    portfolio_data.append({
                        'Activo': asset,
                        'Nominales': current_nominals,
                        'Precio Actual': current_price,
                        'Valor Actual': current_value,
                        'Invertido': total_invested,
                        'Ventas': total_sales,
                        'Div - Cupones': total_dividends_coupons,
                        'Ganancia Total': total_gain
                    })
    
    return pd.DataFrame(portfolio_data)

def calculate_portfolio_evolution(operaciones, precios, fecha_inicio, fecha_fin):
    """Calcular evolución de la cartera en un rango de fechas"""
    
    # Convertir fechas
    operaciones['Fecha'] = pd.to_datetime(operaciones['Fecha'])
    precios['Fecha'] = pd.to_datetime(precios['Fecha'])
    
    # Obtener activos únicos
    assets = operaciones['Activo'].unique()
    assets = [asset for asset in assets if pd.notna(asset)]
    
    evolution_data = []
    
    for asset in assets:
        # Obtener operaciones del activo ordenadas por fecha
        asset_ops = operaciones[operaciones['Activo'] == asset].sort_values('Fecha')
        
        # PASO 1: Identificar si el activo tuvo nominales positivos en algún momento del período
        had_positive_nominals_in_period = False
        temp_nominals = 0
        
        # Verificar todas las operaciones del activo hasta la fecha fin
        for _, op in asset_ops.iterrows():
            if op['Fecha'] > pd.to_datetime(fecha_fin):
                break
                
            if op['Tipo'].strip() == 'Compra':
                temp_nominals += op['Cantidad']
            elif op['Tipo'].strip() == 'Venta':
                temp_nominals -= op['Cantidad']
            
            # Verificar si en algún momento del período tuvo nominales positivos
            if (op['Fecha'] >= pd.to_datetime(fecha_inicio) and 
                op['Fecha'] <= pd.to_datetime(fecha_fin) and 
                temp_nominals > 0):
                had_positive_nominals_in_period = True
                break
        
        # CORRECCIÓN ADICIONAL: Verificar si tenía nominales positivos al inicio del período
        if not had_positive_nominals_in_period:
            # Calcular nominales al inicio del período
            temp_nominals_inicio = 0
            for _, op in asset_ops.iterrows():
                if op['Fecha'] >= pd.to_datetime(fecha_inicio):
                    break
                if op['Tipo'].strip() == 'Compra':
                    temp_nominals_inicio += op['Cantidad']
                elif op['Tipo'].strip() == 'Venta':
                    temp_nominals_inicio -= op['Cantidad']
            
            if temp_nominals_inicio > 0:
                had_positive_nominals_in_period = True
        
        # Si no tuvo nominales positivos en el período, continuar con el siguiente activo
        if not had_positive_nominals_in_period:
            continue
        
        # PASO 2: Encontrar el último reset ANTES o EN el inicio del período
        running_nominals = 0
        last_reset_date = None
        
        # Recorrer todas las operaciones hasta la fecha de inicio para encontrar el último reset ANTES o EN el período
        for _, op in asset_ops.iterrows():
            if op['Fecha'] > pd.to_datetime(fecha_inicio):
                break
                
            previous_nominals = running_nominals
            
            if op['Tipo'].strip() == 'Compra':
                running_nominals += op['Cantidad']
            elif op['Tipo'].strip() == 'Venta':
                running_nominals -= op['Cantidad']
            
            # Si los nominales pasan de positivo a cero o negativo, es un reset
            if previous_nominals > 0 and running_nominals <= 0:
                last_reset_date = op['Fecha']
                running_nominals = 0  # Reset a cero
        
        # PASO 3: Calcular nominales desde la fecha posterior al último reset hasta fecha fin
        if last_reset_date is None:
            # Si no hay reset, usar todas las operaciones desde el inicio
            ops_since_reset = asset_ops[asset_ops['Fecha'] <= pd.to_datetime(fecha_fin)]
        else:
            # Si hay reset, usar operaciones desde la fecha posterior al reset
            ops_since_reset = asset_ops[
                (asset_ops['Fecha'] > last_reset_date) & 
                (asset_ops['Fecha'] <= pd.to_datetime(fecha_fin))
            ]
        
        # Calcular nominales al inicio del rango (desde reset hasta fecha_inicio)
        current_nominals_inicio = 0
        total_invested_hasta_inicio = 0
        total_sales_hasta_inicio = 0
        total_dividends_coupons_hasta_inicio = 0
        
        # Procesar operaciones hasta la fecha de inicio
        ops_until_inicio = ops_since_reset[ops_since_reset['Fecha'] <= pd.to_datetime(fecha_inicio)]
        
        for _, op in ops_until_inicio.iterrows():
            if op['Tipo'].strip() == 'Compra':
                current_nominals_inicio += op['Cantidad']
                total_invested_hasta_inicio += op['Monto']
            elif op['Tipo'].strip() == 'Venta':
                current_nominals_inicio -= op['Cantidad']
                total_sales_hasta_inicio += op['Monto']
            elif any(keyword in op['Tipo'].strip().lower() for keyword in ['dividendo', 'cupon', 'dividend', 'coupon', 'amortizacion', 'amortización']):
                total_dividends_coupons_hasta_inicio += op['Monto']
        
        # Calcular nominales al fin del rango (desde reset hasta fecha_fin)
        current_nominals_fin = current_nominals_inicio
        total_invested_hasta_fin = total_invested_hasta_inicio
        total_sales_hasta_fin = total_sales_hasta_inicio
        total_dividends_coupons_hasta_fin = total_dividends_coupons_hasta_inicio
        
        # Procesar operaciones en el rango de fechas
        ops_en_rango = ops_since_reset[
            (ops_since_reset['Fecha'] >= pd.to_datetime(fecha_inicio)) &
            (ops_since_reset['Fecha'] <= pd.to_datetime(fecha_fin))
        ]
        
        for _, op in ops_en_rango.iterrows():
            if op['Tipo'].strip() == 'Compra':
                current_nominals_fin += op['Cantidad']
                total_invested_hasta_fin += op['Monto']
            elif op['Tipo'].strip() == 'Venta':
                current_nominals_fin -= op['Cantidad']
                total_sales_hasta_fin += op['Monto']
            elif any(keyword in op['Tipo'].strip().lower() for keyword in ['dividendo', 'cupon', 'dividend', 'coupon', 'amortizacion', 'amortización']):
                total_dividends_coupons_hasta_fin += op['Monto']
        
        # Obtener precios al inicio y fin
        asset_prices = precios[precios['Activo'] == asset]
        
        # Precio al inicio
        available_prices_inicio = asset_prices[asset_prices['Fecha'] <= pd.to_datetime(fecha_inicio)]
        precio_inicio = available_prices_inicio.iloc[-1]['Precio'] if not available_prices_inicio.empty else 0
        
        # Precio al fin
        available_prices_fin = asset_prices[asset_prices['Fecha'] <= pd.to_datetime(fecha_fin)]
        precio_fin = available_prices_fin.iloc[-1]['Precio'] if not available_prices_fin.empty else 0
        
        # Calcular el costo de todas las compras dentro del período
        valor_inicio = 0
        
        # 1. Si hay nominales existentes al inicio del período (por reset anterior):
        if current_nominals_inicio > 0:
            # CORRECCIÓN: Usar precio al inicio del período, no al momento del reset
            valor_inicio += current_nominals_inicio * precio_inicio
        
        # 2. Sumar solo las compras DENTRO del período:
        # Filtrar solo las operaciones de compra en el período
        compras_en_periodo = 0
        for _, op in ops_en_rango.iterrows():
            if op['Tipo'].strip() == 'Compra':
                compras_en_periodo += op['Monto']
        
        valor_inicio += compras_en_periodo
        
        # Valor al fin (nominales al fin * precio al fin)
        valor_fin = current_nominals_fin * precio_fin
        
        # Dividendos/cupones/amortizaciones solo desde la fecha de inicio
        div_cupones_desde_inicio = total_dividends_coupons_hasta_fin - total_dividends_coupons_hasta_inicio
        
        # Ventas desde la fecha de inicio
        ventas_desde_inicio = total_sales_hasta_fin - total_sales_hasta_inicio
        
        # Ganancia total usando valor al inicio como base
        total_gain = (valor_fin - valor_inicio) + div_cupones_desde_inicio + ventas_desde_inicio
        
        evolution_data.append({
            'Activo': asset,
            'Nominales': current_nominals_fin,
            'Precio Actual': precio_fin,
            'Valor Actual': valor_fin,
            'Valor al Inicio': valor_inicio,
            'Ventas': ventas_desde_inicio,
            'Div - Cupones': div_cupones_desde_inicio,
            'Ganancia Total': total_gain
        })
    
    return pd.DataFrame(evolution_data)

def mostrar_analisis_detallado_activo(operaciones, precios, activo, fecha_inicio, fecha_fin):
    """Mostrar análisis detallado de un activo específico"""
    
    # Convertir fechas
    operaciones['Fecha'] = pd.to_datetime(operaciones['Fecha'])
    precios['Fecha'] = pd.to_datetime(precios['Fecha'])
    
    # Filtrar operaciones del activo
    asset_ops = operaciones[operaciones['Activo'] == activo].sort_values('Fecha')
    
    # PASO 1: Encontrar el último reset ANTES o EN el inicio del período
    running_nominals = 0
    last_reset_date = None
    
    # Recorrer todas las operaciones hasta la fecha de inicio para encontrar el último reset
    for _, op in asset_ops.iterrows():
        if op['Fecha'] > pd.to_datetime(fecha_inicio):
            break
            
        previous_nominals = running_nominals
        
        if op['Tipo'].strip() == 'Compra':
            running_nominals += op['Cantidad']
        elif op['Tipo'].strip() == 'Venta':
            running_nominals -= op['Cantidad']
        
        # Si los nominales pasan de positivo a cero o negativo, es un reset
        if previous_nominals > 0 and running_nominals <= 0:
            last_reset_date = op['Fecha']
            running_nominals = 0  # Reset a cero
    
    # PASO 2: Determinar operaciones a procesar
    if last_reset_date is None:
        # Si no hay reset, usar todas las operaciones desde el inicio hasta fecha fin
        ops_since_reset = asset_ops[asset_ops['Fecha'] <= pd.to_datetime(fecha_fin)]
    else:
        # Si hay reset, usar operaciones desde la fecha posterior al reset hasta fecha fin
        ops_since_reset = asset_ops[
            (asset_ops['Fecha'] > last_reset_date) & 
            (asset_ops['Fecha'] <= pd.to_datetime(fecha_fin))
        ]
    
    # PASO 3: Calcular nominales al inicio del período
    current_nominals_inicio = 0
    for _, op in ops_since_reset.iterrows():
        if op['Fecha'] > pd.to_datetime(fecha_inicio):
            break
        if op['Tipo'].strip() == 'Compra':
            current_nominals_inicio += op['Cantidad']
        elif op['Tipo'].strip() == 'Venta':
            current_nominals_inicio -= op['Cantidad']
    
    # PASO 4: Crear tabla detallada
    detalle_data = []
    
    # Agregar valor inicial si hay nominales al inicio del período
    if current_nominals_inicio > 0:
        # Obtener precio al inicio del período
        asset_prices = precios[precios['Activo'] == activo]
        available_prices_inicio = asset_prices[asset_prices['Fecha'] <= pd.to_datetime(fecha_inicio)]
        precio_inicio = available_prices_inicio.iloc[-1]['Precio'] if not available_prices_inicio.empty else 0
        
        detalle_data.append({
            'Fecha': fecha_inicio,
            'Operación': 'Valor Inicial',
            'Nominales': current_nominals_inicio,
            'Precio': precio_inicio,
            'Valor': current_nominals_inicio * precio_inicio
        })
    
    # Agregar todas las operaciones en el período
    ops_en_periodo = ops_since_reset[
        (ops_since_reset['Fecha'] >= pd.to_datetime(fecha_inicio)) &
        (ops_since_reset['Fecha'] <= pd.to_datetime(fecha_fin))
    ]
    
    for _, op in ops_en_periodo.iterrows():
        detalle_data.append({
            'Fecha': op['Fecha'],
            'Operación': op['Tipo'],
            'Nominales': op['Cantidad'],
            'Precio': op['Precio'],
            'Valor': op['Monto']
        })
    
    # Crear DataFrame y formatear
    detalle_df = pd.DataFrame(detalle_data)
    
    if not detalle_df.empty:
        # Formatear fechas
        detalle_df['Fecha'] = pd.to_datetime(detalle_df['Fecha']).dt.strftime('%d/%m/%Y')
        
        # Formatear números con comas
        detalle_display = detalle_df.copy()
        detalle_display['Nominales'] = detalle_display['Nominales'].apply(lambda x: f"{x:,.0f}")
        detalle_display['Precio'] = detalle_display['Precio'].apply(lambda x: f"${x:,.2f}")
        detalle_display['Valor'] = detalle_display['Valor'].apply(lambda x: f"${x:,.2f}")
        
        # Mostrar tabla
        st.markdown(f"**Operaciones detalladas para {activo}:**")
        st.dataframe(
            detalle_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fecha": st.column_config.TextColumn("Fecha", width="small"),
                "Operación": st.column_config.TextColumn("Operación", width="medium"),
                "Nominales": st.column_config.TextColumn("Nominales", width="small"),
                "Precio": st.column_config.TextColumn("Precio", width="small"),
                "Valor": st.column_config.TextColumn("Valor", width="small")
            }
        )
        
        # Botón de descarga
        csv_detalle = detalle_df.to_csv(index=False)
        st.download_button(
            label=f"📥 Descargar CSV - {activo}",
            data=csv_detalle,
            file_name=f"detalle_{activo}_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info(f"No hay operaciones para {activo} en el período seleccionado.")

def main():
    # Sidebar
    with st.sidebar:
        st.header("Configuración")
        
        # Botón para cargar archivo diferente
        uploaded_file = st.file_uploader(
            "Cargar archivo Excel diferente",
            type=['xlsx', 'xls'],
            help="Opcional: Cargar un archivo Excel diferente al operaciones.xlsx"
        )
        
        # Fecha actual
        fecha_actual = st.date_input(
            "Fecha actual",
            value=datetime.now().date(),
            help="Fecha para calcular la composición actual"
        )
        
        st.markdown("---")
        st.subheader("Análisis de Evolución")
        
        # Fechas para análisis de evolución
        fecha_inicio = st.date_input(
            "Fecha de Inicio",
            value=(datetime.now().date() - timedelta(days=365)),
            help="Fecha de inicio para el análisis de evolución"
        )
        
        fecha_fin = st.date_input(
            "Fecha de Fin",
            value=datetime.now().date(),
            help="Fecha de fin para el análisis de evolución"
        )
    
    # Determinar qué archivo usar
    if uploaded_file is not None:
        # Guardar archivo temporalmente
        with open("temp_file.xlsx", "wb") as f:
            f.write(uploaded_file.getbuffer())
        filename = "temp_file.xlsx"
        st.success(f"📁 Archivo cargado: {uploaded_file.name}")
    else:
        filename = 'operaciones.xlsx'
    
    # Cargar datos
    operaciones, precios = load_data(filename)
    
    if operaciones is not None and precios is not None:
        # Calcular composición actual
        portfolio_df = calculate_current_portfolio(operaciones, precios, fecha_actual)
        
        if not portfolio_df.empty:
            st.header("Composición Actual de la Cartera")
            st.markdown(f"*Calculado al {fecha_actual.strftime('%d/%m/%Y')}*")
            
            # Mostrar métricas resumidas
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                total_assets = len(portfolio_df)
                st.metric("Total de Activos", total_assets)
            
            with col2:
                total_value = portfolio_df['Valor Actual'].sum()
                st.metric("Valor Total", f"${total_value:,.2f}")
            
            with col3:
                total_invested = portfolio_df['Invertido'].sum()
                st.metric("Total Invertido", f"${total_invested:,.2f}")
            
            with col4:
                # Flujos netos = Ventas + Div-Cupones
                total_sales = portfolio_df['Ventas'].sum()
                total_div_cupones = portfolio_df['Div - Cupones'].sum()
                flujos_netos = total_sales + total_div_cupones
                st.metric("Flujos Netos", f"${flujos_netos:,.2f}")
            
            with col5:
                total_gain = portfolio_df['Ganancia Total'].sum()
                gain_pct = (total_gain / total_invested * 100) if total_invested > 0 else 0
                st.metric("Ganancia Total", f"${total_gain:,.2f}", f"{gain_pct:.1f}%")
            
            # Formatear números con comas antes de mostrar
            portfolio_display = portfolio_df.copy()
            numeric_cols = ['Nominales', 'Precio Actual', 'Valor Actual', 'Invertido', 'Ventas', 'Div - Cupones', 'Ganancia Total']
            for col in numeric_cols:
                if col == 'Nominales':
                    portfolio_display[col] = portfolio_display[col].apply(lambda x: f"{x:,.0f}")
                else:
                    portfolio_display[col] = portfolio_display[col].apply(lambda x: f"${x:,.2f}")
            
            # Mostrar tabla
            st.dataframe(
                portfolio_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Activo": st.column_config.TextColumn("Activo", width="medium")
                }
            )
            
            # Botón de descarga
            csv = portfolio_df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"composicion_cartera_{fecha_actual.strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No hay activos con nominales positivos en la fecha seleccionada.")
        
        # Análisis de Evolución
        st.header("Análisis de la Evolución de la Cartera")
        st.markdown(f"*Análisis del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}*")
        
        # Calcular evolución de la cartera
        evolution_df = calculate_portfolio_evolution(operaciones, precios, fecha_inicio, fecha_fin)
        
        if not evolution_df.empty:
            # Mostrar métricas resumidas de evolución
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                total_assets_evo = len(evolution_df)
                st.metric("Total de Activos", total_assets_evo)
            
            with col2:
                total_value_evo = evolution_df['Valor Actual'].sum()
                st.metric("Valor Total", f"${total_value_evo:,.2f}")
            
            with col3:
                total_value_inicio = evolution_df['Valor al Inicio'].sum()
                st.metric("Valor al Inicio", f"${total_value_inicio:,.2f}")
            
            with col4:
                # Flujos netos = Ventas + Div-Cupones
                total_sales_evo = evolution_df['Ventas'].sum()
                total_div_cupones_evo = evolution_df['Div - Cupones'].sum()
                flujos_netos_evo = total_sales_evo + total_div_cupones_evo
                st.metric("Flujos Netos", f"${flujos_netos_evo:,.2f}")
            
            with col5:
                total_gain_evo = evolution_df['Ganancia Total'].sum()
                gain_pct_evo = (total_gain_evo / total_value_inicio * 100) if total_value_inicio > 0 else 0
                st.metric("Ganancia Total", f"${total_gain_evo:,.2f}", f"{gain_pct_evo:.1f}%")
            
            # Formatear números con comas antes de mostrar
            evolution_display = evolution_df.copy()
            numeric_cols_evo = ['Nominales', 'Precio Actual', 'Valor Actual', 'Valor al Inicio', 'Ventas', 'Div - Cupones', 'Ganancia Total']
            for col in numeric_cols_evo:
                if col == 'Nominales':
                    evolution_display[col] = evolution_display[col].apply(lambda x: f"{x:,.0f}")
                else:
                    evolution_display[col] = evolution_display[col].apply(lambda x: f"${x:,.2f}")
            
            # Mostrar tabla de evolución
            st.dataframe(
                evolution_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Activo": st.column_config.TextColumn("Activo", width="medium")
                }
            )
            
            # Botón de descarga para evolución
            csv_evo = evolution_df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar CSV Evolución",
                data=csv_evo,
                file_name=f"evolucion_cartera_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No hay datos de evolución para el rango de fechas seleccionado.")
        
        # Análisis detallado por activo
        if not evolution_df.empty:
            st.markdown("---")
            st.subheader("📋 Análisis Detallado por Activo")
            
            # Selector de activos
            activos_disponibles = evolution_df['Activo'].tolist()
            activo_seleccionado = st.selectbox(
                "Seleccionar activo para análisis detallado:",
                activos_disponibles,
                help="Selecciona un activo para ver todas las operaciones consideradas en el período"
            )
            
            if activo_seleccionado:
                # Mostrar análisis detallado del activo seleccionado
                mostrar_analisis_detallado_activo(operaciones, precios, activo_seleccionado, fecha_inicio, fecha_fin)
    else:
        st.error("Error al cargar los datos. Verifica que el archivo 'operaciones.xlsx' esté en la carpeta del proyecto.")

if __name__ == "__main__":
    main()
