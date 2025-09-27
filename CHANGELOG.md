# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere al [Versionado Semántico](https://semver.org/lang/es/).

## [0.11.1] - 2025-09-27

### 🗑️ Removed
- Eliminado parámetro `-b/--batch-size` por ser innecesario y confuso para usuarios
- Removidos archivos de PyInstaller spec obsoletos (historiador.spec, pyinstaller_optimized.spec)

### 🔧 Changed
- Mensaje de directorio vacío cambiado de ERROR a WARNING para mejor UX
- Título de features limitado a 120 caracteres máximo
- Documentación README y CLAUDE.md actualizadas para reflejar parámetros actuales

### 🐛 Fixed
- Corrección en contador de features procesadas mostrado en pantalla
- Formateo Black aplicado a imports para consistencia de código

### ⚡ Performance
- Ejecutable optimizado mantenido en ~54MB con configuración limpia
- Un solo archivo .spec activo para builds más simples

### 🔒 Security
- Configuración de agentes de seguridad y reportes automáticos
- Permisos de edición optimizados para entorno Claude Code

## [0.10.0] - 2025-08-30

### 🎉 Added
- **Sistema de alias multiidioma** para tipos de issue (Story ↔ Historia, Bug ↔ Error, etc.)
- **Configuración automática desde Jira** para tipos de issue y campos
- Auto-detección de configuración óptima del proyecto
- Configuración dinámica de parámetros Jira

### 🔧 Changed
- Soporte para separadores de criterios por fin de línea además de punto y coma
- Mejoras en documentación para nuevas funcionalidades

### 🐛 Fixed
- Uso automático de alias para mayor compatibilidad entre configuraciones

## [0.9.2] - 2025-08-29

### 🐛 Fixed
- Correcciones para manejo de criterios de aceptación opcionales
- Validación mejorada cuando no se proporcionan criterios

## [0.9.1] - 2025-08-29

### 🐛 Fixed
- Arreglo de problema SSL en conexiones GitHub Actions
- Construcción condicional en Windows mejorada
- Tests para generación de archivos .env

## [0.9.0] - 2025-08-27

### 🎉 Added
- **Configuración interactiva automática** cuando no existe archivo .env
- Agente especializado para build con optimización
- Agente para mejora automática de cobertura de tests
- Soporte para numpy en ejecutable y mejoras en pandas

### 🔧 Changed
- Mejoras en linting y calidad de código
- Tests de feature manager expandidos para >87% cobertura
- Mejores excepciones cuando no hay configuración de entorno

---

## Guía de Contribución

### Formato de Commits
```
tipo(ámbito): descripción breve

Descripción más detallada del cambio si es necesario.

Fixes #123
```

### Tipos de Commit que generan changelog
- `feat`: Nueva funcionalidad (→ Added)
- `fix`: Corrección de bug (→ Fixed)
- `perf`: Mejora de rendimiento (→ Performance)
- `security`: Correcciones de seguridad (→ Security)
- `remove`: Eliminación de funcionalidad (→ Removed)
- `change`: Cambio en funcionalidad existente (→ Changed)

### Versionado
- **MAJOR** (x.0.0): Cambios incompatibles en API
- **MINOR** (0.x.0): Nueva funcionalidad compatible hacia atrás
- **PATCH** (0.0.x): Correcciones de bugs compatibles

### Generación de Changelog
```bash
# Obtener cambios desde último tag
git log --oneline v0.11.1..HEAD

# Crear nuevo tag
git tag v0.12.0
git push origin v0.12.0

# Actualizar este archivo con cambios correspondientes
```

### Comandos útiles para mantener changelog
```bash
# Ver todos los tags
git tag --sort=-version:refname

# Ver cambios entre tags
git log --oneline v0.10.0..v0.11.1

# Ver fecha y mensaje de un tag
git show v0.11.1 --format="%ci %s" --no-patch
```