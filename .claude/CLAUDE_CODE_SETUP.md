# Claude Code - Configuración Avanzada y Troubleshooting

Esta documentación contiene todo lo aprendido sobre configuración avanzada de Claude Code, permisos, agentes y resolución de problemas para futuras sesiones.

## 📋 Índice

1. [Configuración de Permisos](#configuración-de-permisos)
2. [Hooks y Auto-aprobación](#hooks-y-auto-aprobación)
3. [Configuración de Agentes](#configuración-de-agentes)
4. [Troubleshooting](#troubleshooting)
5. [Comandos Útiles](#comandos-útiles)
6. [Lecciones Aprendidas](#lecciones-aprendidas)

---

## Configuración de Permisos

### Archivo de Configuración: `.claude/settings.json`

#### Formato Correcto de Wildcards
```json
{
  "permissions": {
    "allow": [
      "Bash(python -m pytest:*)",      // ✅ Correcto: usar :* para wildcards
      "Bash(python -m pylint:*)",      // ✅ Correcto: cubre cualquier parámetro
      "Python -m black:*",             // ✅ Correcto: formato sin Bash()
      "Dist/historiador.exe:*"         // ✅ Correcto: uppercase + wildcard
    ]
  }
}
```

#### Errores Comunes a Evitar
```json
// ❌ INCORRECTO: usar * sin :
"Bash(python -m pytest*)"

// ❌ INCORRECTO: lowercase en tool names
"python -m pytest:*"

// ❌ INCORRECTO: comentarios mal formateados
"# Comments with () cause errors"

// ✅ CORRECTO: formato adecuado
"Bash(python -m pytest:*)",
"Python -m pytest:*"
```

### Configuración Mínima Efectiva (50 reglas vs 120+ anteriores)

#### Wildcards Bash() - Comandos Python
- `Bash(python -m pylint:*)`
- `Bash(python -m pytest:*)`
- `Bash(python -m black:*)`
- `Bash(python -m isort:*)`
- `Bash(python -m mypy:*)`
- `Bash(python -m flake8:*)`
- `Bash(python -m PyInstaller:*)`
- `Bash(python -m bandit:*)`

#### Wildcards Bash() - Sistema
- `Bash(rm -rf:*)`
- `Bash(ls:*)`
- `Bash(dir:*)`
- `Bash(test:*)`
- `Bash(file:*)`
- `Bash(du:*)`
- `Bash(dist/historiador.exe:*)`

#### Wildcards Directos (sin Bash())
- `Python -m pytest:*`
- `Python -m black:*`
- `Python -m PyInstaller:*`
- `Dist/historiador.exe:*`

---

## Hooks y Auto-aprobación

### Hook de Auto-aprobación: `.claude/auto_approve.py`

```python
#!/usr/bin/env python3
"""Auto-approval hook for Claude Code development commands."""
import json
import sys

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        
        # Lista de comandos pre-aprobados para desarrollo
        approved_patterns = [
            "rm -rf dist/", "rm -rf build/",
            "python -m black", "python -m isort",
            "python -m pylint", "python -m pytest",
            "python -m PyInstaller", "dist/historiador",
            "ls", "pwd", "git status"
        ]
        
        for pattern in approved_patterns:
            if command.startswith(pattern):
                output = {
                    "permissionDecision": "allow",
                    "permissionDecisionReason": f"Auto-approved: {pattern}"
                }
                print(json.dumps(output))
                sys.exit(0)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Configuración de Hooks: `.claude/hooks.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/auto_approve.py"
          }
        ]
      }
    ]
  }
}
```

**Nota Importante**: Los hooks funcionan para comandos directos pero **NO para agentes**. Los agentes requieren configuración en `settings.json`.

---

## Configuración de Agentes

### Estructura de Agentes: `.claude/agents/*.md`

#### Formato de Agente con Validaciones Estrictas

```markdown
---
name: qa-analyzer
description: Comprehensive QA analysis with strict validation
tools: Bash, Glob, Grep, Read, TodoWrite, BashOutput, KillBash, Edit, MultiEdit, Write, NotebookEdit
model: sonnet
color: pink
---

**CRITICAL FAILURE CONDITIONS - ABORT ANALYSIS IF ANY OCCUR:**
- Build fails to generate executable (dist/historiador.exe does not exist)
- Executable does not respond to --help command
- Coverage falls below 80% threshold
- PyLint score falls below 8.0 threshold
- Any command requests user confirmation (configuration error)

**COMMAND EXECUTION PRIORITY:**
1. **Always use module format**: `python -m PyInstaller` (NOT `pyinstaller`)
2. **Set timeouts**: Use timeout=600000 (10 minutes) for PyInstaller
3. **Use exact file extensions**: `dist/historiador.exe` (NOT `dist/historiador`)
4. **NEVER ask for permission** - all commands are pre-approved

**CRITICAL COMMAND FORMATS:**
- Build cleanup: `Bash(rm -rf dist/ build/, timeout=30000)`
- PyInstaller: `Bash(python -m PyInstaller historiador-clean.spec --clean, timeout=600000)`
- Executable test: `Bash(dist/historiador.exe --help, timeout=30000)`
```

#### Configuración de Timeouts Críticos

Para comandos que toman tiempo (como PyInstaller):
- **Cleanup**: 30 segundos
- **PyInstaller**: 600 segundos (10 minutos) mínimo
- **Tests básicos**: 30-60 segundos

---

## Troubleshooting

### Comando `/doctor` - Diagnóstico de Configuración

```bash
/doctor
```

**Ejemplo de salida con errores**:
```
Invalid Settings
C:\path\to\.claude\settings.json
  └ permissions
    └ allow
      ├ "python -m pytest*": Tool names must start with uppercase. Use "Python -m pytest*"
      ├ "Bash(python -m pylint*)": Use ":*" for prefix matching, not just "*". Change to "Bash(python -m pylint:*)"
```

### Problemas Comunes y Soluciones

#### 1. Agentes Piden Confirmación
**Problema**: Agente solicita confirmación para comandos básicos
**Causa**: Permisos no configurados correctamente en `settings.json`
**Solución**: Agregar wildcards específicos y usar formato correcto

#### 2. PyInstaller Falla en Agentes
**Problema**: Build timeout o comando no encontrado
**Causa**: 
- Usar `pyinstaller` en lugar de `python -m PyInstaller`
- Timeout insuficiente (default 2 min vs necesario 10 min)
**Solución**: Configurar comando y timeout explícitamente

#### 3. Hooks No Funcionan con Agentes
**Problema**: Hooks funcionan para comandos directos pero no agentes
**Causa**: Agentes ejecutan en contexto diferente
**Solución**: Usar `settings.json` en lugar de hooks para agentes

#### 4. Wildcards No Funcionan
**Problema**: Wildcards no capturan comandos
**Causa**: Usar `*` en lugar de `:*` 
**Solución**: Formato correcto `"Bash(comando:*)"`

---

## Comandos Útiles

### Diagnóstico y Validación

```bash
# Diagnosticar configuración Claude Code
/doctor

# Verificar permisos configurados
cat .claude/settings.json | jq '.permissions.allow'

# Validar formato JSON
python -c "import json; json.load(open('.claude/settings.json'))"

# Test manual de comandos problémáticos
python -m black --check src/
python -m PyInstaller historiador-clean.spec --clean
```

### Limpieza y Build

```bash
# Limpieza completa
rm -rf dist/ build/ *.spec

# Build con timeout extendido
python -m PyInstaller historiador-clean.spec --clean

# Verificación del ejecutable
ls -la dist/
dist/historiador.exe --help
dist/historiador.exe test-connection
```

### QA y Testing

```bash
# QA completo manual
python -m black --check src/
python -m isort --check-only --diff src/
python -m pylint src/ --fail-under=8.0
python -m pytest tests/unit/ --cov=src --cov-fail-under=80
```

---

## Lecciones Aprendidas

### 1. Precedencia de Configuración
- **settings.json** > hooks para agentes
- **Wildcards** más efectivos que comandos específicos
- **Formato exacto** crítico según `/doctor`

### 2. Diferencias entre Contextos
- **Comandos directos**: Hooks + settings.json funcionan
- **Agentes**: Solo settings.json funciona
- **Timeouts**: Diferentes defaults entre contextos

### 3. Configuración Óptima
- **50 reglas bien formateadas** > 120+ reglas redundantes
- **Wildcards extensos** (`comando:*`) mejor que comandos específicos
- **Validaciones estrictas** en agentes previenen reportes parciales

### 4. Debugging Efectivo
- **`/doctor`** identifica errores de formato exactos
- **Pruebas directas** aíslan problemas de permisos
- **Logs de agentes** muestran comandos bloqueados específicos

### 5. Build y Deployment
- **`python -m PyInstaller`** más confiable que `pyinstaller`
- **Timeout 600s** mínimo para builds complejos
- **Verificación de archivos** crítica antes de ejecutar tests

---

## Configuración Recomendada para Nuevos Proyectos

### 1. Archivo `.claude/settings.json` Mínimo
```json
{
  "permissions": {
    "allow": [
      "Update(tests\\unit\\*)",
      "Bash(python -m pylint:*)",
      "Bash(python -m pytest:*)",
      "Bash(python -m black:*)",
      "Bash(python -m isort:*)",
      "Bash(python -m flake8:*)",
      "Bash(python -m pyinstaller:*)",
      "Bash(python -m PyInstaller:*)",
      "Bash(rm -rf:*)",
      "Bash(ls:*)",
      "Bash(dist/app:*)",
      "Python -m pytest:*",
      "Python -m black:*",
      "Python -m PyInstaller:*",
      "Dist/app:*"
    ],
    "deny": [],
    "ask": []
  }
}
```

### 2. Agente QA con Validaciones Estrictas
- Incluir criterios de fallo críticos
- Configurar timeouts apropiados
- Validar archivos antes de ejecutar
- Usar comandos de módulo (`python -m`)

### 3. Workflow de Validación
1. Ejecutar `/doctor` para verificar configuración
2. Probar comandos críticos manualmente
3. Ejecutar agentes con validación estricta
4. Documentar cualquier nuevo comando que requiera permisos

---

**Fecha de creación**: 2025-09-06  
**Última actualización**: 2025-09-06  
**Versión Claude Code**: 1.0.108  
**Proyecto**: Historiador (Python CLI con PyInstaller)