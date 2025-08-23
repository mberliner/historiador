# Jira Batch Importer

Aplicación CLI para crear historias de usuario en Jira desde archivos Excel/CSV con gestión automática de subtareas y Features.

## 🚀 Inicio Rápido

**Requisitos**: Python 3.8+

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   # Para desarrollo:
   pip install -r requirements-dev.txt
   ```

2. **Configurar credenciales:**
   ```bash
   cp .env.example .env
   # Editar .env con tus credenciales de Jira
   ```

3. **Probar conexión:**
   ```bash
   python src/main.py test-connection
   ```

4. **Procesar archivos:**
   ```bash
   # Modo prueba
   python src/main.py -p TU_PROYECTO --dry-run
   
   # Procesamiento real
   python src/main.py -p TU_PROYECTO
   ```

## ✨ Características Principales

- ✅ **Procesamiento automático** de archivos CSV/Excel
- ✅ **Creación automática de Features** desde descripciones
- ✅ **Subtareas automáticas** con validación avanzada
- ✅ **Prevención de duplicados** con normalización inteligente
- ✅ **Modo dry-run** para pruebas seguras
- ✅ **Rollback opcional** si fallan subtareas
- ✅ **Reportes detallados** de procesamiento

## 📋 Formato de Archivo

### Columnas Requeridas
- `titulo`: Título de la historia
- `descripcion`: Descripción detallada  
- `criterio_aceptacion`: Criterios separados por `;`

### Columnas Opcionales
- `subtareas`: Lista separada por `;` o salto de línea
- `parent`: Key existente (`PROJ-123`) **O** descripción para crear Feature

### Ejemplo CSV
```csv
titulo,descripcion,subtareas,criterio_aceptacion,parent
"Login usuario","Como usuario quiero autenticarme","Crear formulario;Validar datos","Login exitoso con credenciales válidas;Error visible con credenciales inválidas","Sistema de Autenticación"
"Dashboard admin","Como admin quiero ver métricas","Crear gráficos;Conectar BD","Dashboard carga en <3s;Datos actualizados","PROJ-50"
```

## 🔧 Comandos Principales

```bash
# Procesar todos los archivos en entrada/
python src/main.py

# Procesar todos los archivos en entrada e impactar en un proyecto jira especifico/
python src/main.py -p KEY_PROYECTO

# Procesar archivo específico
python src/main.py process -f archivo.csv -p PROYECTO

# Validar archivo sin crear issues
python src/main.py validate -f archivo.csv

# Diagnosticar configuración
python src/main.py diagnose -p PROYECTO

# Si tienes el ejecutable:
historiador = python src/main.py

```

## ⚙️ Configuración Básica (.env)

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

## 📁 Estructura del Proyecto

```
historiador/
├── entrada/                    # Archivos CSV/Excel a procesar
├── procesados/                 # Archivos procesados exitosamente  
├── logs/                      # Logs de ejecución
├── src/
│   ├── presentation/          # CLI y formatters
│   ├── application/           # Casos de uso e interfaces
│   ├── domain/               # Entidades y repositorios
│   ├── infrastructure/       # Implementaciones (Jira, archivos)
│   └── main.py              # Punto de entrada
├── requirements.txt
├── .env                     # Configuración
└── README.md
```

## 🔍 Gestión Automática de Features

La aplicación distingue automáticamente:

- **Keys existentes** (`PROJ-123`) → Se vincula directamente
- **Descripciones** (`"Sistema de Login"`) → Se crea Feature automáticamente
- **Descripciones similares** → Se reutilizan para evitar duplicados

## 📖 Documentación Completa

- **[DOCS.md](DOCS.md)**: Ejemplos avanzados, troubleshooting y configuración detallada
- **[BUILD_OPTIMIZATION.md](BUILD_OPTIMIZATION.md)**: Detalles de optimización del ejecutable (83MB → 51MB)
- **[CLAUDE.md](CLAUDE.md)**: Contexto técnico completo para desarrollo

## 🛠️ Generar Ejecutable

### Recomendado (51MB optimizado):
```bash
pip install pyinstaller
pyinstaller historiador-clean.spec --clean
```

### Alternativas:
```bash
# Comando directo (53MB)
pyinstaller --onefile --name historiador \
  --exclude-module pytest --exclude-module pylint --exclude-module black \
  --add-data=".env.example:." src/main.py --clean

# Completo con dev tools (83MB)
python -m PyInstaller --onefile --name historiador --add-data=".env.example:." src/main.py --clean
```

El ejecutable optimizado se genera en `dist/historiador` (Linux/Mac) o `dist/historiador.exe` (Windows).

## 📝 Obtener API Token

1. Ve a https://id.atlassian.com/manage-profile/security/api-tokens
2. Crea un nuevo token
3. Usa tu email y el token en `.env`

---

**Arquitectura**: Clean Architecture con 4 capas (Presentation, Application, Domain, Infrastructure)  
**Calidad**: PyLint Score 8.96/10 | Test Coverage 80.58% | Ejecutable optimizado 51MB
