# Historiador - Jira Batch Importer

**Automatiza la creación masiva de historias de usuario en Jira** desde archivos Excel/CSV con subtareas automáticas, criterios de aceptación y vinculación a Features.

## 💡 ¿Qué hace?

- **Importa historias masivamente** desde CSV/Excel a Jira
- **Crea subtareas automáticamente** para cada historia
- **Genera Features** automáticamente desde descripciones
- **Valida archivos** antes del procesamiento 
- **Modo dry-run** para pruebas sin modificar Jira
- **Configuración interactiva** la primera vez que lo usas

## 📥 Descarga

Descarga el ejecutable desde [releases](https://github.com/mberliner/historiador/releases) o genéralo:
```bash
pip install pyinstaller
pyinstaller historiador-clean.spec --clean
```

## 🚀 Comandos del Ejecutable

### Procesamiento Automático
```bash
# Procesa TODOS los archivos en entrada/
./historiador

# Procesa archivos de un proyecto específico
./historiador -p PROYECTO_KEY

# Modo prueba - NO modifica Jira
./historiador --dry-run
./historiador -p PROYECTO_KEY --dry-run
```

### Validación y Diagnóstico
```bash
# Valida archivo sin crear nada en Jira
./historiador validate -f entrada/archivo.csv

# Diagnostica campos obligatorios del proyecto
./historiador diagnose -p PROYECTO_KEY

# Prueba conexión y configuración
./historiador test-connection
```

### Procesamiento Específico
```bash
# Procesa archivo específico
./historiador process -f entrada/archivo.csv -p PROYECTO_KEY

# Modo dry-run para archivo específico
./historiador process -f entrada/archivo.csv -p PROYECTO_KEY --dry-run
```

## 📋 Formato de Archivo

**Columnas requeridas:**
- `titulo` - Título de la historia de usuario
- `descripcion` - Descripción detallada de la funcionalidad

**Columnas opcionales:**
- `criterio_aceptacion` - Criterios separados por `;`
- `subtareas` - Lista separada por `;` o salto de línea
- `parent` - Key existente (`PROJ-123`) o descripción para crear Feature

**Campo parent:**
- Key existente (`PROJ-123`) → Se vincula directamente
- Descripción (`"Sistema de Login"`) → Se crea Feature automáticamente
- Features similares → Se reutilizan para evitar duplicados

**Ejemplo CSV:**
```csv
titulo,descripcion,subtareas,criterio_aceptacion,parent
"Login usuario","Como usuario quiero autenticarme","Crear formulario;Validar datos","Login exitoso;Error con credenciales inválidas","Sistema de Autenticación"
"Dashboard admin","Como admin quiero ver métricas","Crear gráficos;Conectar BD","Dashboard carga en <3s","PROJ-50"
"Logout","Como usuario quiero cerrar sesión","Limpiar sesión","Sesión cerrada correctamente",""
```

## ⚙️ Configuración

**Primera vez:** La aplicación te pedirá los datos automáticamente:
```bash
./historiador test-connection
```

**Manual (.env):**
```env
JIRA_URL=https://empresa.atlassian.net
JIRA_EMAIL=email@empresa.com
JIRA_API_TOKEN=tu-token-aqui
PROJECT_KEY=PROJ
```

**Obtener API Token:** [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)

## 📁 Directorios

```
├── entrada/           # Tus archivos CSV/Excel aquí
├── procesados/        # Archivos procesados exitosamente  
├── logs/             # Logs de ejecución
└── dist/             # Ejecutable descargado
```

## 🔧 Desarrollo

**Instalar dependencias:**
```bash
pip install -r requirements.txt
cp .env.example .env  # Editar con tus credenciales
```

**Usar con Python:**
```bash
python src/main.py test-connection
python src/main.py --dry-run
```

**Generar ejecutable:**
```bash
pyinstaller historiador-clean.spec --clean
```