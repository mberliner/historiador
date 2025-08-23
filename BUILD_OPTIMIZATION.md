# Optimización de Ejecutable - Historiador

## Problema Original: Ejecutable de 83MB

### Causa Raíz
El ejecutable original incluía herramientas de desarrollo innecesarias:
- pytest (~10MB) - Framework de testing  
- pylint (~15MB) - Linter de código
- black (~5MB) - Formateador de código
- coverage (~5MB) - Análisis de cobertura
- responses (~5MB) - HTTP mocking
- faker (~8MB) - Generador de datos fake
- **Total innecesario**: ~54MB de 83MB

### Dependencias Necesarias (Producción)
- pandas (~25MB) - Procesamiento CSV/Excel
- numpy (~15MB) - Dependencia de pandas  
- requests (~5MB) - API Jira
- pydantic (~8MB) - Validación de datos
- openpyxl (~5MB) - Soporte Excel
- click (~2MB) - CLI framework

## Solución Implementada

### 1. Spec File Optimizado: `historiador-clean.spec`

```python
# Exclusiones de herramientas de desarrollo
dev_tools_excludes = [
    'pytest', 'pylint', 'black', 'coverage', 'isort',
    'responses', 'freezegun', 'faker', 'pre_commit',
]

# Exclusiones adicionales para optimizar
optional_excludes = [
    'matplotlib', 'scipy', 'IPython', 'jupyter',
    'pandas.plotting._matplotlib', 'pandas.io.html',
    'pandas.io.sql', 'numpy.distutils', 'numpy.testing',
]

exe = EXE(
    # ...
    strip=True,    # Eliminar símbolos de debug
    upx=False,     # UPX compresión opcional
)
```

### 2. Configuración CI/CD

**GitHub Actions & GitLab CI** ahora usan:
```yaml
- pyinstaller historiador-clean.spec --clean
```

**Antes usaban**:
```yaml  
- pyinstaller --onefile --name historiador --add-data=".env.example:." src/main.py --clean
```

### 3. Actualización de .gitignore

```gitignore
# PyInstaller
*.spec
# Except our clean build spec
!historiador-clean.spec

# Testing (añadido coverage.xml)
coverage.xml
```

## Resultados

| Método de Build | Tamaño | Reducción |
|----------------|---------|-----------|
| **Original** (con dev tools) | 83MB | Baseline |
| **Comando con exclusiones** | 53MB | -36% |
| **Spec file optimizado** | **51MB** | **-39%** |

### Beneficios Obtenidos

1. **39% reducción de tamaño** - De 83MB → 51MB
2. **Funcionalidad completa mantenida** - Todos los comandos funcionan
3. **Build consistente** - Mismo resultado en local y CI/CD
4. **Configuración versionable** - Spec file trackeado en Git
5. **Mejor optimización** - Strip symbols + exclusiones extras

## Comandos de Build Disponibles

### Recomendado (51MB optimizado):
```bash
pyinstaller historiador-clean.spec --clean
```

### Alternativas:

**Comando directo (53MB)**:
```bash
pyinstaller --onefile --name historiador \
  --exclude-module pytest --exclude-module pylint --exclude-module black \
  --add-data=".env.example:." src/main.py --clean
```

**Completo con dev tools (83MB)**:
```bash
pyinstaller --onefile --name historiador --add-data=".env.example:." src/main.py --clean
```

## Verificación

```bash
# Generar y probar ejecutable optimizado
pyinstaller historiador-clean.spec --clean
./dist/historiador --help

# Verificar tamaño
du -sh dist/historiador
# Output: 51M dist/historiador
```

## Impacto en Pipelines

- **GitHub Actions**: Genera ejecutables 51MB (antes 83MB)
- **GitLab CI**: Genera ejecutables 51MB (antes 83MB)  
- **Build local**: Consistente con CI/CD

La optimización se aplica automáticamente en todos los entornos sin afectar la funcionalidad.