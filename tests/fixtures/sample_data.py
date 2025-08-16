"""Sample data for testing."""
import tempfile
import csv
from pathlib import Path
from typing import List, Dict, Any

# Sample user stories for testing
SAMPLE_STORIES = [
    {
        "titulo": "Login de usuario",
        "descripcion": "Como usuario quiero poder autenticarme en el sistema",
        "criterio_aceptacion": "Usuario puede loguearse con credenciales válidas;Error visible con credenciales inválidas",
        "subtareas": "Crear formulario de login;Validar credenciales;Mostrar errores",
        "parent": "DEMO-100"
    },
    {
        "titulo": "Dashboard principal", 
        "descripcion": "Como usuario autenticado quiero ver mi dashboard",
        "criterio_aceptacion": "Dashboard carga en menos de 3 segundos;Datos están actualizados",
        "subtareas": "Crear componente dashboard;Conectar con API;Optimizar performance",
        "parent": "Sistema de Gestión de Usuarios"
    },
    {
        "titulo": "Historia sin subtareas",
        "descripcion": "Una historia simple sin subtareas",
        "criterio_aceptacion": "Criterio simple",
        "subtareas": None,
        "parent": None
    }
]

# Invalid stories for error testing
INVALID_STORIES = [
    {
        "titulo": "",  # Empty title
        "descripcion": "Descripción válida",
        "criterio_aceptacion": "Criterio válido",
        "subtareas": None,
        "parent": None
    },
    {
        "titulo": "Título muy largo que excede los 255 caracteres permitidos para validación " + "x" * 200,
        "descripcion": "Descripción válida", 
        "criterio_aceptacion": "Criterio válido",
        "subtareas": None,
        "parent": None
    },
    {
        "titulo": "Título válido",
        "descripcion": "",  # Empty description
        "criterio_aceptacion": "Criterio válido",
        "subtareas": None,
        "parent": None
    }
]

def create_sample_csv(stories: List[Dict[str, Any]], file_path: str = None) -> str:
    """Create a sample CSV file with given stories."""
    if file_path is None:
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        file_path = temp_file.name
        temp_file.close()
    
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['titulo', 'descripcion', 'criterio_aceptacion', 'subtareas', 'parent']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for story in stories:
            writer.writerow(story)
    
    return file_path

def create_sample_excel(stories: List[Dict[str, Any]], file_path: str = None) -> str:
    """Create a sample Excel file with given stories."""
    import pandas as pd
    
    if file_path is None:
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False)
        file_path = temp_file.name
        temp_file.close()
    
    df = pd.DataFrame(stories)
    df.to_excel(file_path, index=False)
    
    return file_path

def create_invalid_file(file_path: str = None) -> str:
    """Create a file with invalid format."""
    if file_path is None:
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        file_path = temp_file.name
        temp_file.close()
    
    with open(file_path, 'w') as f:
        f.write("This is not a CSV or Excel file")
    
    return file_path