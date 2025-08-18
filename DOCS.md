# Documentación Detallada - Jira Batch Importer

## Tabla de Contenidos

- [Configuración Avanzada](#configuración-avanzada)
- [Comandos y Opciones](#comandos-y-opciones)
- [Formato de Archivos](#formato-de-archivos)
- [Gestión de Features](#gestión-de-features)
- [Testing y Coverage](#testing-y-coverage)
- [CI/CD Pipelines](#cicd-pipelines)
- [Validación y Manejo de Errores](#validación-y-manejo-de-errores)
- [Ejemplos Completos](#ejemplos-completos)
- [Troubleshooting](#troubleshooting)
- [Arquitectura](#arquitectura)

## Configuración Avanzada

### Variables de Entorno Completas

```env
# === Configuración de Jira (Requerido) ===
JIRA_URL=https://tu-empresa.atlassian.net
JIRA_EMAIL=tu-email@empresa.com
JIRA_API_TOKEN=tu-api-token-aqui
PROJECT_KEY=MYPROJ

# === Tipos de Issue ===
DEFAULT_ISSUE_TYPE=Story
SUBTASK_ISSUE_TYPE=Sub-task
FEATURE_ISSUE_TYPE=Feature

# === Configuración de Procesamiento ===
BATCH_SIZE=10
DRY_RUN=false

# === Campos Personalizados ===
ACCEPTANCE_CRITERIA_FIELD=customfield_10001

# === Configuración de Directorios ===
INPUT_DIRECTORY=entrada
LOGS_DIRECTORY=logs
PROCESSED_DIRECTORY=procesados

# === Configuración de Subtareas ===
ROLLBACK_ON_SUBTASK_FAILURE=false

# === Configuración de Features ===
FEATURE_REQUIRED_FIELDS={"customfield_10020": {"id": "1"}}
```

### Obtener Campo de Criterios de Aceptación

1. **Encontrar el ID del campo**:
   - Ve a Jira Settings > Issues > Custom fields
   - Busca "Acceptance Criteria" o "Criterios de Aceptación"
   - Haz clic en More (⋯) > Edit Details
   - El ID aparece en la URL: `customfield_XXXXX`

2. **Configurar en .env**:
   ```env
   ACCEPTANCE_CRITERIA_FIELD=customfield_10001
   ```

3. **Si no tienes este campo**: Los criterios irán en la descripción (comportamiento por defecto)

### Rollback de Subtareas

```env
ROLLBACK_ON_SUBTASK_FAILURE=true
```

**Comportamiento**:
- `false` (defecto): Mantiene la historia aunque fallen todas las subtareas
- `true`: Elimina la historia si fallan todas las subtareas definidas

## Comandos y Opciones

### Comando `process`

```bash
python src/main.py process [OPCIONES]
```

**Opciones**:
- `-f, --file`: Archivo específico (opcional)
- `-p, --project`: Key del proyecto (requerido)
- `-b, --batch-size`: Tamaño del lote (default: 10)
- `--dry-run`: Modo prueba sin crear issues
- `--log-level`: DEBUG, INFO, WARNING, ERROR

**Ejemplos**:
```bash
# Procesar todos los archivos
python src/main.py process -p DEMO

# Archivo específico con dry-run
python src/main.py process -f entrada/historias.csv -p DEMO --dry-run

# Con logging detallado
python src/main.py process -p DEMO --log-level DEBUG
```

### Comando `validate`

```bash
python src/main.py validate -f archivo.csv [OPCIONES]
```

**Opciones**:
- `-f, --file`: Archivo a validar (requerido)
- `-r, --rows`: Número de filas a mostrar (default: 5)

**Ejemplo**:
```bash
python src/main.py validate -f entrada/historias.csv --rows 10
```

### Comando `diagnose`

```bash
python src/main.py diagnose -p PROYECTO
```

Verifica:
- ✅ Conexión con Jira
- ✅ Tipos de issue válidos
- ✅ Campos obligatorios para Features
- ✅ Permisos de creación

### Comando `test-connection`

```bash
python src/main.py test-connection
```

Prueba conectividad y autenticación con Jira.

## Formato de Archivos

### Estructura Completa

| Columna | Requerida | Descripción | Ejemplo |
|---------|-----------|-------------|---------|
| `titulo` | ✅ | Título de la historia (máx 255 caracteres) | "Login de usuario" |
| `descripcion` | ✅ | Descripción detallada | "Como usuario quiero autenticarme..." |
| `criterio_aceptacion` | ✅ | Criterios separados por `;` | "Login exitoso;Error visible" |
| `subtareas` | ❌ | Subtareas separadas por `;` o `\n` | "Crear formulario;Validar datos" |
| `parent` | ❌ | Key existente o descripción | "PROJ-123" o "Sistema Login" |

### Formato de Criterios de Aceptación

```csv
criterio_aceptacion
"Criterio único sin separador"
"Criterio 1;Criterio 2;Criterio 3"
"Dado que...;Cuando...;Entonces..."
```

**Resultado en Jira**:
- **Sin separador**: Texto plano
- **Con separador `;`**: Lista con viñetas (•)

### Formato de Subtareas

```csv
subtareas
"Subtarea única"
"Subtarea 1;Subtarea 2;Subtarea 3"
"Línea 1
Línea 2
Línea 3"
```

**Validaciones**:
- ✅ No pueden estar vacías
- ✅ Máximo 255 caracteres por subtarea
- ✅ Se crean como issues tipo "Subtarea"

## Gestión de Features

### Detección Automática

La aplicación distingue automáticamente entre:

1. **Keys de Jira** (formato: `PROJ-123`)
   - Se valida existencia en Jira
   - Se vincula directamente
   - **Falla** si no existe

2. **Descripciones** (cualquier otro texto)
   - Se normaliza y busca Features similares
   - Se crea automáticamente si no existe
   - Se reutiliza si encuentra similar

### Proceso de Normalización

```
Input: "Implementar Sistema de Autenticación!!!"
Step 1: Convertir a minúsculas
Step 2: Remover acentos (á→a, é→e, etc.)
Step 3: Limpiar espacios múltiples
Step 4: Remover puntuación final
Step 5: Limpiar caracteres especiales
Output: "implementar sistema de autenticacion"
```

### Búsqueda de Duplicados

1. **Cache local**: Verifica Features creadas en el mismo lote
2. **Búsqueda en Jira**: Usa JQL para encontrar Features similares
3. **Comparación**: Normaliza descripciones para comparar
4. **Decisión**: Reutiliza existente o crea nueva

### Configuración de Campos Obligatorios

Si tu Jira requiere campos obligatorios para Features:

```env
# Formato JSON con campos y valores
FEATURE_REQUIRED_FIELDS={"customfield_10020": {"id": "1"}, "customfield_10021": {"value": "Medium"}}
```

**Detección automática**: El comando `diagnose` detecta campos obligatorios automáticamente.

## Testing y Coverage

### Estrategia de Testing

El proyecto implementa testing exhaustivo con múltiples niveles:

#### **Tests Unitarios**
```bash
# Ejecutar todos los tests unitarios
pytest tests/unit/

# Tests específicos por módulo
pytest tests/unit/domain/
pytest tests/unit/application/
pytest tests/unit/infrastructure/
pytest tests/unit/presentation/
```

#### **Estructura de Tests**
```
tests/
├── unit/                           # Tests unitarios
│   ├── application/               # Tests de casos de uso
│   │   ├── test_process_files_use_case.py
│   │   ├── test_validate_file_use_case.py
│   │   └── test_diagnose_features_use_case.py
│   ├── domain/                    # Tests de entidades
│   │   ├── test_user_story.py
│   │   ├── test_process_result.py
│   │   └── test_batch_result.py
│   ├── infrastructure/           # Tests de infraestructura
│   │   ├── jira/
│   │   │   ├── test_jira_client.py
│   │   │   ├── test_feature_manager.py
│   │   │   └── test_utils.py
│   │   └── file_system/
│   │       └── test_file_processor.py
│   └── presentation/             # Tests de CLI
│       ├── cli/test_commands.py
│       └── formatters/test_output_formatter.py
├── fixtures/                     # Datos de prueba
│   ├── jira_responses.py        # Mocks de respuestas Jira
│   └── sample_data.py           # Datos CSV de ejemplo
└── conftest.py                  # Configuración pytest
```

#### **Mocks y Fixtures**

El proyecto usa mocks para aislar componentes:

```python
# Ejemplo: Mock de Jira API
@pytest.fixture
def mock_jira_client():
    with patch('infrastructure.jira.jira_client.requests') as mock_requests:
        mock_requests.post.return_value.json.return_value = {
            "key": "PROJ-123",
            "id": "10001"
        }
        yield mock_requests

# Uso en tests
def test_create_issue(mock_jira_client):
    result = jira_client.create_issue(issue_data)
    assert result.key == "PROJ-123"
```

### Políticas de Coverage

#### **Umbrales de Coverage**
- **Mínimo requerido**: 80%
- **Objetivo**: 90%+
- **Crítico**: Nunca < 75%

#### **Coverage por Módulo**
```bash
# Coverage detallado por archivo
pytest --cov=src --cov-report=html tests/unit/

# Coverage con exclusiones
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

#### **Archivos Excluidos del Coverage**
```ini
# .coveragerc
[run]
omit = 
    */tests/*
    */venv/*
    */migrations/*
    src/main.py  # Entry point simple
```

#### **Reportes de Coverage**

**Terminal Report:**
```bash
pytest --cov=src --cov-report=term
# Muestra % por archivo

pytest --cov=src --cov-report=term-missing
# Muestra líneas no cubiertas
```

**HTML Report:**
```bash
pytest --cov=src --cov-report=html
# Genera htmlcov/index.html navegable
```

**XML Report (CI/CD):**
```bash
pytest --cov=src --cov-report=xml
# Genera coverage.xml para herramientas CI
```

### Comandos de Testing

#### **Development Workflow**
```bash
# Quick test (solo cambios)
pytest tests/unit/application/ -v

# Full test suite con coverage
pytest tests/unit/ --cov=src --cov-report=term-missing

# Test específico
pytest tests/unit/domain/test_user_story.py::test_validate_title -v

# Test con debugging
pytest tests/unit/ -s -vv --tb=short
```

#### **CI/CD Commands**
```bash
# Comando usado en CI (falla si coverage < 80%)
pytest tests/unit/ --cov=src --cov-report=xml --cov-fail-under=80

# Linting antes de tests
pylint src/ --fail-under=8.0

# Comando completo CI
pylint src/ --fail-under=8.0 && pytest tests/unit/ --cov=src --cov-fail-under=80
```

#### **Performance Testing**
```bash
# Tests con timing
pytest tests/unit/ --durations=10

# Profile de memoria
pytest tests/unit/ --profile

# Parallel execution
pytest tests/unit/ -n auto  # Requiere pytest-xdist
```

### Quality Gates

#### **Pre-commit Hooks**
```yaml
# .pre-commit-config.yaml (ejemplo)
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest tests/unit/ --cov=src --cov-fail-under=80
        language: system
        pass_filenames: false
        
      - id: pylint
        name: pylint
        entry: pylint src/ --fail-under=8.0
        language: system
        files: \.py$
```

#### **IDE Integration**
```json
// VSCode settings.json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests/unit/",
        "--cov=src",
        "--cov-report=html"
    ],
    "coverage-gutters.coverageFileNames": [
        "coverage.xml",
        "htmlcov/index.html"
    ]
}
```

## CI/CD Pipelines

El proyecto cuenta con pipelines automatizados en **GitHub Actions** y **GitLab CI** que garantizan la calidad del código.

### GitHub Actions

#### **Configuración Actual**
```yaml
# .github/workflows/ci.yaml
name: CI
on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]
```

#### **Jobs Implementados**

**1. Test Matrix:**
- **Python 3.8 y 3.11** ejecutándose en paralelo
- **Fail-fast**: Pipeline se detiene si falla cualquier versión
- **Cache de pip** para optimizar velocidad

**2. Quality Gates:**
```bash
# Linting obligatorio (score ≥ 8.0)
pylint src/ --fail-under=8.0 --output-format=text

# Coverage mínimo (≥ 80%)
pytest tests/unit/ --cov=src --cov-report=xml --cov-fail-under=80
```

**3. Build y Validación:**
```bash
# Generación de ejecutable
pyinstaller --onefile --name historiador --add-data=".env.example:." src/main.py --clean

# Test del ejecutable
./dist/historiador --help
```

**4. Artifacts Generados:**
- **Coverage report** (coverage.xml) - Solo Python 3.8
- **Ejecutable binario** (historiador-executable-SHA)
- **Build logs** (solo en caso de error)

#### **Branch Protection Configurado**
```yaml
Required status checks:
  - test / Test and Quality Checks (3.8)
  - test / Test and Quality Checks (3.11)
  - build / Build Executable

Branch rules:
  - Require pull request reviews: 1
  - Dismiss stale PR approvals: ✅
  - Include administrators: ✅
  - No direct pushes to master
```

### GitLab CI

#### **Configuración Equivalente**
```yaml
# .gitlab-ci.yml
workflow:
  rules:
    - if: $CI_COMMIT_BRANCH == "master"
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

stages:
  - test
  - build
```

#### **Jobs Configurados**

**1. Test Matrix GitLab:**
```yaml
test:
  parallel:
    matrix:
      - PYTHON_VERSION: ["3.8", "3.11"]
  image: python:${PYTHON_VERSION}
  script:
    - pylint src/ --fail-under=8.0
    - pytest tests/unit/ --cov=src --cov-fail-under=80
```

**2. Build Job:**
```yaml
build:
  image: python:3.8
  needs: [test]
  script:
    - pyinstaller --onefile --name historiador src/main.py
    - ./dist/historiador --help
```

#### **Diferencias Implementadas**

| Feature | GitHub Actions | GitLab CI |
|---------|----------------|-----------|
| **Triggers** | Push + PR a master | Push + MR a master |
| **Matrix** | `strategy: matrix` | `parallel: matrix` |
| **Cache** | `actions/cache@v4` | `cache: paths:` |
| **Coverage** | Upload artifact | `reports: coverage_report` |
| **Dependencies** | `needs: [test]` | `needs: - test` |

### Pipeline Status

#### **Triggers Actuales**
- ✅ **Push a master** → Ejecuta pipeline completo
- ✅ **Pull/Merge Requests** → Ejecuta pipeline completo
- ❌ **Tags** → No configurado actualmente
- ❌ **Scheduled** → No configurado

#### **Quality Gates Activos**
- 🔍 **PyLint Score** ≥ 8.0 (obligatorio)
- 📊 **Test Coverage** ≥ 80% (obligatorio)
- 🧪 **Unit Tests** deben pasar (obligatorio)
- 🏗️ **Build Success** ejecutable funcional (obligatorio)

### Workflow de Desarrollo

#### **Flujo Actual**
```bash
1. Developer crea branch feature/xxx
2. Push a GitHub → GitHub Actions ejecuta
3. Crear Pull Request → Re-ejecuta pipeline
4. Review + CI verde → Merge permitido
5. Merge a master → GitLab sync manual
6. GitLab CI valida sync
```

#### **Branch Protection en Acción**
```bash
# ❌ Esto está bloqueado:
git push origin master

# ✅ Flujo obligatorio:
git checkout -b feature/improvement
git push origin feature/improvement
# → Crear PR → CI pasa → Review → Merge
```

### Artifacts y Reports

#### **GitHub Artifacts**
- **Coverage XML**: Disponible 30 días
- **Ejecutable**: Con SHA único, 30 días retention
- **Build logs**: Solo en fallos, 7 días retention

#### **GitLab Artifacts**
- **Coverage Report**: Integrado en UI de GitLab
- **Ejecutable**: Con SHA único, 30 días
- **Coverage Visualization**: Badges automáticos

### Troubleshooting CI

#### **Errores Comunes**

**1. PyLint Score < 8.0:**
```bash
# Ver detalles del error
pylint src/ --output-format=text

# Fix común: documentar funciones
def process_file(file_path):
    """Process CSV file and create Jira issues."""
```

**2. Coverage < 80%:**
```bash
# Ver líneas no cubiertas
pytest --cov=src --cov-report=term-missing

# Identificar archivos con bajo coverage
pytest --cov=src --cov-report=html
# Ver htmlcov/index.html
```

**3. Build Failure:**
```bash
# Error común: PyInstaller syntax
pyinstaller --add-data=".env.example:." src/main.py  # ✅ Correcto
pyinstaller --add-data ".env.example;." src/main.py  # ❌ Windows syntax
```

**4. Test Failures:**
```bash
# Debug tests localmente
pytest tests/unit/ -v -s --tb=short

# Test específico
pytest tests/unit/domain/test_user_story.py::test_validate -v
```

#### **Comandos de Debug Local**

**Simular CI localmente:**
```bash
# Ejecutar exact CI commands
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pylint src/ --fail-under=8.0 --output-format=text
pytest tests/unit/ --cov=src --cov-report=term --cov-fail-under=80
```

**Test del ejecutable:**
```bash
# Generar como en CI
pyinstaller --onefile --name historiador --add-data=".env.example:." src/main.py --clean
chmod +x dist/historiador
./dist/historiador --help
```

### Estado Actual

#### **Funcionalidades Implementadas**
- ✅ **Dual CI**: GitHub Actions + GitLab CI
- ✅ **Quality Gates**: PyLint + Coverage + Tests
- ✅ **Matrix Testing**: Python 3.8 + 3.11
- ✅ **Branch Protection**: PRs obligatorios
- ✅ **Artifact Generation**: Ejecutables + Reports
- ✅ **Build Validation**: Test de ejecutable

#### **Pendientes de Configurar**
- ⏳ **Release automation**: Tags y releases automáticos
- ⏳ **Deployment**: Deploy a registries/releases
- ⏳ **Notifications**: Slack/email en fallos
- ⏳ **Security scanning**: SAST/dependency check

## Validación y Manejo de Errores

### Validaciones Pre-procesamiento

- ✅ Archivo existe y formato válido (.csv, .xlsx, .xls)
- ✅ Columnas requeridas presentes
- ✅ Conexión con Jira funcional
- ✅ Proyecto existe
- ✅ Tipos de issue válidos
- ✅ Permisos de creación

### Validaciones Por Fila

- ✅ Campos requeridos no vacíos
- ✅ Longitud de título ≤ 255 caracteres
- ✅ Subtareas válidas (no vacías, ≤ 255 caracteres)
- ✅ Parent válido (key existente o descripción)

### Manejo de Errores

**Por historia**:
- Error en historia → Se reporta y continúa con siguiente
- Error en subtareas → Se reporta cuántas fallaron/exitosas

**Por archivo**:
- Al menos 1 historia exitosa → Archivo se mueve a `procesados/`
- Todas las historias fallan → Archivo permanece en `entrada/`

**Logging**:
- Consola: Información resumida
- `logs/jira_batch.log`: Detalles completos

### Reportes de Subtareas

```
✓ Historia PROJ-456 creada exitosamente
  ✓ Subtarea 1 creada: PROJ-457
  ✓ Subtarea 2 creada: PROJ-458
  ✗ Subtarea 3 falló: Error de validación
  📊 Subtareas: 2 exitosas, 1 fallida
```

## Ejemplos Completos

### Ejemplo 1: Proyecto Nuevo con Features Automáticas

**archivo.csv**:
```csv
titulo,descripcion,subtareas,criterio_aceptacion,parent
"Login usuario","Como usuario quiero autenticarme","Crear formulario;Validar credenciales;Manejar errores","Usuario puede loguearse con credenciales válidas;Error visible con credenciales inválidas;Sesión persiste 24h","Sistema de Autenticación y Autorización"
"Logout usuario","Como usuario quiero cerrar sesión","Crear botón logout;Limpiar sesión","Usuario puede cerrar sesión;Redirección a login","Sistema de Autenticación y Autorización"
"Dashboard admin","Como admin quiero ver métricas","Crear gráficos;Conectar con base de datos","Dashboard carga en menos de 3 segundos;Datos actualizados cada minuto","Panel de Administración"
```

**Resultado**:
- ✅ **2 Features creadas**: "Sistema de Autenticación..." y "Panel de Administración..."
- ✅ **3 Historias creadas** vinculadas a sus Features
- ✅ **6 Subtareas creadas** (2+2+2)

### Ejemplo 2: Proyecto Existente con Mix de Keys

**archivo.csv**:
```csv
titulo,descripcion,criterio_aceptacion,parent
"Mejorar performance","Optimizar consultas de base de datos","Consultas ejecutan en <100ms","PROJ-100"
"Agregar cache","Implementar sistema de cache Redis","Cache mejora response time en 50%","PROJ-100"
"Nueva funcionalidad","Implementar sistema de notificaciones","Notificaciones llegan en tiempo real","Módulo de Comunicaciones"
```

**Resultado**:
- ✅ **0 Features creadas** (PROJ-100 existe)
- ✅ **1 Feature creada**: "Módulo de Comunicaciones..."
- ✅ **3 Historias creadas**:
  - 2 vinculadas a PROJ-100 (existente)
  - 1 vinculada a nueva Feature

### Ejemplo 3: Manejo de Errores

**archivo_con_errores.csv**:
```csv
titulo,descripcion,criterio_aceptacion,parent
"Historia válida","Descripción ok","Criterio válido","PROJ-100"
"","Descripción sin título","Criterio","PROJ-100"
"Título muy largo que excede los 255 caracteres permitidos para el campo título en Jira y causa un error de validación porque supera el límite establecido por la aplicación y el sistema","Descripción","Criterio","PROJ-100"
"Historia con subtarea inválida","Descripción","Criterio","PROJ-999"
```

**Resultado**:
- ✅ **1 Historia exitosa**: Se procesa normalmente
- ❌ **3 Historias fallidas**:
  - Título vacío
  - Título muy largo
  - Parent no existe
- 📁 **Archivo no se mueve** (no todas exitosas)

## Troubleshooting

### Errores Comunes

#### Error 404: "Issue type not found"
```
Error: Tipo de issue 'Sub-task' no encontrado
```
**Solución**: Verificar nombres exactos con `diagnose`:
```bash
python src/main.py diagnose -p PROYECTO
```

#### Error 403: "Permission denied"
```
Error HTTP 403 creando historia
```
**Solución**: 
- Verificar permisos de creación en el proyecto
- Verificar que el usuario tenga rol adecuado

#### Error 400: "Field X is required"
```
Error: Campo customfield_10020 es obligatorio
```
**Solución**: Usar comando `diagnose` para detectar campos obligatorios automáticamente:
```bash
python src/main.py diagnose -p PROYECTO
```

#### Error: "Key PROJ-123 no existe"
```
Error procesando parent: PROJ-123
```
**Solución**: 
- Verificar que la key existe en Jira
- O cambiar por descripción para crear Feature automáticamente

### Problemas de Configuración

#### Credenciales incorrectas
```bash
python src/main.py test-connection
```

#### Campos personalizados
```bash
# Encontrar ID de campo de criterios
python src/main.py diagnose -p PROYECTO
```

#### Tipos de issue específicos
```env
# Configurar nombres exactos según tu Jira
SUBTASK_ISSUE_TYPE=Subtarea
FEATURE_ISSUE_TYPE=Epic
```

### Logs Detallados

Para debugging completo:
```bash
python src/main.py --log-level DEBUG process -p PROYECTO
```

Revisa `logs/jira_batch.log` para detalles completos.

## Arquitectura

### Clean Architecture - 4 Capas

```
src/
├── presentation/          # Capa de Presentación
│   ├── cli/              # Comandos CLI (Click)
│   └── formatters/       # Formateo de salida
├── application/          # Capa de Aplicación  
│   ├── interfaces/       # Protocolos/Abstracciones
│   └── use_cases/        # Casos de uso de negocio
├── domain/              # Capa de Dominio
│   ├── entities/        # Modelos de datos puros
│   └── repositories/    # Interfaces de repositorios
└── infrastructure/      # Capa de Infraestructura
    ├── file_system/     # Sistema de archivos
    ├── jira/           # API de Jira
    └── settings.py     # Configuración
```

### Principios Aplicados

- **Separation of Concerns**: Cada capa tiene responsabilidad específica
- **Dependency Inversion**: Capas superiores no dependen de inferiores
- **Interface Segregation**: Interfaces específicas y cohesivas
- **Single Responsibility**: Cada clase tiene una responsabilidad

### Calidad de Código

- **PyLint Score**: 8.64/10
- **Problemas resueltos**: Código duplicado, líneas largas, imports
- **Utilidades compartidas**: `infrastructure/jira/utils.py`
- **Configuraciones especiales**: Imports dinámicos justificados

### Flujo de Datos

```
CLI → Use Cases → Domain Entities → Infrastructure → Jira API
 ↑      ↓            ↓                    ↓
User  Formatters  Validation         File System
```

1. **CLI** recibe comandos del usuario
2. **Use Cases** orquestan la lógica de negocio
3. **Entities** validan y modelan datos
4. **Infrastructure** interactúa con sistemas externos
5. **Formatters** presentan resultados al usuario

---

Para más información, consulta [CLAUDE.md](CLAUDE.md) con contexto específico del proyecto.
