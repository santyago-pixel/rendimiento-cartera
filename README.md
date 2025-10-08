# Portfolio Simple Analyzer

Una aplicación Streamlit para analizar la composición actual y evolución de carteras de inversión.

## 🚀 Características

### 📊 Composición Actual de la Cartera
- Tabla que muestra activos con nominales positivos a la fecha actual
- Lógica de "reseteo a cero" para cálculos correctos
- Métricas resumidas: valor total, invertido, flujos netos, ganancia total

### 📈 Análisis de Evolución de la Cartera
- Análisis de activos en un rango de fechas personalizable
- Incluye activos que tuvieron nominales positivos en algún momento del período
- Cálculo de valor al inicio vs valor actual
- Seguimiento de ventas, dividendos, cupones y amortizaciones

### 🔧 Funcionalidades Técnicas
- Carga automática de `operaciones.xlsx` por defecto
- Opción de cargar archivo Excel diferente
- Debug completo para verificación de cálculos
- Exportación de resultados a CSV

## 📁 Estructura de Datos

### Hoja "Operaciones"
| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| Fecha | Fecha de la operación | 2024-10-16 |
| Operacion | Tipo de operación | Compra, Venta, Cupón, Dividendo, Amortización |
| Tipo de activo | Categoría del activo | Bono, Acción |
| Activo | Nombre del activo | AL30, AL41, GD35 |
| Nominales | Cantidad de activos | 1000 |
| Precio | Precio de la transacción | 95.50 |
| Valor | Monto total de la operación | 95500 |

### Hoja "Precios"
- **Columna A**: Fechas (formato fecha)
- **Fila 1**: Nombres de activos como columnas
- **Valores**: Precios de cierre diarios

## 🛠️ Instalación

1. **Clonar el repositorio:**
```bash
git clone https://github.com/tu-usuario/portfolio-simple-analyzer.git
cd portfolio-simple-analyzer
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Ejecutar la aplicación:**
```bash
streamlit run app.py
```

## 📊 Lógica de Cálculos

### Composición Actual
- **Nominales**: Cantidad después del último reset a cero
- **Valor Actual**: Nominales × Precio actual
- **Invertido**: Suma de compras desde el último reset
- **Ganancia Total**: (Valor Actual - Invertido) + Ventas + Div-Cupones

### Evolución de Cartera
- **Elegibilidad**: Activos con nominales positivos en algún momento del período
- **Valor al Inicio**: (Nominales al inicio × Precio al inicio) + Compras en período
- **Ventas**: Suma de ventas desde fecha inicio
- **Div-Cupones**: Suma de dividendos, cupones y amortizaciones desde fecha inicio

## 🔍 Debug y Verificación

La aplicación incluye debug completo que muestra:
- Procesamiento de cada activo
- Cálculo de elegibilidad
- Fechas de reset
- Operaciones consideradas
- Precios utilizados
- Cálculos paso a paso

## 📋 Requisitos

- Python 3.8+
- Streamlit >= 1.28.0
- Pandas >= 2.0.0
- OpenPyXL >= 3.1.0

## 🎯 Casos de Uso

1. **Análisis de cartera actual**: Ver composición y rendimiento actual
2. **Análisis histórico**: Evaluar evolución en períodos específicos
3. **Verificación de cálculos**: Debug detallado para auditoría
4. **Comparación de períodos**: Cambiar fechas para análisis comparativo

## 📝 Notas Importantes

- Los archivos Excel deben seguir la estructura exacta especificada
- Las ventas en el Excel están en valores positivos
- La lógica de reset considera el último reset antes del período analizado
- Los precios se obtienen de la hoja "Precios" usando la fecha más cercana disponible

## 👨‍💻 Autor

**Santiago Aronson**

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.