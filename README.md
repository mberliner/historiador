# Jira Batch Importer

Aplicación de línea de comandos para crear historias de usuario en Jira a partir de archivos Excel o CSV.

## Características

- ✅ Procesa archivos Excel (.xlsx, .xls) y CSV
- ✅ **Procesamiento automático** de todos los archivos en directorio de entrada
- ✅ **Gestión automática de directorios** (entrada, logs, procesados)
- ✅ **Movimiento automático** de archivos procesados
- ✅ Crea historias de usuario con título, descripción y criterios de aceptación
- ✅ Soporte para subtareas automáticas
- ✅ Vinculación con Epics/Features padre
- ✅ **Creación automática de Features** a partir de descripciones
- ✅ **Detección inteligente** entre keys existentes vs descripciones de features
- ✅ **Prevención de duplicados** con normalización y cache
- ✅ Procesamiento por lotes configurable
- ✅ Modo dry-run para pruebas
- ✅ Validación de archivos y conexión
- ✅ Logging detallado
- ✅ **Validación avanzada de subtareas** con detección de errores
- ✅ **Rollback opcional** de historias si fallan todas las subtareas
- ✅ **Reporte detallado** de subtareas creadas/fallidas por historia

## Instalación

1. Para construir debe existir python en tu entorno


2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura las variables de entorno:
```bash
cp .env.example .env
# Edita .env con tus credenciales de Jira
```

## Configuración

### Variables de Entorno (.env)

```env
# Configuración de Jira
JIRA_URL=https://tu-empresa.atlassian.net
JIRA_EMAIL=tu-email@empresa.com
JIRA_API_TOKEN=tu-api-token-aqui
PROJECT_KEY=MYPROJ

# Configuración de la aplicación
DEFAULT_ISSUE_TYPE=Story
SUBTASK_ISSUE_TYPE=Sub-task
BATCH_SIZE=10
DRY_RUN=false
ACCEPTANCE_CRITERIA_FIELD=customfield_10001

# Configuración de directorios
INPUT_DIRECTORY=entrada
LOGS_DIRECTORY=logs
PROCESSED_DIRECTORY=procesados

# Configuración de subtareas
ROLLBACK_ON_SUBTASK_FAILURE=false

# Configuración de features
FEATURE_ISSUE_TYPE=Feature
FEATURE_REQUIRED_FIELDS=
```

### Obtener API Token de Jira

1. Ve a https://id.atlassian.com/manage-profile/security/api-tokens
2. Crea un nuevo token
3. Usa tu email y el token para autenticación

### Configurar Campo de Criterios de Aceptación

Para usar un campo personalizado para criterios de aceptación:

1. **Encontrar el ID del campo**:
   - Ve a Jira Settings > Issues > Custom fields
   - Busca el campo "Acceptance Criteria" o "Criterios de Aceptación"
   - Haz clic en More (⋯) > Edit Details
   - El ID aparece en la URL: `customfield_XXXXX`

2. **Configurar en .env**:
   ```env
   ACCEPTANCE_CRITERIA_FIELD=customfield_10001
   ```

3. **Si no tienes este campo**: Los criterios irán en la descripción del issue (comportamiento por defecto)

### Configurar Rollback de Subtareas

La aplicación puede eliminar automáticamente historias si fallan todas sus subtareas:

```env
ROLLBACK_ON_SUBTASK_FAILURE=true
```

**Comportamiento**:
- `false` (defecto): Mantiene la historia aunque fallen todas las subtareas
- `true`: Elimina la historia si fallan todas las subtareas definidas

## Formato del Archivo

### Columnas Requeridas
- `titulo`: Título de la historia de usuario
- `descripcion`: Descripción detallada
- `criterio_aceptacion`: Criterios de aceptación

### Columnas Opcionales
- `subtareas`: Lista de subtareas separadas por `;` o salto de línea
- `parent`: Key del Epic/Feature padre (ej: EPIC-123) **O** descripción de feature a crear automáticamente

### Ejemplo CSV
```csv
titulo,descripcion,subtareas,criterio_aceptacion,parent
"Implementar login","Como usuario quiero poder autenticarme","Crear formulario;Validar credenciales;Mostrar errores","Dado que ingreso credenciales válidas, cuando hago click en login, entonces accedo al sistema;Dado que ingreso credenciales inválidas, entonces veo mensaje de error;La sesión debe persistir por 24 horas","EPIC-123"
"Dashboard principal","Como usuario autenticado quiero ver mi dashboard","","Dado que estoy logueado, cuando accedo a la página principal, entonces veo mi dashboard personalizado","EPIC-123"
"Sistema de notificaciones","Como usuario quiero recibir notificaciones","Crear modelo;Diseñar UI;Implementar push","Las notificaciones deben ser en tiempo real;Debe permitir configurar preferencias","Implementar sistema de comunicaciones para la aplicación"
"Chat en vivo","Como usuario quiero chatear con soporte","Integrar WebSocket;Crear interfaz","El chat debe funcionar en tiempo real;Debe guardar historial","Implementar sistema de comunicaciones para la aplicación"
```

**Nota**: 
- Los criterios de aceptación separados por `;` se mostrarán como elementos de lista con viñetas en Jira
- Las subtareas pueden separarse por `;` o salto de línea (útil en celdas de Excel con Alt+Enter)
- En el campo `parent`:
  - **Key existente** (ej: "EPIC-123"): Se vincula directamente al issue existente
  - **Descripción** (ej: "Implementar sistema de autenticación"): Se crea automáticamente una nueva Feature
  - **Descripciones similares**: Se normalizan y reutilizan para evitar duplicados

## Uso

### Comandos Disponibles

#### Procesar Archivo
```bash
python src/main.py process -f entrada/archivo.csv -p MYPROJ

# Con opciones adicionales
python src/main.py process -f entrada/archivo.xlsx -p MYPROJ --batch-size 5 --dry-run
```

#### Validar Archivo
```bash
python src/main.py validate -f entrada/archivo.csv --rows 10
```

#### Probar Conexión
```bash
python src/main.py test-connection
```

#### Diagnosticar Configuración
```bash
python src/main.py diagnose -p MYPROJ
```

### Opciones de Comandos

#### `process`
- `-f, --file`: Archivo Excel o CSV específico (opcional)
- `-p, --project`: Key del proyecto en Jira
- `-b, --batch-size`: Tamaño del lote (default: 10)
- `--dry-run`: Modo de prueba sin crear issues
- `--log-level`: Nivel de logging (DEBUG, INFO, WARNING, ERROR)

**Nota**: Si no se especifica `--file`, el programa procesará automáticamente todos los archivos CSV/Excel encontrados en el directorio de entrada.

#### `validate`
- `-f, --file`: Archivo a validar (requerido)
- `-r, --rows`: Número de filas a mostrar (default: 5)

#### `diagnose`
- `-p, --project`: Key del proyecto en Jira
- Verifica configuración de tipos de issue, campos obligatorios y permisos

#### `test-connection`
- Verifica conectividad con Jira y autenticación

## Ejemplos

### Procesamiento Automático (Por Defecto)
```bash
# Procesa todos los archivos CSV/Excel del directorio de entrada
python src/main.py -p DEMO

# Con modo dry-run
python src/main.py -p DEMO --dry-run

# También funciona con el comando explícito
python src/main.py process -p DEMO
```

### Procesamiento de Archivo Específico
```bash
# Procesa un archivo específico
python src/main.py process -f entrada/historias.csv -p DEMO

# Con modo dry-run
python src/main.py process -f entrada/historias.xlsx -p DEMO --dry-run
```

### Validación de Archivo
```bash
python src/main.py validate -f entrada/historias.csv
```

### Con Logging Detallado
```bash
python src/main.py --log-level DEBUG process -f entrada/historias.csv -p DEMO
```

### Usando el Archivo de Ejemplo Incluido
```bash
# Validar el archivo de ejemplo
python src/main.py validate -f entrada/ejemplo_historias.csv

# Probar en modo dry-run (comando por defecto)
python src/main.py -p TU_PROYECTO --dry-run

# Ejecutar procesamiento real (cambiar TU_PROYECTO por tu project key)
python src/main.py -p TU_PROYECTO

# O procesar archivo específico
python src/main.py -f entrada/ejemplo_historias.csv -p TU_PROYECTO
```

## Estructura del Proyecto

```
historiador/
├── entrada/                     # 📁 Archivos de entrada (CSV/Excel)
│   └── ejemplo_historias.csv    # Archivo de ejemplo incluido
├── procesados/                  # 📁 Archivos ya procesados (creado automáticamente)
├── logs/                        # 📁 Archivos de log (creado automáticamente)
│   └── jira_batch.log          # Log detallado de ejecuciones
├── src/
│   ├── config/
│   │   └── settings.py          # Configuración de la aplicación
│   ├── models/
│   │   └── jira_models.py       # Modelos de datos
│   ├── services/
│   │   ├── file_processor.py    # Procesamiento de archivos
│   │   ├── jira_client.py       # Cliente de Jira API
│   │   └── feature_manager.py   # Gestión automática de features
│   └── main.py                  # Aplicación principal
├── requirements.txt             # Dependencias
├── .env                        # Configuración (crear desde .env.example)
├── .env.example                # Ejemplo de configuración
└── README.md                   # Documentación
```

## Logging

La aplicación genera logs en:
- Consola (stdout)
- Archivo `logs/jira_batch.log` (directorio creado automáticamente)

Niveles de log disponibles: DEBUG, INFO, WARNING, ERROR

## Gestión Automática de Directorios

La aplicación crea automáticamente los siguientes directorios si no existen:

- **`entrada/`**: Donde colocar los archivos CSV/Excel a procesar
- **`logs/`**: Donde se almacenan los logs de ejecución
- **`procesados/`**: Donde se mueven los archivos después de ser procesados exitosamente

### Flujo de Procesamiento

1. **Colocar archivos**: Poner archivos CSV/Excel en el directorio `entrada/`
2. **Ejecutar**: `python src/main.py -p TU_PROYECTO`
3. **Procesamiento**: Se procesan todos los archivos en secuencia
4. **Movimiento**: Archivos exitosos se mueven a `procesados/`
5. **Logs**: Detalles del procesamiento en `logs/jira_batch.log`

## Manejo de Errores

- ✅ Validación de archivos y formato
- ✅ Verificación de conexión con Jira
- ✅ Validación de proyectos y issues padre
- ✅ **Validación de tipos de subtareas** antes del procesamiento
- ✅ Manejo de errores por fila y por archivo
- ✅ **Detección de subtareas inválidas** (vacías o >255 caracteres)
- ✅ Reporte detallado de fallos
- ✅ **Contadores de subtareas** creadas/fallidas por historia
- ✅ Los archivos con errores no se mueven de `entrada/`

### Validación de Subtareas

La aplicación valida automáticamente:

1. **Tipo de issue**: Verifica que `Sub-task` existe en el proyecto
2. **Formato**: Detecta títulos vacíos o excesivamente largos (>255 caracteres)
3. **Permisos**: Valida capacidad de crear subtareas
4. **Rollback**: Opcional eliminación si fallan todas las subtareas

### Validación de Features

La aplicación maneja automáticamente la creación de features:

1. **Detección inteligente**: Distingue entre keys existentes (PROJ-123) y descripciones
2. **Validación de keys**: Verifica que keys existentes sean válidas en Jira
3. **Creación automática**: Genera features a partir de descripciones
4. **Normalización**: Convierte descripciones similares al mismo formato
5. **Cache**: Evita crear features duplicadas en el mismo lote
6. **Búsqueda**: Busca features existentes en Jira antes de crear nuevas

**En el comando `validate`**:
```bash
python src/main.py validate -f entrada/archivo.csv
```

Muestra estadísticas de subtareas y detecta problemas antes del procesamiento.

## Distribución como Ejecutable

### Generar Ejecutable

Para crear un ejecutable independiente que incluya todas las dependencias:

```bash
# Instalar PyInstaller (solo la primera vez)
pip install pyinstaller

# Generar ejecutable
python -m PyInstaller --onefile --name historiador --add-data ".env.example;." src/main.py --clean
```

El ejecutable se generará en el directorio `dist/historiador.exe`

### Usar el Ejecutable

1. **Crear estructura de directorios**: El ejecutable creará automáticamente los directorios necesarios
2. **Configurar variables de entorno**: Copiar `.env.example` como `.env` y configurar las credenciales de Jira
3. **Colocar archivos**: Poner archivos CSV/Excel en el directorio `entrada/`
4. **Ejecutar**: `historiador.exe -p TU_PROYECTO`

### Distribución

Para distribuir la aplicación:

1. Copiar `historiador.exe` al equipo destino
2. Crear archivo `.env` con las configuraciones necesarias
3. La aplicación funcionará sin necesidad de instalar Python

## Funcionalidad de Creación Automática de Features

### ¿Cómo Funciona?

La aplicación puede **crear automáticamente Features** cuando el campo `parent` contiene una descripción en lugar de una key existente:

```csv
titulo,descripcion,subtareas,criterio_aceptacion,parent
"Historia 1","Descripción 1","Subtarea A","Criterio A","PROJ-100"
"Historia 2","Descripción 2","Subtarea B","Criterio B","Implementar sistema de autenticación"
"Historia 3","Descripción 3","Subtarea C","Criterio C","Implementar sistema de autenticación"
```

**Resultado:**
- **Historia 1**: Se vincula al issue existente `PROJ-100`
- **Historia 2**: Se crea una nueva Feature con título "Implementar sistema de autenticación..." y se vincula
- **Historia 3**: Se reutiliza la Feature creada para Historia 2 (misma descripción normalizada)

### Detección Inteligente

La aplicación distingue automáticamente entre:

1. **Keys de Jira** (formato: `PROJ-123`)
   - Se valida que existan en Jira
   - Se vincula directamente
   - Si no existe, falla el procesamiento

2. **Descripciones de Features** (cualquier otro texto)
   - Se normaliza el texto (minúsculas, sin acentos, etc.)
   - Se busca si ya existe una Feature similar
   - Si no existe, se crea automáticamente
   - Se cachea para evitar duplicados en el mismo lote

### Normalización y Duplicados

Para evitar Features duplicadas, la aplicación:

1. **Normaliza** las descripciones:
   ```
   "Implementar Sistema de Autenticación!!!"
   "implementar sistema de autenticacion"
   "Implementar sistema de autenticación"
   ```
   Todas se normalizan a: `"implementar sistema de autenticacion"`

2. **Busca** Features existentes en Jira con descripción similar
3. **Reutiliza** Features encontradas
4. **Crea** solo si no existe una similar

### Configuración Avanzada

#### Campos Obligatorios para Features

Si tu instancia de Jira requiere campos obligatorios para Features:

```env
# Configuración manual de campos obligatorios (formato JSON)
FEATURE_REQUIRED_FIELDS={"customfield_10020": {"id": "1"}, "customfield_10021": {"value": "Medium"}}
```

#### Tipo de Feature Personalizado

```env
# Si el tipo de issue para features no es "Feature"
FEATURE_ISSUE_TYPE=Epic
```

### Comando de Diagnóstico

Para verificar la configuración de Features:

```bash
python src/main.py diagnose -p MYPROJ
```

Este comando verifica:
- ✅ Tipo de feature válido en el proyecto
- ✅ Campos obligatorios detectados automáticamente
- ✅ Permisos para crear features
- ✅ Configuración de la aplicación

### Ejemplo Completo

```csv
titulo,descripcion,subtareas,criterio_aceptacion,parent
"Login de usuario","Como usuario quiero autenticarme","Crear formulario;Validar datos","Usuario debe poder loguearse","Sistema de Autenticación y Autorización"
"Registro de usuario","Como visitante quiero registrarme","Crear formulario;Enviar email","Registro debe ser fácil","Sistema de Autenticación y Autorización"
"Dashboard admin","Como admin quiero ver métricas","Crear gráficos;Conectar DB","Dashboard debe ser informativo","PROJ-50"
"Reportes","Como admin quiero generar reportes","Diseñar templates;Exportar PDF","Reportes deben ser precisos","PROJ-50"
```

**Resultado:**
1. Se crea **1 Feature nueva**: "Sistema de Autenticación y Autorización..."
2. Se reutiliza **1 Epic existente**: `PROJ-50`
3. Se crean **4 Historias** vinculadas a sus respectivos parents
4. **Login** y **Registro** → vinculadas a la Feature creada
5. **Dashboard** y **Reportes** → vinculadas al Epic existente

## Limitaciones

- Requiere permisos de creación de issues en Jira
- El proyecto debe existir previamente
- Los issues padre deben existir antes de procesamiento (para keys específicas)
- Formato específico de archivos requerido
- Solo archivos con al menos una historia exitosa se mueven a `procesados/`
- La creación de Features requiere permisos de creación del tipo de issue configurado