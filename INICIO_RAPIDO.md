# GUÍA RÁPIDA - CarlosTech Math AI v4.0

## ¿Qué se arregló?

✅ Plotly CDN actualizado  
✅ Error de tiempo corregido  
✅ Motor de resolución completamente reescrito  
✅ Parser LaTeX mejorado  
✅ Multiplicación implícita funcionando  

## Inicio Rápido

### 1. Instalar dependencias
```bash
cd c:\Users\Luisc\Desktop\integral_app
pip install -r requirements.txt
```

### 2. Ejecutar servidor
```bash
python server.py
```

Deberías ver:
```
================================================================================
   CarlosTech Math AI v4.0 - Motor de Integrales
================================================================================
   Motor: SymPy
   URL: http://localhost:10000
================================================================================
```

### 3. Abrir en navegador
```
http://localhost:10000
```

### 4. Login
- Usuario: `carlos`
- Contraseña: `carlos123`

### 5. Probar
Escribe en el editor:
- `2x` → Resultado: `x²`
- `x**2` → Resultado: `x³/3`
- `sin(x)` → Resultado: `-cos(x)`

## Pruebas Automatizadas

### Test del Parser
```bash
python test_parser.py
```

### Test de Integración
```bash
python test_integration.py
```

### Test del Servidor
```bash
python test_server.py
```

## Archivos Importantes

| Archivo | Descripción |
|---------|-------------|
| `server.py` | Motor principal (v4.0) |
| `templates/index.html` | Interfaz web |
| `static/style.css` | Estilos |
| `requirements.txt` | Dependencias |
| `DIAGNOSTICO.md` | Explicación del problema |
| `RESUMEN_MEJORAS.md` | Cambios realizados |

## Integrales Soportadas

✅ Polinómicas: `x`, `2x`, `x**2`, `x**3`  
✅ Trigonométricas: `sin(x)`, `cos(x)`, `tan(x)`  
✅ Exponenciales: `exp(x)`, `2*exp(x)`  
✅ Logarítmicas: `1/x`, `log(x)`  
✅ Radicales: `sqrt(x)`, `sqrt(1-x**2)`  
✅ Mixtas: `x*sin(x)`, `2*x*exp(x)`  

## Formatos Aceptados

El parser acepta múltiples formatos:

| Formato | Ejemplo | Convertido |
|---------|---------|-----------|
| Potencia | `x^2` | `x**2` |
| Multiplicación | `2x` | `2*x` |
| Función | `sin(x)` | `sin(x)` |
| LaTeX | `\sin(x)` | `sin(x)` |
| Fracción | `\frac{1}{x}` | `(1)/(x)` |
| Raíz | `\sqrt{x}` | `sqrt(x)` |

## Solución de Problemas

### Error: "No autenticado"
- Asegúrate de hacer login primero
- Usuario: `carlos`, Contraseña: `carlos123`

### Error: "Expression empty"
- Escribe algo en el editor de MathQuill
- Haz clic en "Resolver Integral"

### Error: "Error en parsing"
- Verifica que la expresión sea válida
- Usa formatos soportados (ver tabla arriba)

### Gráfico no aparece
- Asegúrate de que Plotly se cargó (v2.26.0)
- Abre la consola del navegador (F12)
- Busca errores de Plotly

## Características

### Motor Matemático
- Resolución de integrales indefinidas y definidas
- Detección automática de métodos
- Pasos de resolución
- Gráficos interactivos

### Interfaz
- Editor de ecuaciones (MathQuill)
- Teclado de atajos
- Tema oscuro moderno
- Responsive design

### API REST
- `/api/resolver` - Resolver integrales
- `/api/graficar` - Generar gráficos
- `/api/derivada` - Calcular derivadas
- `/api/info` - Información del motor

## Ejemplos de Uso

### Desde Navegador
1. Escribe: `2x`
2. Haz clic: "Resolver Integral"
3. Resultado: `x²`

### Desde Terminal (cURL)
```bash
curl -X POST http://localhost:10000/api/resolver \
  -H "Content-Type: application/json" \
  -d '{"integral": "2x"}'
```

### Desde Python
```python
import requests

response = requests.post('http://localhost:10000/api/resolver',
    json={'integral': '2x'}
)

print(response.json())
```

## Rendimiento

| Integral | Tiempo |
|----------|--------|
| x | 0.022s |
| 2x | 0.002s |
| x² | 0.033s |
| sin(x) | 0.006s |
| exp(x) | 0.015s |

## Próximas Mejoras

1. Agregar más métodos de integración
2. Implementar IA para explicaciones
3. Agregar base de datos
4. Implementar rate limiting
5. Agregar soporte para integrales múltiples

## Soporte

Si tienes problemas:

1. Revisa `DIAGNOSTICO.md` para entender qué se arregló
2. Revisa `RESUMEN_MEJORAS.md` para ver los cambios
3. Ejecuta los tests: `python test_server.py`
4. Abre la consola del navegador (F12) para ver errores

## Estado

✅ **FUNCIONANDO CORRECTAMENTE**

Todos los tests pasan. El motor resuelve integrales sin problemas.

---

**Versión**: 4.0  
**Última actualización**: 2025  
**Estado**: Producción
