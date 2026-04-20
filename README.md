# Prueba Técnica — Modelo KMV y Análisis Financiero · Emisores Colombia

Repositorio con el desarrollo completo de la prueba técnica. Contiene extracción de estados financieros públicos en formato XBRL (RNVE / Superintendencia Financiera), implementación del modelo KMV–Merton para calcular probabilidades de incumplimiento y análisis histórico de métricas financieras.

---

## Contenido del repositorio

```
├── parte_1/
│   ├── KMV_Punto1_Extraccion_Pasivos.ipynb   # Notebook principal
│   ├── app.py                                 # Dashboard Streamlit interactivo
│   ├── eeff_kmv_completo.csv                  # EEFF extraídos de XBRL (5 emisores)
│   ├── kmv_resultados.csv                     # PD, DD y parámetros KMV por emisor/trimestre
│   ├── punto2_ecopetrol_analisis.csv          # Métricas EEFF vs PD (Ecopetrol)
│   ├── rating_ecopetrol_historico.csv         # Calificaciones crediticias históricas Ecopetrol
│   └── speech_video_kmv.txt                   # Guión del video de presentación
├── EEFF/                                      # Archivos XBRL por emisor (fuente: RNVE)
│   ├── BANCOBOGOTA/
│   ├── BANCOLOMBIA/
│   ├── CEMARGOS/
│   ├── ECOPETROL/
│   └── GRUPO NUTRESA/
├── parte_2_MMV.docx                           # Parte 2 de la prueba técnica (desarrollo escrito)
├── presentacion.mp4                           # Video de presentación del análisis
├── requirements.txt
└── README.md
```

---

## Descripción del proyecto

### Punto 1 — Modelo KMV

Se implementa el modelo KMV–Merton en su versión iterativa para cinco emisores del mercado de valores colombiano:

- **Banco de Bogotá**, **Bancolombia**, **Cementos Argos**, **Ecopetrol**, **Grupo Nutresa**

El modelo calcula, para cada corte trimestral (2017–2022):

| Variable | Descripción |
|---|---|
| `V_A` | Valor de mercado de los activos (solver Merton) |
| `sigma_A` | Volatilidad de activos |
| `DD` | Distance to Default |
| `PD` | Probabilidad de incumplimiento N(−DD) |

**Fuentes de datos:**
- EEFF en formato XBRL: [RNVE – Superintendencia Financiera](https://www.superfinanciera.gov.co/jsp/loader.jsf?lServicio=PublicacionesNoticias&lTipo=publicaciones&lFuncion=loadContenidoPublicacion&id=62714) (informes bajo NIIF)
- Precios de mercado: Yahoo Finance vía `yfinance` (tickers BVC + ADR donde aplica)
- TRM histórica: Banco de la República (API de datos abiertos)

**Literal b — PD vs calificación de crédito (Emisor: Ecopetrol)**

Se compara la evolución de la PD calculada con la calificación crediticia histórica de Ecopetrol (Fitch Ratings Colombia, largo plazo). Las calificaciones están en `rating_ecopetrol_historico.csv`.

### Punto 2 — Análisis de métricas financieras

Para Ecopetrol se calculan métricas históricas vinculadas a la probabilidad de incumplimiento:

- **Apalancamiento:** Deuda Neta / EBITDA
- **Cobertura:** EBIT / Costos financieros
- **Márgenes:** Margen EBITDA, Margen Neto
- **Liquidez:** Razón Corriente, Caja / Activos totales

Los resultados se comparan explícitamente contra la PD del Punto 1.

---

### Parte 2 — `parte_2_MMV.docx`

Documento con el desarrollo escrito de la segunda parte de la prueba técnica. Contiene el análisis, conclusiones y respuestas a las preguntas teóricas y metodológicas complementarias al ejercicio cuantitativo de la Parte 1.

---

## Reproducción

> ⚠️ **Requisito de ruta:** Clona o copia el proyecto en una ruta **sin espacios ni caracteres especiales**.
> Rutas como `C:\Users\Mi Usuario\Mis Documentos\` causan errores en el parser XBRL (Arelle) y en la resolución de rutas relativas.
> Usa algo como `C:\proyectos\kmv_colombia\` o `C:\Users\nombre\kmv_colombia\`.

### 1. Clonar el repositorio

```bash
git clone https://github.com/<tu-usuario>/<tu-repo>.git
cd <tu-repo>
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

> Se requiere **Python 3.9+**. La librería `arelle-release` se usa para parsear archivos XBRL.

### 3. Datos de entrada

Los archivos XBRL deben estar ubicados en `EEFF/<EMISOR>/` tal como están en el repositorio. No se eliminó ningún archivo fuente para garantizar la reproducibilidad completa.

### 4. Ejecutar el notebook

Abrir `parte_1/KMV_Punto1_Extraccion_Pasivos.ipynb` en Jupyter o VS Code y ejecutar las celdas en orden. El notebook está diseñado para correr de principio a fin sin intervención manual.

> ⚠️ La extracción de XBRL tarda ~10 minutos dependiendo del equipo. El notebook guarda los resultados intermedios en CSV para evitar reprocesar.

### 5. Lanzar el dashboard interactivo

```bash
cd parte_1
streamlit run app.py
```

El dashboard abre automáticamente en `http://localhost:8501` y contiene cuatro páginas:

| Página | Contenido |
|---|---|
| Contexto & Modelo | Pipeline metodológico y KPIs globales |
| Punto 1 — Evolución PD | Figura 1 interactiva con filtros por emisor y fecha |
| Literal b — PD vs Rating | Figura 2 dual-eje: PD trimestral vs calificación Fitch |
| Punto 2 — EEFF vs PD | Figura 3 + paneles de métricas financieras de Ecopetrol |

---

## Video de presentación

> 🎥 **`presentacion.mp4`** — incluido en la raíz del repositorio.
>
> El video recorre en ~7 minutos la metodología implementada, los resultados obtenidos y las conclusiones del análisis comparativo entre la probabilidad de incumplimiento (KMV) y las métricas financieras del emisor seleccionado. La presentación se apoya en el dashboard Streamlit (`app.py`) como soporte visual.

---

## Referencia

Modelo basado en:
- Merton, R. C. (1974). *On the pricing of corporate debt: the risk structure of interest rates*. Journal of Finance.
- KMV Corporation (2003). *Modeling Default Risk*.
- Ejemplo de implementación: [andres-gomez-hernandez/Financial_markets_datascience](https://github.com/andres-gomez-hernandez/Financial_markets_datascience)
