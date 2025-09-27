# Proyecto Historiador - Contexto para Claude

## Descripción del Proyecto
Aplicación de línea de comandos que importa historias de usuario desde archivos CSV/Excel hacia Jira, con soporte para subtareas automáticas y vinculación con Epics.

## Comandos Importantes
```bash
# Ejecutar aplicación (preferido) para todos los archivos de entrada
python src/main.py

# Ejecutar aplicación (procesamiento automático para un proyecto especifico)
python src/main.py -p PROJECT_KEY

# Procesar archivo específico
python src/main.py process -f entrada/archivo.csv -p PROJECT_KEY

# Validar archivo sin crear issues
python src/main.py validate -f entrada/archivo.csv

# Validar archivo mostrando solo 3 filas de preview
python src/main.py validate -f entrada/archivo.csv -r 3

# Diagnosticar campos obligatorios para features que existan en Jira
python src/main.py diagnose -p PROJECT_KEY

# Modo dry-run para pruebas, no modifica en Jira
python src/main.py -p PROJECT_KEY --dry-run

# Control de logging detallado (DEBUG, INFO, WARNING, ERROR)
python src/main.py --log-level DEBUG -p PROJECT_KEY --dry-run

# Procesar archivo específico con logging detallado
python src/main.py process -f entrada/archivo.csv -p PROJECT_KEY --log-level INFO

# Generar ejecutable optimizado (RECOMENDADO: ~51MB)
pyinstaller historiador-clean.spec --clean

# Generar ejecutable con comando directo (alternativa: ~53MB)
pyinstaller --onefile --name historiador \
  --exclude-module pytest --exclude-module pylint --exclude-module black \
  --exclude-module coverage --exclude-module isort --exclude-module responses \
  --exclude-module freezegun --exclude-module faker \
  --add-data=".env.example:." src/main.py --clean

# Generar ejecutable completo (incluye herramientas dev - más pesado: ~83MB)
python -m PyInstaller --onefile --name historiador --add-data=".env.example:." src/main.py --clean
```

## Configuración Específica del Proyecto
- **Tipo de subtarea**: "Subtarea" (no "Sub-task" como es común en otros proyectos)
- **Tipo de feature**: "Feature" (configurable via FEATURE_ISSUE_TYPE)
- **Campo personalizado criterios**: Usar variable ACCEPTANCE_CRITERIA_FIELD en .env (opcional)
- **Separadores de subtareas**: `;` y salto de línea (`\n`)
- **Separadores de criterios**: `;` y salto de línea (`\n`)
- **Rollback opcional**: ROLLBACK_ON_SUBTASK_FAILURE=true elimina historia si fallan todas las subtareas
- **Gestión de parents**: Detección automática entre keys existentes y descripciones de features

## Orden de Columnas en Archivos de Entrada
1. `titulo` (requerida)
2. `descripcion` (requerida)
3. `subtareas` (opcional) - separadas por `;` o salto de línea (`\n`)
4. `criterio_aceptacion` (opcional) - criterios separados por `;` o salto de línea (`\n`)
5. `parent` (opcional) - Key existente (PROJ-123) o descripción para crear feature

## Arquitectura del Código
El proyecto implementa **Clean Architecture** con separación en 4 capas:

### Capa de Presentación (`src/presentation/`)
- **cli/commands.py**: Comandos CLI extraídos usando Click
- **formatters/output_formatter.py**: Formateo de salida y reportes
- **main.py**: Punto de entrada minimalista (45 líneas)

### Capa de Aplicación (`src/application/`)
- **use_cases/**: Casos de uso de negocio (process_files, validate_file, etc.)
- **interfaces/**: Protocolos y abstracciones para infraestructura

### Capa de Dominio (`src/domain/`)
- **entities/**: Modelos de datos puros (UserStory, ProcessResult, etc.)
- **repositories/**: Interfaces de repositorios

### Capa de Infraestructura (`src/infrastructure/`)
- **jira/**: Implementaciones para API de Jira (jira_client, feature_manager, utils)
- **file_system/**: Procesamiento de archivos CSV/Excel
- **settings.py**: Configuración con variables de entorno

## Funcionalidades Implementadas
- ✅ Procesamiento automático de archivos en directorio de entrada
- ✅ Creación de subtareas con validación avanzada
- ✅ Rollback opcional de historias si fallan todas las subtareas
- ✅ Validación de tipos de issue en Jira antes del procesamiento
- ✅ Reporte detallado de subtareas creadas/fallidas
- ✅ Movimiento automático de archivos procesados
- ✅ Creación automática de features cuando el campo parent contiene descripción
- ✅ Detección inteligente entre keys existentes y descripciones de features
- ✅ Búsqueda de features existentes para evitar duplicados
- ✅ Normalización de descripciones para comparación consistente
- ✅ Refactorización Fase 1: Arquitectura limpia (Score PyLint: 7.92 → 8.64)
- ✅ Configuración interactiva: Si no existe `.env`, solicita valores al usuario paso a paso
- ✅ **Manejo inteligente de alias de tipos de issue**: Auto-corrección Story ↔ Historia
- ✅ **Validación consistente**: `diagnose` y `process` usan misma lógica de alias

## Validaciones Implementadas
- Existencia del tipo "Subtarea" en el proyecto Jira
- Existencia del tipo "Feature" en el proyecto Jira (para creación automática)
- Subtareas inválidas (vacías o >255 caracteres)
- Conexión con Jira y permisos
- Validación de proyecto y issues padre
- Búsqueda de features existentes antes de crear duplicados
- Formato de archivos CSV/Excel

## Manejo de Errores
- Tracking detallado de subtareas creadas/fallidas por historia
- Logging específico para errores HTTP vs otros errores
- Reporte visual con ✓/✗ para subtareas
- Los archivos solo se mueven a 'procesados' si hay al menos una historia exitosa

## Variables de Entorno Importantes
```env
JIRA_URL=https://company.atlassian.net
JIRA_EMAIL=email@company.com
JIRA_API_TOKEN=token
PROJECT_KEY=PROJ
SUBTASK_ISSUE_TYPE=Subtarea
FEATURE_ISSUE_TYPE=Feature
ROLLBACK_ON_SUBTASK_FAILURE=false
ACCEPTANCE_CRITERIA_FIELD=customfield_10001
```

## Sistema de Logging
### Niveles Disponibles
- **DEBUG**: Información técnica detallada, llamadas a API, debugging
- **INFO**: Progreso normal, operaciones exitosas (default)
- **WARNING**: Situaciones recuperables, alertas
- **ERROR**: Errores críticos, fallos de conexión

### Configuración de Logs
- **Archivo**: Los logs técnicos se escriben en `logs/jira_batch.log`
- **Consola**: Solo salida user-friendly via OutputFormatter
- **Rotación**: Manual (archivo se sobrescribe en cada ejecución)

### Ejemplos de Uso
```bash
# Debugging completo para desarrollo
python src/main.py --log-level DEBUG diagnose -p PROJECT_KEY

# Información normal para producción
python src/main.py --log-level INFO process -f archivo.csv -p PROJ

# Solo errores críticos
python src/main.py --log-level ERROR --dry-run
```

## Configuración Interactiva
Si no existe archivo `.env`, la aplicación ofrece configuración interactiva:

### Ejemplo de Uso
```bash
./historiador test-connection
```

**Salida cuando no hay .env:**
```
[ERROR] Configuracion faltante.
¿Desea configurar los valores manualmente ahora? [y/N]: y

=== Configuración Interactiva ===
URL de Jira (ej: https://company.atlassian.net): https://mycompany.atlassian.net
Email del usuario de Jira: myemail@company.com
API Token de Jira: [OCULTO]
Clave del proyecto en Jira (ej: PROJ): MYPROJ
ID del campo de criterios (ej: customfield_10001) (opcional): customfield_10147

✓ Archivo .env creado exitosamente
Reiniciando configuración...
Probando conexión con Jira...
[OK] Conexión exitosa
[OK] Proyecto MYPROJ encontrado
```

### Características
- **API Token oculto**: Se solicita con `hide_input=True` por seguridad
- **Campo opcional**: `acceptance_criteria_field` puede dejarse vacío
- **Archivo .env automático**: Se genera con valores predeterminados para otros campos
- **Validación inmediata**: Recarga configuración y verifica conexión
- **Manejo de errores**: Si la configuración falla, muestra error descriptivo

## Problemas Conocidos y Soluciones
- **Error 404 en /project/{key}/issuetype**: Usar endpoint `/issue/createmeta` con expand
- **Error 403 al eliminar issues**: Común en entornos corporativos, rollback se desactiva automáticamente
- **Tipos de subtarea varían**: Verificar nombres exactos con el comando `validate`
- **Error 400 "Campo X es obligatorio" al crear features**: Usar comando `diagnose` para detectar campos obligatorios automáticamente
- **❌ SOLUCIONADO: "Story" no válido en diagnose**: Sistema detecta automáticamente alias (Story ↔ Historia)

## Manejo Inteligente de Alias de Tipos de Issue

### Funcionalidad Implementada
El sistema ahora maneja automáticamente alias comunes entre nombres de tipos de issue en diferentes idiomas:

#### Mapeo de Alias Soportado
```python
'story' ↔ ['historia', 'historia de usuario', 'user story']
'bug' ↔ ['error', 'defecto', 'incident'] 
'task' ↔ ['tarea', 'trabajo']
'subtask' ↔ ['subtarea', 'sub-task']
'epic' ↔ ['epopeya']
'feature' ↔ ['funcionalidad', 'característica']
```

#### Comportamiento Automático
- **Auto-detección**: Si especificas `DEFAULT_ISSUE_TYPE=Story` pero Jira usa "Historia"
- **Auto-corrección**: El sistema actualiza la configuración automáticamente  
- **Logs informativos**: Muestra qué alias se encontró y aplicó
- **Experiencia consistente**: Tanto `diagnose` como `process` usan la misma lógica

#### Ejemplo de Funcionamiento
```bash
# Configuración inicial
DEFAULT_ISSUE_TYPE=Story

# Al ejecutar diagnose
./historiador diagnose -p AGCF
# ✅ Detecta automáticamente que "Story" → "Historia" 
# ✅ Actualiza configuración interna
# ✅ Funciona sin errores para el usuario
```

#### Logs de Auto-corrección
```
INFO:src.infrastructure.jira.jira_client:✅ Tipo de issue encontrado por alias: 'Story' -> 'Historia' (id: 10004)
INFO:src.infrastructure.jira.jira_client:🔄 Actualizando configuración: Story -> Historia
```

## Calidad de Código - PyLint
Se aplican las siguientes consideraciones para mantener alta calidad:

### Problemas Resueltos
- **R0801 (código duplicado)**: Creación de `infrastructure/jira/utils.py` con utilidades compartidas
- **C0413 (import después de código)**: Imports dinámicos necesarios por `sys.path.append`
- **C0301 (línea muy larga)**: División de líneas largas con continuación
- **W0291 (trailing whitespace)**: Eliminación de espacios al final de líneas

### Configuraciones Especiales
- **Imports dinámicos**: Se mantienen después de `sys.path.append` para evitar errores de ruta
- **Límite de líneas**: 100 caracteres con flexibilidad para URLs y strings largos
- **Métodos con muchos argumentos**: Justificados por APIs externas (Jira)

### Comandos de Verificación
```bash
# Ejecutar PyLint completo
pylint src/

# Verificar archivo específico
pylint src/main.py

# Ver solo errores críticos
pylint --errors-only src/
```

## CI/CD Configuration
El proyecto cuenta con pipelines automatizados que garantizan calidad en cada commit:

### GitHub Actions (Primary)
- **Archivo**: `.github/workflows/ci.yaml`
- **Triggers**: Push y Pull Requests a master
- **Matrix testing**: Python 3.8 y 3.11 en paralelo
- **Quality gates**: 
  - PyLint score ≥ 8.0 (obligatorio)
  - Test coverage ≥ 80% (obligatorio)
  - All unit tests pass (obligatorio)
  - Executable builds successfully (obligatorio)

### GitLab CI (Mirror)
- **Archivo**: `.gitlab-ci.yml`
- **Configuración equivalente** para validación secundaria
- **Mismo quality gates** que GitHub Actions

### Pipeline Commands (Simular CI localmente)
```bash
# Comandos exactos del CI para debug local
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Quality checks (deben pasar)
pylint src/ --fail-under=8.0 --output-format=text
pytest tests/unit/ --cov=src --cov-report=xml --cov-fail-under=80

# Build validation (genera ejecutable optimizado 51MB)
pyinstaller historiador-clean.spec --clean
./dist/historiador --help
```

### Branch Protection Activa
- ❌ **No direct pushes** to master (bloqueado)
- ✅ **Pull Request required** (obligatorio)
- ✅ **CI must pass** before merge (obligatorio)
- ✅ **1 review required** (obligatorio)

## Testing Strategy
### Framework y Configuración
- **Test framework**: pytest + coverage + mocks
- **Test organization**: tests/unit/ organized by Clean Architecture layers
- **Coverage tool**: pytest-cov with XML output
- **Mock strategy**: Jira API responses via fixtures in tests/fixtures/

### Test Structure
```
tests/unit/
├── application/     # Use cases tests
├── domain/         # Entity tests  
├── infrastructure/ # Jira client, file processor tests
└── presentation/   # CLI commands tests
```

### Test Commands for Development
```bash
# Run all unit tests
pytest tests/unit/

# Run by layer
pytest tests/unit/domain/
pytest tests/unit/application/
pytest tests/unit/infrastructure/
pytest tests/unit/presentation/

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=term-missing

# Debug specific test
pytest tests/unit/domain/test_user_story.py::test_validate_title -v -s
```

## Development Workflow
### Required Process (Branch Protection)
```bash
# ❌ BLOCKED - Direct push to master
git push origin master

# ✅ REQUIRED - Feature branch workflow
git checkout -b feature/improvement
git push origin feature/improvement
# 1. Create Pull Request in GitHub
# 2. CI pipeline runs automatically
# 3. All quality gates must pass
# 4. Get 1 review approval
# 5. Merge button enabled
```

### Quality Gates Process
```bash
# These must ALL pass for merge:
1. ✅ PyLint score ≥ 8.0
2. ✅ Test coverage ≥ 80%  
3. ✅ All unit tests pass
4. ✅ Executable builds and runs (51MB optimized)
5. ✅ 1 code review approval
```

## Coverage Configuration
### Current Settings
- **Threshold**: 80% minimum (enforced in CI)
- **Tool**: pytest-cov with XML output for CI integration
- **Exclusions**: tests/, main.py (entry point)
- **Reports**: 
  - Terminal: `--cov-report=term-missing`
  - HTML: `--cov-report=html` (generates htmlcov/)
  - XML: `--cov-report=xml` (for CI tools)

### Coverage Commands
```bash
# Check coverage locally
pytest tests/unit/ --cov=src --cov-report=term-missing --cov-fail-under=80

# Generate HTML report for detailed analysis
pytest tests/unit/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser

# CI command (exact)
pytest tests/unit/ --cov=src --cov-report=xml --cov-fail-under=80
```

## Estructura de Directorios
```
historiador/
├── entrada/                           # Archivos CSV/Excel a procesar
├── procesados/                        # Archivos ya procesados exitosamente
├── logs/                             # Logs de ejecución (jira_batch.log)
├── src/
│   ├── presentation/                 # Capa de presentación
│   │   ├── cli/                      # Comandos CLI
│   │   │   └── commands.py
│   │   └── formatters/               # Formateo de salida
│   │       └── output_formatter.py
│   ├── application/                  # Capa de aplicación
│   │   ├── interfaces/               # Abstracciones
│   │   │   ├── feature_manager.py
│   │   │   ├── file_repository.py
│   │   │   └── jira_repository.py
│   │   └── use_cases/                # Casos de uso
│   │       ├── diagnose_features.py
│   │       ├── process_files.py
│   │       ├── test_connection.py
│   │       └── validate_file.py
│   ├── domain/                       # Capa de dominio
│   │   ├── entities/                 # Entidades puras
│   │   │   ├── batch_result.py
│   │   │   ├── feature_result.py
│   │   │   ├── process_result.py
│   │   │   └── user_story.py
│   │   └── repositories/             # Interfaces de repositorios
│   ├── infrastructure/               # Capa de infraestructura
│   │   ├── file_system/              # Sistema de archivos
│   │   │   └── file_processor.py
│   │   ├── jira/                     # API de Jira
│   │   │   ├── feature_manager.py
│   │   │   ├── jira_client.py
│   │   │   └── utils.py
│   │   └── settings.py               # Configuración
│   └── main.py                       # Punto de entrada (45 líneas)
└── dist/                             # Ejecutable generado con PyInstaller
```

## Comandos de Desarrollo Simplificados

Comandos agrupados por funcionalidad para tareas de desarrollo comunes:

### qa-simple
**Propósito**: Verificación completa de calidad (PyLint + Tests + Cobertura)
```bash
pylint src/ --fail-under=8.0 && pytest tests/unit/ --cov=src --cov-fail-under=80 --cov-report=term-missing
```

### build-simple  
**Propósito**: Build optimizado + validación del ejecutable
```bash
rm -rf build/ dist/ && pyinstaller historiador-clean.spec --clean && dist/historiador --help && dist/historiador test-connection
```

### coverage-simple
**Propósito**: Reporte detallado de cobertura HTML
```bash
pytest tests/unit/ --cov=src --cov-report=html --cov-report=term-missing
```

### lint-simple
**Propósito**: Análisis PyLint detallado sin threshold
```bash
pylint src/ --output-format=text
```

### test-simple
**Propósito**: Ejecutar tests con salida verbose
```bash
pytest tests/unit/ -v
```

### test-validation-simple
**Propósito**: Validación completa pre-agente (OBLIGATORIO antes de coverage-improver)
```bash
pytest tests/unit/ -v --tb=short && echo "✅ SAFE TO USE coverage-improver" || echo "❌ FIX TESTS BEFORE coverage-improver"
```

### ci-simple
**Propósito**: Simulación completa del pipeline de CI/CD
```bash
pylint src/ --fail-under=8.0 --output-format=text && pytest tests/unit/ --cov=src --cov-report=xml --cov-fail-under=80
```

## Uso de Comandos

Para usar cualquier comando, simplemente escribir su nombre:

```bash
# Ejemplos de uso
qa-simple
build-simple
coverage-simple
lint-simple
test-simple
ci-simple
```

Cada comando es autónomo y ejecuta una tarea específica. Para workflows más complejos, combinar comandos según necesidad.

## Claude Code - Configuración Avanzada

### Agentes Disponibles
El proyecto incluye agentes especializados configurados para ejecutarse sin confirmaciones:
- **qa-analyzer**: Análisis QA completo con validaciones estrictas
- **coverage-analyzer**: Análisis detallado de cobertura de tests
- **coverage-improver**: Mejora automática de cobertura de tests
- **code-reviewer**: Revisión de código y mejores prácticas
- **security-analyzer**: Análisis de seguridad y vulnerabilidades

### Uso de Agentes
```bash
# Ejecutar análisis QA completo (recomendado antes de commits)
qa-analyzer

# Analizar cobertura de tests específicamente
coverage-analyzer

# Mejorar cobertura automáticamente (CON VALIDACIÓN ESTRICTA)
coverage-improver 85  # Solo si todos los tests actuales pasan

# Revisar código para mejores prácticas
code-reviewer
```

### REGLAS CRÍTICAS PARA AGENTES

#### coverage-improver - VALIDACIÓN OBLIGATORIA
- **ANTES DE USAR**: Verificar que todos los tests pasan (`pytest tests/unit/ -q`)
- **DURANTE**: Validación automática después de cada test agregado
- **TOLERANCIA**: CERO tests rotos - cualquier falla es crítica
- **PROCESO**: Stop inmediato si algún test falla, reparar antes de continuar

### Configuración de Permisos
La configuración en `.claude/settings.json` permite ejecución automática de comandos sin confirmación:
- ✅ **50 reglas optimizadas** (vs 120+ anteriores)
- ✅ **Wildcards extensos** para máxima cobertura
- ✅ **Validaciones estrictas** en agentes

### Troubleshooting
```bash
# Diagnosticar problemas de configuración
/doctor

# Ver documentación completa
cat .claude/CLAUDE_CODE_SETUP.md
```

**Ver documentación completa**: [`.claude/CLAUDE_CODE_SETUP.md`](.claude/CLAUDE_CODE_SETUP.md)

## Gestión de Changelog

El proyecto mantiene un changelog detallado siguiendo las mejores prácticas de [Keep a Changelog](https://keepachangelog.com/).

### Estructura del Changelog
- **Formato**: Markdown estándar con categorías claras
- **Orden**: Cronológico descendente (más reciente primero)
- **Fuente**: Datos reales extraídos de tags y commits de git
- **Ubicación**: `/CHANGELOG.md`

### Categorías de Cambios
- 🎉 **Added**: Nuevas funcionalidades
- 🔧 **Changed**: Cambios en funcionalidad existente
- 🐛 **Fixed**: Correcciones de bugs
- 🗑️ **Removed**: Funcionalidades eliminadas
- 🔒 **Security**: Correcciones de seguridad
- ⚡ **Performance**: Mejoras de rendimiento

### Criterios de Inclusión
**✅ Incluir**: Cambios visibles al usuario, nuevas funcionalidades, correcciones importantes, cambios en configuración
**❌ No incluir**: Refactoring interno, cambios en tests, documentación menor, configuración CI/CD

### Comandos para Mantener Changelog
```bash
# Ver historial de tags por versión
git tag --sort=-version:refname

# Ver cambios entre dos versiones
git log --oneline v0.10.0..v0.11.1

# Ver información de un tag específico
git show v0.11.1 --format="%ci %s" --no-patch

# Ver cambios desde último tag liberado
git log --oneline v0.11.1..HEAD
```

### Proceso de Release
1. **Preparar cambios**: Implementar y testear funcionalidades
2. **Actualizar changelog**: Agregar nueva sección con cambios
3. **Crear tag**: `git tag v0.12.0 && git push origin v0.12.0`
4. **Verificar**: Confirmar que el changelog refleja correctamente los cambios

### Versionado Semántico
- **MAJOR** (x.0.0): Cambios incompatibles en API
- **MINOR** (0.x.0): Nueva funcionalidad compatible hacia atrás
- **PATCH** (0.0.x): Correcciones de bugs compatibles

### Ejemplo de Entrada
```markdown
## [0.12.0] - 2025-10-01

### 🎉 Added
- Nueva funcionalidad de exportación a múltiples formatos
- Soporte para templates personalizados

### 🐛 Fixed
- Corrección en validación de campos especiales
```
