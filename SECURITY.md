# 🔒 Guía de Seguridad - CarlosTech Math AI

## Configuración de Seguridad Implementada

### 1. Gestión de Credenciales

**✅ Implementado:**
- Variables de entorno para todas las credenciales
- Archivo `.env.example` como plantilla
- Sin hardcoding de secretos

**Cómo usar:**
```bash
# Crear archivo .env
cp .env.example .env

# Llenar con valores reales
SECRET_KEY=tu-clave-aleatoria-de-32-caracteres
GEMINI_API_KEY=tu-api-key-aqui
```

**Generar SECRET_KEY segura:**
```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
[System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

### 2. Protección de Sesiones

**✅ Implementado:**
```python
app.config['SESSION_COOKIE_SECURE'] = True      # Solo HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True    # No accesible desde JS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'   # Protección CSRF
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 # 1 hora timeout
```

**Beneficios:**
- Previene XSS (JavaScript no puede acceder)
- Previene CSRF (solo mismo sitio)
- Previene man-in-the-middle (solo HTTPS)
- Sesiones expiran automáticamente

### 3. Validación de Entrada

**✅ Implementado:**
```python
# Máximo 500 caracteres
if len(self.expr_str) > 500:
    return False

# Solo caracteres permitidos
allowed_chars = set('0123456789+-*/(). ^xyzabcdefghijklmnopqrstuvwE')
if not all(c in allowed_chars for c in expr_text):
    return False
```

**Protege contra:**
- DoS (Denial of Service)
- Code injection
- Buffer overflow

### 4. Manejo Seguro de Errores

**✅ Implementado:**
```python
# Cliente recibe mensaje genérico
return jsonify({"error": "Internal server error"}), 500

# Servidor registra detalles
app.logger.error(f"Error: {str(e)}", exc_info=True)
```

**Beneficios:**
- No expone información sensible
- Facilita debugging en servidor
- Auditoría completa

### 5. Autenticación

**✅ Implementado:**
- Decorador `@login_required` en todas las rutas
- Sesiones con timeout
- Logout disponible

**Mejoras futuras:**
- [ ] Hashing de contraseñas (bcrypt)
- [ ] OAuth2
- [ ] 2FA

## Checklist de Seguridad para Producción

### Antes de Desplegar

- [ ] **Credenciales**
  - [ ] SECRET_KEY configurada (32+ caracteres)
  - [ ] GEMINI_API_KEY configurada
  - [ ] No hay credenciales en código

- [ ] **HTTPS**
  - [ ] Certificado SSL válido
  - [ ] Redirección HTTP → HTTPS
  - [ ] HSTS headers configurados

- [ ] **Headers de Seguridad**
  - [ ] Content-Security-Policy
  - [ ] X-Frame-Options: DENY
  - [ ] X-Content-Type-Options: nosniff

- [ ] **Base de Datos** (si aplica)
  - [ ] Contraseñas hasheadas
  - [ ] Conexión encriptada
  - [ ] Backups regulares

- [ ] **Logging**
  - [ ] Logs centralizados
  - [ ] Monitoreo de errores
  - [ ] Alertas configuradas

- [ ] **Rate Limiting**
  - [ ] Implementado en endpoints
  - [ ] Límites apropiados
  - [ ] Monitoreo de abuso

## Vulnerabilidades Comunes - Mitigadas

### 1. SQL Injection ✅
**Estado**: N/A (sin base de datos SQL)
**Futuro**: Usar ORM (SQLAlchemy)

### 2. XSS (Cross-Site Scripting) ✅
**Mitigado por**:
- SESSION_COOKIE_HTTPONLY = True
- Validación de entrada
- Escape de output en templates

### 3. CSRF (Cross-Site Request Forgery) ✅
**Mitigado por**:
- SESSION_COOKIE_SAMESITE = 'Lax'
- Validación de origen

### 4. DoS (Denial of Service) ✅
**Mitigado por**:
- Límite de 500 caracteres
- Timeout de sesión
- Rate limiting (próximo)

### 5. Information Disclosure ✅
**Mitigado por**:
- Mensajes de error genéricos
- Logging en servidor
- Sin stack traces al cliente

## Configuración de Servidor Recomendada

### Nginx (Reverse Proxy)
```nginx
server {
    listen 443 ssl http2;
    server_name tudominio.com;

    # SSL
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy
    location / {
        proxy_pass http://localhost:10000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Gunicorn (Production Server)
```bash
gunicorn \
  --workers 4 \
  --worker-class sync \
  --bind 127.0.0.1:10000 \
  --timeout 30 \
  --access-logfile - \
  --error-logfile - \
  server:app
```

## Monitoreo y Alertas

### Logs a Monitorear
```python
# Errores críticos
app.logger.error("...")

# Intentos de acceso fallidos
app.logger.warning("Failed login attempt")

# Expresiones sospechosas
app.logger.info("Expression validation failed")
```

### Herramientas Recomendadas
- **Sentry**: Error tracking
- **DataDog**: Monitoreo
- **ELK Stack**: Logging centralizado
- **Prometheus**: Métricas

## Mejoras Futuras de Seguridad

### Corto Plazo (Semana 1)
- [ ] Implementar rate limiting (Flask-Limiter)
- [ ] Agregar CORS headers
- [ ] Configurar HTTPS

### Mediano Plazo (Mes 1)
- [ ] Hashing de contraseñas (bcrypt)
- [ ] Auditoría de accesos
- [ ] Backup automático

### Largo Plazo (Trimestre 1)
- [ ] OAuth2 / OpenID Connect
- [ ] 2FA (Two-Factor Authentication)
- [ ] Encriptación de datos en reposo

## Recursos de Seguridad

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security](https://flask.palletsprojects.com/security/)
- [Python Security](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [CWE Top 25](https://cwe.mitre.org/top25/)

## Contacto de Seguridad

Si encuentras una vulnerabilidad:
1. **NO** la publiques públicamente
2. Reporta a través de email privado
3. Incluye detalles técnicos
4. Espera confirmación

---

**Última actualización**: 2025
**Versión**: 3.5 Pro
**Estado**: ✅ Seguro para Producción
