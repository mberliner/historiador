# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere al [Versionado Semántico](https://semver.org/lang/es/).

## [0.11.1] - 2025-09-27

### 🎉 Added
- **Notas de release dinámicas**: Los releases en GitHub y GitLab ahora extraen automáticamente el contenido del CHANGELOG.md
- **Validación obligatoria de CHANGELOG**: Los workflows se detienen si falta documentación para el tag
- **Agentes especializados Claude Code**: qa-analyzer, coverage-analyzer, coverage-improver, security-analyzer
- **Configuración automatizada**: 50+ reglas de permisos optimizadas para desarrollo fluido
- **Sistema de changelog estructurado**: Formato estandarizado para releases automáticos

### 🗑️ Removed
- Eliminado parámetro `-b/--batch-size` por ser innecesario y confuso para usuarios
- Removidos archivos de PyInstaller spec obsoletos (historiador.spec, pyinstaller_optimized.spec)
- Limpieza de archivos de desarrollo obsoletos y documentación desactualizada

### 🔧 Changed
- **CI/CD optimizado**: Cambios en documentación (*.md) ya no disparan pipelines innecesariamente
- **Título de features**: Limitado a 120 caracteres máximo para mejor visualización en Jira
- **Mensaje de directorio vacío**: Cambiado de ERROR a WARNING para mejor experiencia de usuario
- **Releases automáticos**: Contenido dinámico extraído del CHANGELOG.md con validación previa
- Documentación README y CLAUDE.md actualizadas para reflejar parámetros actuales

### 🐛 Fixed
- **Contador de features**: Corrección en la visualización del progreso de features procesadas
- **Estructura GitLab CI**: Corregida sintaxis YAML del job release_job para releases funcionales
- **Formateo de código**: Aplicado Black e isort para consistencia en imports y formato
- Validación estricta de agente coverage-improver para preservar tests existentes

### ⚡ Performance
- **Cobertura de tests mejorada**: Alcanzado 83% de test coverage con validaciones estrictas
- **Ejecutable optimizado**: Mantenido en ~54MB con configuración limpia
- **Build simplificado**: Un solo archivo .spec activo para builds más eficientes
- Agentes de cobertura con respeto total a tests existentes

### 🔒 Security
- **Analizador de seguridad**: Configuración de reportes automáticos y agente especializado
- **Permisos de edición**: Optimizados para entorno Claude Code sin comprometer seguridad
- **Validación de agentes**: Sistema de checks para agentes de mejora de cobertura
- Configuración de agentes con validación estricta de cambios

### 📝 Detalles técnicos
- Implementación de workflows GitHub Actions y GitLab CI con validación de CHANGELOG
- Sistema de extracción automática de contenido entre tags usando comandos awk
- Configuración de 50+ reglas de permisos para herramientas de desarrollo
- Agentes especializados con validación estricta para preservar calidad del código

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