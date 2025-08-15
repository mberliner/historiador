"""Script de prueba detallada para modo dry-run con features."""
import sys
import os
from pathlib import Path

# Agregar el directorio padre al path
sys.path.append(str(Path(__file__).parent))

from src.config.settings import Settings
from src.services.jira_client import JiraClient
from src.services.file_processor import FileProcessor


def test_detailed_dry_run():
    """Prueba detallada del modo dry-run con features."""
    print("=== Test Detallado: Dry-Run con Features ===\n")
    
    # Configuracion de prueba
    settings = Settings(
        jira_url="https://test.atlassian.net",
        jira_email="test@test.com", 
        jira_api_token="test_token",
        project_key="TEST",
        dry_run=True,
        feature_issue_type="Feature"
    )
    
    # Crear instancias
    jira_client = JiraClient(settings)
    file_processor = FileProcessor()
    
    # Procesar archivo de prueba
    test_file = "entrada/test_errors.csv"
    if not os.path.exists(test_file):
        print(f"Error: Archivo de prueba no encontrado: {test_file}")
        return False
    
    print(f"Procesando archivo: {test_file}")
    print("-" * 50)
    
    # Procesar cada historia
    results = []
    for row_number, story in enumerate(file_processor.process_file(test_file), start=1):
        print(f"\nFILA {row_number}: {story.titulo}")
        print(f"   Descripcion: {story.descripcion[:50]}...")
        print(f"   Parent: {story.parent}")
        
        # Analizar que hara con el parent
        if story.parent:
            is_key = jira_client.feature_manager.is_jira_key(story.parent)
            normalized = jira_client.feature_manager._normalize_description(story.parent)
            print(f"   - Es key de Jira: {is_key}")
            if not is_key:
                print(f"   - Descripcion normalizada: '{normalized}'")
                print(f"   - Titulo generado: '{jira_client.feature_manager._generate_feature_title(story.parent)}'")
        else:
            print(f"   - Sin parent")
        
        # Procesar historia
        result = jira_client.create_user_story(story, row_number)
        results.append(result)
        
        # Mostrar resultado
        if result.success:
            print(f"   + Historia creada: {result.jira_key}")
            if result.feature_info:
                if result.feature_info.was_created:
                    print(f"      + Feature creada: {result.feature_info.feature_key}")
                else:
                    print(f"      = Feature reutilizada: {result.feature_info.feature_key}")
        else:
            print(f"   - Error: {result.error_message}")
    
    # Mostrar estadisticas del cache
    cache_stats = jira_client.feature_manager.get_cache_stats()
    print(f"\nESTADISTICAS DEL CACHE:")
    print(f"   Features cacheadas: {cache_stats['cached_features']}")
    for desc, key in cache_stats['features']:
        print(f"   * '{desc[:30]}...' -> {key}")
    
    # Resumen
    successful = sum(1 for r in results if r.success)
    print(f"\nRESUMEN:")
    print(f"   Total procesadas: {len(results)}")
    print(f"   Exitosas: {successful}")
    print(f"   Fallidas: {len(results) - successful}")
    
    return successful == len(results)


if __name__ == "__main__":
    success = test_detailed_dry_run()
    print(f"\nTest {'EXITOSO' if success else 'FALLIDO'}")
    sys.exit(0 if success else 1)