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

# Generar ejecutable
python -m PyInstaller --onefile --name historiador --add-data ".env.example;." src/main.py --clean
```

## Configuración Específica del Proyecto
- **Tipo de subtarea**: "Subtarea" (no "Sub-task" como es común en otros proyectos)
- **Tipo de feature**: "Feature" (configurable via FEATURE_ISSUE_TYPE)
- **Campo personalizado criterios**: Usar variable ACCEPTANCE_CRITERIA_FIELD en .env
- **Separadores de subtareas**: `;` y salto de línea (`\n`)
- **Rollback opcional**: ROLLBACK_ON_SUBTASK_FAILURE=true elimina historia si fallan todas las subtareas
- **Gestión de parents**: Detección automática entre keys existentes y descripciones de features

## Orden de Columnas en Archivos de Entrada
1. `titulo` (requerida)
2. `descripcion` (requerida)
3. `subtareas` (opcional) - separadas por `;` o salto de línea
4. `criterio_aceptacion` (requerida)
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

## Problemas Conocidos y Soluciones
- **Error 404 en /project/{key}/issuetype**: Usar endpoint `/issue/createmeta` con expand
- **Error 403 al eliminar issues**: Común en entornos corporativos, rollback se desactiva automáticamente
- **Tipos de subtarea varían**: Verificar nombres exactos con el comando `validate`
- **Error 400 "Campo X es obligatorio" al crear features**: Usar comando `diagnose` para detectar campos obligatorios automáticamente

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
