# CarlosTech Math AI v3.5 - Motor Profesional con IA Gratuita

## 🚀 Nuevas Características

### ✨ IA GRATUITA INTEGRADA (Google Gemini)
El servidor ahora usa **Google Gemini** (modelo `gemini-1.5-flash`) completamente **GRATIS** para generar explicaciones detalladas paso a paso de cómo resolver integrales.

### 📚 Módulo IntegrationExplainer
Genera explicaciones automáticas de dos formas:

1. **Con IA Gemini** (si está configurada):
   - Análisis inteligente del tipo de integral
   - Identificación automática del método
   - Pasos de resolución ordenados
   - Simplificación final con LaTeX

2. **Con Reglas Matemáticas** (fallback, SIEMPRE funciona):
   - Sistema basado en reglas puras
   - No requiere API
   - Funciona sin conexión

---

## 🔧 INSTALACIÓN Y CONFIGURACIÓN

### Paso 1: Instalar paquete de Google AI
```bash
pip install google-generativeai
```

O si usas el requirements.txt actualizado:
```bash
pip install -r requirements.txt
```

### Paso 2: Obtener API Key GRATIS de Google Gemini

**Importante**: Google ofrece tier GRATUITO generoso para Gemini:
- **500 solicitudes por minuto**
- **Prompts ilimitados** (hasta ciertos límites)
- **NO requiere tarjeta de crédito**

#### Obtener tu API Key GRATIS:
1. Ve a: https://aistudio.google.com/app/apikey
2. Haz clic en "Create API Key"
3. Selecciona o crea un proyecto
4. Copia el API Key

### Paso 3: Configurar la Variable de Entorno

En tu sistema operativo, establece la variable de entorno:

**Windows (CMD/PowerShell):**
```powershell
$env:GEMINI_API_KEY = "tu-api-key-aqui"
```

**Windows (Permanentemente - .env file):**
```
GEMINI_API_KEY=tu-api-key-aqui
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY="tu-api-key-aqui"
```

**En Render (Production):**
Ve a: Render Dashboard → Environment Variables
Agrega: `GEMINI_API_KEY` = tu-api-key

### Paso 4: Iniciar el Servidor

```bash
python server.py
```

El servidor mostrará:
```
================================================================================
   🚀 CarlosTech Math AI - Motor de Integrales v3.5 Pro
================================================================================
   📊 Motor: SymPy + Google Gemini
   🤖 IA Gemini: ✅ HABILITADA
   📝 Autenticación: Activada
   🔗 URL: http://localhost:10000
================================================================================
```

---

## 📖 CÓMO FUNCIONAN LOS PASOS CON IA

### Ejemplo 1: Integral Polinómica
**Input:** `x**2`

**Respuesta del servidor:**
```json
{
  "steps": [
    "✓ Expresión parseada: $x^{2}$",
    "📊 Método: Regla de potencia: ∫xⁿ dx = (xⁿ⁺¹)/(n+1) + C",
    "✓ Aplicando integración indefinida",
    "1. Identificamos que es una integral polinómica de grado 2",
    "2. La expresión a integrar es: $x^{2}$",
    "3. Aplicamos la regla de potencia: ∫xⁿ dx = xⁿ⁺¹/(n+1) + C",
    "4. Incrementamos el exponente: n+1 = 3",
    "5. Dividimos por el nuevo exponente: $\frac{x^{3}}{3}$",
    "6. Resultado final: $\frac{x^{3}}{3}$ + C"
  ],
  "result": "x^3/3",
  "gemini_used": true,
  "gemini_available": true
}
```

### Ejemplo 2: Integral Trigonométrica
**Input:** `sin(x)`

**Respuesta (con IA):**
```json
{
  "method_detected": "Función Trigonométrica - Seno",
  "steps": [
    "✓ Expresión parseada: $\sin(x)$",
    "🔢 Método: ∫sin(x) dx = -cos(x) + C",
    "1. Identificamos que es una integral de seno",
    "2. Aplicamos la regla fundamental: ∫sin(x) dx = -cos(x) + C",
    "3. La integral de seno es el negativo del coseno",
    "4. Resultado: -cos(x) + C"
  ],
  "result": "-cos(x)",
  "gemini_used": true
}
```

---

## 🔌 NUEVOS ENDPOINTS DE API

### 1. `/api/resolver` - RESOLVER INTEGRALES CON IA
```bash
curl -X POST http://localhost:10000/api/resolver \
  -H "Content-Type: application/json" \
  -d '{
    "integral": "x*sin(x)"
  }'
```

**Respuesta:**
```json
{
  "input": "x \\sin(x)",
  "method_detected": "Logarítmica (Integración por Partes)",
  "steps": [
    "✓ Expresión parseada",
    "📝 Método: Integración por partes",
    "1. Identificamos producto de x con trigonométrica",
    "2. Formula: ∫u dv = uv - ∫v du",
    ...
  ],
  "result": "- x \\cos(x) + \\sin(x)",
  "gemini_used": true,
  "gemini_available": true
}
```

### 2. `/api/info` - INFO DEL SERVIDOR
```bash
curl http://localhost:10000/api/info
```

**Respuesta:**
```json
{
  "nombre": "CarlosTech Math AI - Motor Profesional",
  "version": "3.5 Pro con IA",
  "motor": "SymPy + Google Gemini (IA Gratuita)",
  "gemini_disponible": true,
  "capacidades": [
    "✅ Polinómicas",
    "✅ Trigonométricas",
    "✅ Exponenciales",
    ...
  ]
}
```

### 3. `/api/graficar` - GENERAR GRÁFICOS
```bash
curl -X POST http://localhost:10000/api/graficar \
  -H "Content-Type: application/json" \
  -d '{
    "integral": "sin(x)",
    "a": 0,
    "b": 6.28
  }'
```

### 4. `/api/derivada` - CALCULAR DERIVADAS
```bash
curl -X POST http://localhost:10000/api/derivada \
  -H "Content-Type: application/json" \
  -d '{
    "expresion": "x**3 + 2*x"
  }'
```

---

## ⚙️ CARACTERÍSTICAS DEL MOTOR

### 6 Métodos de Resolución Automática:
1. **Integración Directa** - El método más rápido (90% de casos)
2. **Heurístico** - Para integrales complejas
3. **Integración por Partes** - Para productos
4. **Sustituciones Trigonométricas** - Para radicales
5. **Fracciones Parciales** - Para racionales
6. **Análisis con IA** - Explicación automática

### Tipos de Integrales Soportadas:
- ✅ Polinómicas (cualquier grado)
- ✅ Trigonométricas (sen, cos, tan)
- ✅ Exponenciales (e^x, a^x)
- ✅ Logarítmicas (ln(x), log(x))
- ✅ Radicales (√x, √(1-x²))
- ✅ Racionales (fracciones)
- ✅ Mixtas (todas las combinaciones)
- ✅ Definidas e Indefinidas

---

## 💰 COSTOS

### Google Gemini (Gratis):
- **$0)** - Completamente gratis
- 500 RPM (solicitudes por minuto)
- API Key simple de obtener
- Sin tarjeta de crédito requerida

### SymPy:
- **$0** - Open Source
- Licencia BSD

### Servidor (Render):
- **Gratis para hobby** - 0.50 recursos/hora
- **$10/mes profesional** - Hosting ilimitado

---

## 🚀 DEPLOYMENT EN RENDER

### Paso 1: Preparar archivo Procfile
```Procfile
web: python server.py
```

### Paso 2: Preparar archivo runtime.txt
```txt
python-3.11.7
```

### Paso 3: Push a GitHub
```bash
git add -A
git commit -m "🚀 Motor profesional con IA Gemini"
git push origin main
```

### Paso 4: En Render.com
1. Conecta tu repositorio de GitHub
2. Crea nuevo "Web Service"
3. En Environment Variables, agrega:
   ```
   GEMINI_API_KEY=tu-api-key-gratis
   SECRET_KEY=tu-secret-key
   ```
4. Deploy automáticamente

---

## 📊 COMPARATIVA

| Característica | CarlosTech v3.5 | Mathway | Wolfram Alpha |
|---|---|---|---|
| **Costo** | Gratis | $15/mes | $7.99/mes |
| **IA incluida** | ✅ Sí | ✅ Sí | ✅ Sí |
| **API REST** | ✅ Sí | ❌ No | ✅ Sí |
| **Open Source** | ✅ Sí | ❌ No | ❌ No |
| **Funciona offline** | ⚠️ Parcial | ❌ No | ❌ No |
| **Pasos detallados** | ✅ Sí | ✅ Sí | ✅ Sí |
| **Gráficos** | ✅ Sí | ✅ Sí | ✅ Sí |
| **Derivadas** | ✅ Sí | ✅ Sí | ✅ Sí |

---

## 🐛 TROUBLESHOOTING

### Error: "GEMINI_API_KEY not found"
**Solución:** Debes establecer la variable de entorno GEMINI_API_KEY

```powershell
# PowerShell
$env:GEMINI_API_KEY = "tu-key"
python server.py
```

### "Gemini IA: ⚠️ NO DISPONIBLE"
**Solución:** Google AI no está instalado. Ejecuta:
```bash
pip install google-generativeai
```

### API Key inválida
**Solución:** Obtén una nueva en: https://aistudio.google.com/app/apikey

### Rate limiting (demasiadas solicitudes)
**Solución:** El servidor automáticamente usa reglas matemáticas si se agota el límite de Gemini

---

## 📝 LICENCIA

MIT License - Libre para usar, modificar y distribuir

---

## 👨‍💻 AUTOR

CarlosTech Math AI - Engine v3.5 Pro
Marzo 2025

**Contáctame:** carlos@techmath.ai
