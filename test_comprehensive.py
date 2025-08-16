"""Test comprehensivo para ambos archivos de prueba."""
import sys
import os
from pathlib import Path

# Agregar el directorio padre al path
sys.path.append(str(Path(__file__).parent))

from src.config.settings import Settings
from src.services.jira_client import JiraClient
from src.services.file_processor import FileProcessor


def test_file(file_name, description):
    """Prueba un archivo específico."""
    print(f"=== {description} ===\n")
    
    settings = Settings(
        jira_url="https://test.atlassian.net",
        jira_email="test@test.com", 
        jira_api_token="test_token",
        project_key="TEST",
        dry_run=True,
        feature_issue_type="Feature"
    )
    
    jira_client = JiraClient(settings)
    file_processor = FileProcessor()
    
    test_file = f"entrada/{file_name}"
    if not os.path.exists(test_file):
        print(f"Error: Archivo {test_file} no encontrado")
        return False
    
    print(f"Procesando archivo: {test_file}")
    print("-" * 50)
    
    results = []
    for row_number, story in enumerate(file_processor.process_file(test_file), start=1):
        print(f"\nFILA {row_number}: {story.titulo}")
        print(f"   Parent: {story.parent}")
        
        if story.parent:
            is_key = jira_client.feature_manager.is_jira_key(story.parent)
            print(f"   - Es key de Jira: {is_key}")
            if not is_key:
                normalized = jira_client.feature_manager._normalize_description(story.parent)
                print(f"   - Descripcion normalizada: '{normalized}'")
        else:
            print("   - Sin parent")
        
        result = jira_client.create_user_story(story, row_number)
        results.append(result)
        
        if result.success:
            print(f"   + Historia creada: {result.jira_key}")
            if result.feature_info:
                if result.feature_info.was_created:
                    print(f"      + Feature creada: {result.feature_info.feature_key}")
                else:
                    print(f"      = Feature reutilizada: {result.feature_info.feature_key}")
        else:
            print(f"   - Error: {result.error_message}")
    
    successful = sum(1 for r in results if r.success)
    print(f"\nRESUMEN:")
    print(f"   Total procesadas: {len(results)}")
    print(f"   Exitosas: {successful}")
    print(f"   Fallidas: {len(results) - successful}")
    
    return successful == len(results)


def main():
    """Ejecuta tests para todos los archivos."""
    print("Test Comprehensivo de Features\n")
    
    test_cases = [
        ("test_features.csv", "Test con scenarios de features"),
        ("test_invalid_keys.csv", "Test con keys invalidas"),
        ("test_errors.csv", "Test de manejo de errores")
    ]
    
    results = []
    for file_name, description in test_cases:
        try:
            result = test_file(file_name, description)
            results.append(result)
            print(f"Test {file_name}: {'EXITOSO' if result else 'FALLIDO'}")
        except Exception as e:
            print(f"Error en {file_name}: {e}")
            results.append(False)
        
        print("\n" + "="*60 + "\n")
    
    passed = sum(results)
    total = len(results)
    
    print(f"RESUMEN FINAL:")
    print(f"Tests pasados: {passed}/{total}")
    
    if passed == total:
        print("Todos los tests pasaron!")
        return 0
    else:
        print("Algunos tests fallaron")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)