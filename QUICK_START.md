# 🚀 CarlosTech Math AI v3.5 - GUÍA RÁPIDA

## ⛔ IMPORTANTE: Configura Gemini API GRATIS (opcional)

### 1. Obtén tu API Key GRATIS de Google (30 segundos)
→ https://aistudio.google.com/app/apikey
→ Click "Create API Key"
→ Copia tu key

### 2. Setup la variable de entorno
```powershell
$env:GEMINI_API_KEY = "tu-api-key-sin-comillas"
```

### 3. ¡Listo! Inicia el servidor
```bash
python server.py
```

---

## 🎯 USAR EL MOTOR

### Login primero
- URL: http://localhost:10000/
- Usuario: `carlos` | Password: `carlos123`

### Ingresa integrales así:
- `x**2` (polinómica)
- `sin(x)` (trigonométrica)
- `exp(x)` (exponencial)
- `log(x)` (logarítmica)
- `sqrt(x)` (con raíz)
- `x*sin(x)` (integración por partes)

### ¡El motor:
✅ Detecta automáticamente el método
✅ Resuelve usando 6 estrategias
✅ Genera pasos con IA Gemini (si está disponible)
✅ Muestra gráficos interactivos
✅ Funciona aunque Gemini no esté disponible

---

## 📊 API REST

### Resolver integral
```bash
curl -X POST http://localhost:10000/api/resolver \
  -H "Content-Type: application/json" \
  -d '{"integral": "x**2"}'
```

### Obtener gráfico
```bash
curl -X POST http://localhost:10000/api/graficar \
  -H "Content-Type: application/json" \
  -d '{"integral": "sin(x)", "a": 0, "b": 6.28}'
```

### Derivada
```bash
curl -X POST http://localhost:10000/api/derivada \
  -H "Content-Type: application/json" \
  -d '{"expresion": "x**3"}'
```

---

## 🎨 Características

✨ **6 métodos automáticos** - Elige el mejor automáticamente
✨ **Pasos detallados** - Explicación paso a paso con IA
✨ **2 modos de operación**:
   - Con Gemini IA: 🤖 Explicaciones inteligentes
   - Sin Gemini: 📋 Reglas matemáticas (SIEMPRE funciona)

✨ **Gráficos interactivos** - Visualiza las funciones
✨ **Autenticación** - Usuario/contraseña seguro
✨ **REST API** - Integra en cualquier app

---

## 🔐 Usuarios por defecto

| Usuario | Contraseña |
|---------|-----------|
| carlos | carlos123 |
| admin | admin123 |
| demo | demo123 |

---

## 💡 Ejemplos de entrada

```
Polinómicas:
  x**2
  x**4 + 3*x**2 + 2
  (x+1)**3

Trigonométricas:
  sin(x)
  cos(x) + sin(x)
  x*sin(x)
  sin(x)**2

Exponenciales:
  exp(x)
  2*exp(x)
  x*exp(x)

Logarítmicas:
  log(x)
  x*log(x)
  1/x

Radicales:
  sqrt(x)
  1/sqrt(1-x**2)
  sqrt(x**2+1)

Definidas:
  Integral de 0 a 5 de x**2
  (ingresa en el campo "De" y "Hasta")
```

---

## 🌐 Desplegar en Render (Gratis)

1. Crea archivo `.env`:
   ```
   GEMINI_API_KEY=tu-key-gratis
   SECRET_KEY=algo-secreto
   ```

2. Push a GitHub:
   ```bash
   git push origin main
   ```

3. En Render.com:
   - New Web Service
   - Conecta tu repo
   - Environment → Agrega GEMINI_API_KEY
   - "Create Web Service"

¡Listo! Tu app en línea GRATIS ✅

---

## 📖 Documentación completa

Ver `AI_SETUP.md` para:
- Instalación detallada
- Configuración de Gemini
- API endpoints completa
- Troubleshooting
- Comparación con Mathway

---

## ✅ Status Actual

✨ **Server.py**: Completamente reescrito (v3.5 Pro)
✨ **IA Gemini**: Integrada y lista
✨ **Parser**: Mejorado con multiplicación implícita
✨ **Métodos**: 6 estrategias automáticas
✨ **API**: REST completa
✨ **Frontend**: Login + dashboard
✨ **Producción**: Pronto en Render
