# Proyecto Historiador - Contexto para Claude

## Descripción del Proyecto
Aplicación de línea de comandos que importa historias de usuario desde archivos CSV/Excel hacia Jira, con soporte para subtareas automáticas y vinculación con Epics.

## Comandos Importantes
```bash
# Ejecutar aplicación (procesamiento automático)
python src/main.py -p PROJECT_KEY

# Procesar archivo específico
python src/main.py process -f entrada/archivo.csv -p PROJECT_KEY

# Validar archivo sin crear issues
python src/main.py validate -f entrada/archivo.csv

# Modo dry-run para pruebas
python src/main.py -p PROJECT_KEY --dry-run

# Generar ejecutable
python -m PyInstaller --onefile --name historiador --add-data ".env.example;." src/main.py --clean
```

## Configuración Específica del Proyecto
- **Tipo de subtarea**: "Subtarea" (no "Sub-task" como es común en otros proyectos)
- **Campo personalizado criterios**: Usar variable ACCEPTANCE_CRITERIA_FIELD en .env
- **Separadores de subtareas**: `;` y salto de línea (`\n`)
- **Rollback opcional**: ROLLBACK_ON_SUBTASK_FAILURE=true elimina historia si fallan todas las subtareas

## Orden de Columnas en Archivos de Entrada
1. `titulo` (requerida)
2. `descripcion` (requerida)
3. `subtareas` (opcional) - separadas por `;` o salto de línea
4. `criterio_aceptacion` (requerida)
5. `parent` (opcional)

## Arquitectura del Código
- **main.py**: Aplicación principal con CLI usando Click
- **file_processor.py**: Procesamiento de archivos CSV/Excel
- **jira_client.py**: Interacción con API de Jira
- **jira_models.py**: Modelos de datos con validación Pydantic
- **settings.py**: Configuración con variables de entorno

## Funcionalidades Implementadas
- ✅ Procesamiento automático de archivos en directorio de entrada
- ✅ Creación de subtareas con validación avanzada
- ✅ Rollback opcional de historias si fallan todas las subtareas
- ✅ Validación de tipos de issue en Jira antes del procesamiento
- ✅ Reporte detallado de subtareas creadas/fallidas
- ✅ Movimiento automático de archivos procesados

## Validaciones Implementadas
- Existencia del tipo "Subtarea" en el proyecto Jira
- Subtareas inválidas (vacías o >255 caracteres)
- Conexión con Jira y permisos
- Validación de proyecto y issues padre
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
ROLLBACK_ON_SUBTASK_FAILURE=false
ACCEPTANCE_CRITERIA_FIELD=customfield_10001
```

## Problemas Conocidos y Soluciones
- **Error 404 en /project/{key}/issuetype**: Usar endpoint `/issue/createmeta` con expand
- **Error 403 al eliminar issues**: Común en entornos corporativos, rollback se desactiva automáticamente
- **Tipos de subtarea varían**: Verificar nombres exactos con el comando `validate`

## Estructura de Directorios
```
historiador/
├── entrada/          # Archivos CSV/Excel a procesar
├── procesados/       # Archivos ya procesados exitosamente
├── logs/            # Logs de ejecución (jira_batch.log)
├── src/
│   ├── config/      # Configuración (settings.py)
│   ├── models/      # Modelos de datos (jira_models.py)
│   ├── services/    # Lógica de negocio
│   └── main.py      # Aplicación principal
└── dist/            # Ejecutable generado con PyInstaller
```