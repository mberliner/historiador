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

# Diagnosticar campos obligatorios para features que existan en Jira
python src/main.py diagnose -p PROJECT_KEY

# Modo dry-run para pruebas, no modifica en Jira
python src/main.py -p PROJECT_KEY --dry-run

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

## Agentes Personalizados

Los siguientes "agentes" están definidos como secuencias de comandos especializadas que Claude debe ejecutar cuando el usuario las solicite:

### qa-agent
**Comando**: `qa-agent`
**Propósito**: Agente de calidad completa para validación de código Python

**Secuencia de ejecución**:
1. Ejecutar `pylint src/ --fail-under=8.0` (validación de calidad)
2. Ejecutar `pytest tests/unit/ --cov=src --cov-fail-under=80` (tests con cobertura)
3. Si hay errores de pylint, mostrar y sugerir correcciones
4. Si hay tests fallando, analizar y sugerir correcciones
5. Verificar que PyInstaller puede generar ejecutable
6. Re-ejecutar hasta que todos los checks pasen
7. Generar reporte final con estadísticas de cobertura y calidad

**Criterios de éxito**: 
- PyLint score ≥8.0
- Cobertura de tests ≥80%
- **CRÍTICO**: Todos los tests pasan al 100%
- Ejecutable generado correctamente

**⚠️ REGLA DE CALIDAD**: El qa-agent debe FALLAR si hay tests fallidos. No es aceptable aprobar calidad con tests rotos.

### build-agent
**Comando**: `build-agent`
**Propósito**: Agente de construcción y validación de ejecutable optimizado

**Secuencia de ejecución**:
1. Ejecutar `qa-agent` primero (prerequisito)
2. Limpiar build anterior: `rm -rf build/ dist/`
3. Generar ejecutable optimizado: `pyinstaller historiador-clean.spec --clean` (52MB optimizado)
4. Verificar que el ejecutable se crea en `dist/historiador`
5. Probar comando básico: `./dist/historiador --help`
6. Ejecutar test de conexión: `./dist/historiador test-connection`
7. Probar modo dry-run: `./dist/historiador --dry-run` (procesamiento automático sin modificar Jira)
8. Validar comando validate: `./dist/historiador validate --help` (sin archivos test)
9. Generar reporte de build con tamaño del ejecutable

**Criterios de éxito**:
- qa-agent pasa completamente (incluyendo todos los tests)
- Ejecutable optimizado generado sin errores (~52MB vs 83MB estándar)
- Comandos básicos funcionan correctamente
- Tests de funcionalidad básica pasan

### release-agent [VERSION]
**Comando**: `release-agent v1.2.3`
**Propósito**: Agente de preparación completa de release

**Secuencia de ejecución**:
1. Ejecutar `build-agent` (incluye qa-agent)
2. Verificar que la rama actual esté limpia (git status)
3. Actualizar versión en archivos relevantes si existen
4. Ejecutar suite completa de tests de aplicación:
   - `python src/main.py test-connection`
   - `python src/main.py validate -f entrada/test_*.csv`
   - `python src/main.py diagnose -p TEST`
5. Crear tag git: `git tag -a {VERSION} -m "Release {VERSION}"`
6. Generar o actualizar CHANGELOG con cambios desde último tag
7. Crear commit de release si hay cambios de versión
8. Mostrar resumen final para revisión antes de push

**Criterios de éxito**:
- build-agent pasa completamente
- Todos los comandos de aplicación funcionan
- Tag git creado correctamente
- CHANGELOG actualizado

### coverage-agent [THRESHOLD]
**Comando**: `coverage-agent 80`
**Propósito**: Agente especializado en análisis de cobertura de tests

**Secuencia de ejecución**:
1. Ejecutar tests con cobertura detallada: `pytest tests/unit/ --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing`
2. Generar reporte HTML en `htmlcov/index.html`
3. Analizar archivos con cobertura insuficiente (excluye main.py)
4. Identificar funciones/métodos sin tests en lógica de negocio
5. Sugerir tests específicos para áreas no cubiertas
6. Si el threshold no se alcanza, crear TODOs específicos
7. Generar reporte detallado con métricas por capa de Clean Architecture

**Nota sobre exclusiones**:
- `src/main.py` se excluye porque es punto de entrada (45 líneas)
- Los tests (`tests/`) se excluyen porque son código de testing
- Se mide cobertura de lógica de negocio en capas: application, domain, infrastructure, presentation

**Criterios de éxito**:
- Cobertura total ≥ threshold especificado (default: 80%)
- Reporte HTML generado
- Identificación clara de gaps de testing

### fix-agent [TIPO]
**Comando**: `fix-agent lint` o `fix-agent tests` o `fix-agent all`
**Propósito**: Agente de reparación automática de problemas comunes

**Secuencia de ejecución**:
Para `lint`:
1. Ejecutar `pylint src/` y capturar errores
2. Analizar warnings y errores comunes de Python
3. Corregir problemas automáticamente (imports no usados, líneas largas, etc.)
4. Re-ejecutar hasta alcanzar score ≥8.0

Para `tests`:
1. Ejecutar `pytest tests/unit/` y capturar fallos
2. Analizar errores de importación y runtime
3. Sugerir correcciones específicas para cada fallo
4. Aplicar fixes automáticos para problemas comunes
5. **CRÍTICO**: Si existen test fallidos corregir, no es aceptable un test fallando

Para `all`:
1. Ejecutar ambos secuencialmente
2. Asegurar que todas las correcciones son compatibles
3. Validar que el código sigue funcionando correctamente

**Criterios de éxito**:
- Sin errores críticos de pylint
- **OBLIGATORIO**: Tests ejecutables y passing al 100%
- Código funcionalmente equivalente

**REGLA CRÍTICA DE CALIDAD**:
❌ **INACEPTABLE**: Cualquier test fallando en el repositorio
✅ **OBLIGATORIO**: Todos los tests deben pasar antes de cualquier commit o release
⚠️ **IMPORTANTE**: Los tests fallidos indican regresiones o cambios no compatibles que deben corregirse inmediatamente

### fix-coverage-agent [THRESHOLD]
**Comando**: `fix-coverage-agent 80`
**Propósito**: Agente iterativo que mejora la cobertura de tests hasta alcanzar el umbral especificado

**Secuencia de ejecución**:
1. Ejecutar tests con cobertura actual: `pytest tests/unit/ --cov=src --cov-report=html --cov-report=term-missing`
2. Analizar reporte de cobertura e identificar archivos con cobertura insuficiente
3. **Iteración principal** (repetir hasta alcanzar threshold):
   a. Identificar el archivo con menor cobertura en lógica de negocio crítica
   b. Analizar funciones/métodos sin tests usando reporte HTML
   c. Priorizar casos más razonables y necesarios:
      - Funciones públicas principales (entry points)
      - Lógica de validación y transformación de datos
      - Manejo de errores y casos edge críticos
      - Algoritmos de negocio principales
   d. Generar tests específicos para los casos identificados
   e. Ejecutar tests para validar que funcionan correctamente
   f. Medir nueva cobertura y continuar si no se alcanzó el threshold
4. Generar reporte final con mejoras de cobertura por archivo
5. Validar que todos los tests pasan correctamente
6. Crear resumen de tests agregados por capa de Clean Architecture

**Estrategia de priorización de tests**:
- **Alta prioridad**: Domain entities, use cases críticos, validaciones
- **Media prioridad**: Infrastructure adapters, formatters, utilities  
- **Baja prioridad**: CLI commands, configuración, logging

**Exclusiones inteligentes**:
- No crear tests triviales para getters/setters simples
- No testear código que solo hace llamadas directas a librerías externas
- No crear tests para configuración estática
- Excluir `src/main.py` (punto de entrada de 45 líneas)

**Criterios de éxito**:
- Cobertura total ≥ threshold especificado
- Todos los tests nuevos pasan correctamente
- Tests enfocados en lógica de negocio crítica
- Código funcionalmente equivalente (sin regresiones)
- Reporte detallado de mejoras por archivo/capa

## Uso de Agentes

Para usar cualquier agente, simplemente escribir su nombre como comando:

```bash
# Ejemplos de uso
qa-agent
build-agent  
release-agent v1.5.0
coverage-agent 80
fix-agent all
fix-coverage-agent 80
```

Los agentes son ejecutados secuencialmente y reportan progreso usando el sistema TodoWrite para tracking de tareas.
