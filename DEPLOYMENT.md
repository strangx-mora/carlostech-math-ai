# ✅ Checklist de Deployment - CarlosTech Math AI

## Pre-Deployment (Antes de Subir a Producción)

### Seguridad
- [ ] **Credenciales**
  - [ ] SECRET_KEY generada (32+ caracteres)
  - [ ] GEMINI_API_KEY configurada
  - [ ] Archivo `.env` NO está en git
  - [ ] `.gitignore` incluye `.env`

- [ ] **Código**
  - [ ] Sin credenciales hardcodeadas
  - [ ] Sin comentarios con información sensible
  - [ ] Validación de entrada implementada
  - [ ] Manejo de errores seguro

- [ ] **Dependencias**
  - [ ] requirements.txt actualizado
  - [ ] Todas las dependencias son necesarias
  - [ ] Versiones pinned (no usar *)

### Funcionalidad
- [ ] **Testing**
  - [ ] Integrales básicas funcionan
  - [ ] Gráficas se generan correctamente
  - [ ] Login/logout funciona
  - [ ] Errores se manejan correctamente

- [ ] **Performance**
  - [ ] Tiempo de respuesta < 2 segundos
  - [ ] Gráficas cargan rápido
  - [ ] Sin memory leaks
  - [ ] Manejo de expresiones complejas

### Documentación
- [ ] [ ] README.md actualizado
- [ ] [ ] SECURITY.md revisado
- [ ] [ ] IMPROVEMENTS.md completo
- [ ] [ ] Comentarios en código crítico

---

## Deployment en Render

### Paso 1: Preparar Repositorio
```bash
# Asegurar que .env NO está en git
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Add .env to gitignore"

# Verificar archivos
git status
```

### Paso 2: Configurar en Render
1. Ir a [render.com](https://render.com)
2. Crear nuevo "Web Service"
3. Conectar repositorio GitHub
4. Configurar:
   - **Name**: carlostech-math-ai
   - **Environment**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
   - **Plan**: Free (o Starter)

### Paso 3: Variables de Entorno
En Render Dashboard → Environment:
```
SECRET_KEY=<generar-con-openssl>
GEMINI_API_KEY=<tu-api-key>
FLASK_ENV=production
PORT=10000
```

### Paso 4: Deploy
```bash
git push origin main
# Render detecta cambios automáticamente
```

### Paso 5: Verificar
- [ ] App está online
- [ ] URL funciona
- [ ] Login funciona
- [ ] Integrales se resuelven
- [ ] Logs sin errores

---

## Deployment en Heroku (Alternativa)

### Paso 1: Instalar Heroku CLI
```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows
# Descargar desde https://devcenter.heroku.com/articles/heroku-cli
```

### Paso 2: Crear App
```bash
heroku login
heroku create carlostech-math-ai
```

### Paso 3: Configurar Variables
```bash
heroku config:set SECRET_KEY="$(openssl rand -hex 32)"
heroku config:set GEMINI_API_KEY="your-key"
heroku config:set FLASK_ENV="production"
```

### Paso 4: Deploy
```bash
git push heroku main
```

### Paso 5: Verificar
```bash
heroku logs --tail
heroku open
```

---

## Deployment en AWS (Escalable)

### Opción 1: Elastic Beanstalk
```bash
# Instalar EB CLI
pip install awsebcli

# Inicializar
eb init -p python-3.11 carlostech-math-ai

# Crear ambiente
eb create production

# Deploy
eb deploy
```

### Opción 2: EC2 + Nginx + Gunicorn
```bash
# En servidor EC2
sudo apt update
sudo apt install python3-pip nginx

# Clonar repo
git clone <repo-url>
cd integral_app

# Instalar dependencias
pip install -r requirements.txt
pip install gunicorn

# Crear servicio systemd
sudo nano /etc/systemd/system/carlostech.service
```

**Contenido de carlostech.service:**
```ini
[Unit]
Description=CarlosTech Math AI
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/integral_app
Environment="PATH=/home/ubuntu/integral_app/venv/bin"
ExecStart=/home/ubuntu/integral_app/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind 127.0.0.1:10000 \
    server:app

[Install]
WantedBy=multi-user.target
```

```bash
# Iniciar servicio
sudo systemctl start carlostech
sudo systemctl enable carlostech

# Configurar Nginx
sudo nano /etc/nginx/sites-available/carlostech
```

---

## Post-Deployment

### Verificaciones Inmediatas
- [ ] App está online y accesible
- [ ] Login funciona correctamente
- [ ] Integrales se resuelven
- [ ] Gráficas se generan
- [ ] Sin errores en logs
- [ ] Tiempo de respuesta aceptable

### Monitoreo
- [ ] Configurar alertas de errores
- [ ] Monitorear uso de CPU/memoria
- [ ] Revisar logs regularmente
- [ ] Hacer backup de datos

### Optimizaciones
- [ ] Habilitar caché
- [ ] Configurar CDN
- [ ] Optimizar imágenes
- [ ] Minificar CSS/JS

---

## Mantenimiento Continuo

### Diario
- [ ] Revisar logs de errores
- [ ] Verificar disponibilidad
- [ ] Monitorear performance

### Semanal
- [ ] Revisar estadísticas de uso
- [ ] Actualizar dependencias menores
- [ ] Hacer backup

### Mensual
- [ ] Revisar seguridad
- [ ] Actualizar dependencias mayores
- [ ] Optimizar performance
- [ ] Revisar costos

### Trimestral
- [ ] Auditoría de seguridad
- [ ] Revisión de código
- [ ] Planificación de mejoras
- [ ] Capacitación del equipo

---

## Troubleshooting

### App no inicia
```bash
# Ver logs
heroku logs --tail
# o
eb logs

# Verificar variables de entorno
heroku config
# o
eb config
```

### Errores de conexión
```bash
# Verificar puerto
netstat -tuln | grep 10000

# Verificar firewall
sudo ufw status
```

### Problemas de performance
```bash
# Monitorear recursos
top
# o
htop

# Revisar logs de errores
tail -f logs/error.log
```

### Credenciales no funcionan
```bash
# Verificar variables
echo $SECRET_KEY
echo $GEMINI_API_KEY

# Reconfigurar
heroku config:set SECRET_KEY="new-value"
```

---

## Rollback (Si algo falla)

### Render
```bash
# En Render Dashboard
# Ir a Deployments
# Seleccionar versión anterior
# Click "Redeploy"
```

### Heroku
```bash
# Ver historial
heroku releases

# Rollback a versión anterior
heroku rollback v123
```

### Git
```bash
# Revertir último commit
git revert HEAD
git push origin main

# O volver a versión específica
git checkout <commit-hash>
git push origin main --force
```

---

## Checklist Final

### Antes de Ir a Producción
- [ ] Código revisado
- [ ] Tests pasados
- [ ] Seguridad verificada
- [ ] Performance aceptable
- [ ] Documentación completa
- [ ] Credenciales configuradas
- [ ] Backups configurados
- [ ] Monitoreo activo

### Después de Ir a Producción
- [ ] Verificar acceso
- [ ] Probar funcionalidad
- [ ] Revisar logs
- [ ] Monitorear performance
- [ ] Comunicar a usuarios
- [ ] Documentar cambios

---

## Contacto de Emergencia

Si algo falla en producción:

1. **Verificar logs** - ¿Cuál es el error?
2. **Aislar problema** - ¿Qué componente falla?
3. **Hacer rollback** - Volver a versión anterior
4. **Investigar** - Encontrar causa raíz
5. **Fijar** - Implementar solución
6. **Redeploy** - Subir versión corregida
7. **Verificar** - Confirmar que funciona

---

**Versión**: 3.5 Pro
**Última actualización**: 2025
**Estado**: ✅ Listo para Producción
