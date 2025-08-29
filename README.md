# Historiador - Jira Batch Importer

Aplicación CLI que importa historias de usuario desde archivos Excel/CSV hacia Jira con creación automática de subtareas y Features.

## 🚀 Inicio Rápido

### Opción 1: Usar Ejecutable (Recomendado)

1. **Descargar ejecutable** desde [releases](https://github.com/mberliner/historiador/releases) o generarlo:
   ```bash
   pip install pyinstaller
   pyinstaller historiador-clean.spec --clean
   ```

2. **Configurar (automático)** - La primera vez te pedirá los datos:
   ```bash
   ./historiador test-connection
   ```
   
3. **Procesar archivos:**
   ```bash
   # Modo prueba (sin modificar Jira)
   ./historiador --dry-run
   
   # Procesamiento real
   ./historiador -p TU_PROYECTO
   ```

### Opción 2: Usar Python (Desarrollo)

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar credenciales:**
   ```bash
   cp .env.example .env
   # Editar .env con tus credenciales
   ```

3. **Usar comandos:**
   ```bash
   python src/main.py test-connection
   python src/main.py -p TU_PROYECTO --dry-run
   ```

## 📋 Formato de Archivo

### Columnas
- `titulo` (**requerida**): Título de la historia de usuario
- `descripcion` (**requerida**): Descripción detallada de la funcionalidad
- `criterio_aceptacion` (**opcional**): Criterios separados por `;`
- `subtareas` (**opcional**): Lista separada por `;` o salto de línea
- `parent` (**opcional**): Key existente (`PROJ-123`) o descripción para crear Feature

### Ejemplo CSV
```csv
titulo,descripcion,subtareas,criterio_aceptacion,parent
"Login usuario","Como usuario quiero autenticarme","Crear formulario;Validar datos","Login exitoso;Error con credenciales inválidas","Sistema de Autenticación"
"Dashboard admin","Como admin quiero ver métricas","Crear gráficos;Conectar BD","Dashboard carga en <3s","PROJ-50"
"Logout","Como usuario quiero cerrar sesión","Limpiar sesión","Sesión cerrada correctamente",""
```

## 🔧 Comandos Disponibles

### Con Ejecutable
```bash
# Procesar todos los archivos en entrada/
./historiador

# Para proyecto específico
./historiador -p PROYECTO_KEY

# Modo prueba (sin crear en Jira)
./historiador -p PROYECTO_KEY --dry-run

# Validar archivo
./historiador validate -f archivo.csv

# Diagnosticar configuración
./historiador diagnose -p PROYECTO_KEY
```

### Con Python (equivalentes)
```bash
python src/main.py
python src/main.py -p PROYECTO_KEY
python src/main.py -p PROYECTO_KEY --dry-run
python src/main.py validate -f archivo.csv
python src/main.py diagnose -p PROYECTO_KEY
```

## ✨ Características

- ✅ **Criterios de aceptación opcionales** - Campo no obligatorio
- ✅ **Creación automática de Features** desde descripciones
- ✅ **Subtareas automáticas** con validación
- ✅ **Prevención de duplicados** con normalización
- ✅ **Modo dry-run** para pruebas seguras
- ✅ **Configuración interactiva** primera vez
- ✅ **Procesamiento batch** de múltiples archivos

## ⚙️ Configuración (.env)

```env
# Jira (requerido)
JIRA_URL=https://empresa.atlassian.net
JIRA_EMAIL=email@empresa.com
JIRA_API_TOKEN=tu-token-aqui
PROJECT_KEY=PROJ

# Tipos de issue
SUBTASK_ISSUE_TYPE=Subtarea
FEATURE_ISSUE_TYPE=Feature

# Opcional
ACCEPTANCE_CRITERIA_FIELD=customfield_10001
ROLLBACK_ON_SUBTASK_FAILURE=false
```

### Obtener API Token
1. Ve a https://id.atlassian.com/manage-profile/security/api-tokens
2. Crea un nuevo token
3. Usa tu email y el token en configuración

## 📁 Estructura

```
historiador/
├── entrada/           # Archivos CSV/Excel a procesar
├── procesados/        # Archivos procesados exitosamente  
├── logs/             # Logs de ejecución
├── dist/             # Ejecutable generado
└── src/              # Código fuente (desarrollo)
```

## 🔍 Gestión de Features

La aplicación distingue automáticamente:
- **Keys existentes** (`PROJ-123`) → Se vincula directamente
- **Descripciones** (`"Sistema de Login"`) → Se crea Feature automáticamente
- **Similares** → Se reutilizan para evitar duplicados

## 🛠️ Generar Ejecutable

### Optimizado (51MB):
```bash
pyinstaller historiador-clean.spec --clean
```

### Alternativas:
```bash
# Comando directo (53MB)
pyinstaller --onefile --name historiador \
  --exclude-module pytest --exclude-module pylint \
  --add-data=".env.example:." src/main.py --clean

# Con herramientas desarrollo (83MB)
python -m PyInstaller --onefile --name historiador \
  --add-data=".env.example:." src/main.py --clean
```

---

**Arquitectura**: Clean Architecture | **Calidad**: PyLint 8.9/10 | **Cobertura**: 80%+ | **Ejecutable**: 51MB optimizado