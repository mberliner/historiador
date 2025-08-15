"""Script de pruebas para el FeatureManager."""
import sys
from pathlib import Path

# Agregar el directorio padre al path
sys.path.append(str(Path(__file__).parent))

from src.services.feature_manager import FeatureManager
from src.config.settings import Settings
import requests


def test_jira_key_detection():
    """Prueba la detección de keys de Jira vs descripciones."""
    print("=== Test: Detección de Keys vs Descripciones ===")
    
    # Mock settings y session
    settings = Settings(
        jira_url="https://test.atlassian.net",
        jira_email="test@test.com", 
        jira_api_token="token",
        project_key="TEST"
    )
    session = requests.Session()
    
    manager = FeatureManager(settings, session)
    
    test_cases = [
        ("PROJ-123", True),
        ("TEST-456", True), 
        ("AB-1", True),
        ("LONGKEY-999", True),
        ("proj-123", False),  # minúsculas
        ("PROJ123", False),   # sin guión
        ("PROJ-", False),     # sin número
        ("123-PROJ", False),  # orden incorrecto
        ("Implementar sistema de autenticación", False),
        ("", False),
        (None, False),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for text, expected in test_cases:
        result = manager.is_jira_key(text)
        status = "OK" if result == expected else "FAIL"
        print(f"{status} '{text}' -> {result} (esperado: {expected})")
        if result == expected:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    return passed == total


def test_normalization():
    """Prueba la normalización de descripciones."""
    print("\n=== Test: Normalización de Descripciones ===")
    
    settings = Settings(
        jira_url="https://test.atlassian.net",
        jira_email="test@test.com", 
        jira_api_token="token",
        project_key="TEST"
    )
    session = requests.Session()
    
    manager = FeatureManager(settings, session)
    
    test_cases = [
        ("Implementar sistema de autenticacion", "implementar sistema de autenticacion"),
        ("  Espacios   multiples  ", "espacios multiples"),
        ("MAYUSCULAS y minusculas", "mayusculas y minusculas"),
        ("Puntuacion... final!!!", "puntuacion final"),
        ("Caracteres-especiales@#$", "caracteres-especiales"),
        ("", ""),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for original, expected in test_cases:
        result = manager._normalize_description(original)
        status = "OK" if result == expected else "FAIL"
        print(f"{status} '{original}' -> '{result}' (esperado: '{expected}')")
        if result == expected:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    return passed == total


def test_title_generation():
    """Prueba la generación de títulos para features."""
    print("\n=== Test: Generación de Títulos ===")
    
    settings = Settings(
        jira_url="https://test.atlassian.net",
        jira_email="test@test.com", 
        jira_api_token="token",
        project_key="TEST"
    )
    session = requests.Session()
    
    manager = FeatureManager(settings, session)
    
    test_cases = [
        ("Texto corto", "Texto corto"),
        ("Este es un texto más largo que debería ser cortado porque excede el límite", "Este es un texto más largo que debería ser cortado..."),
        ("", "Feature sin título"),
        ("Una sola palabra superlargaquedeberíasercortada", "Una sola palabra superlargaquedeberíasercortada..."),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for description, expected_pattern in test_cases:
        result = manager._generate_feature_title(description)
        # Verificar que el resultado contenga elementos esperados
        if expected_pattern == "Feature sin título":
            matches = result == expected_pattern
        elif "..." in expected_pattern:
            matches = len(result) <= 63 and result.endswith("...")
        else:
            matches = result == expected_pattern
            
        status = "OK" if matches else "FAIL"
        print(f"{status} '{description}' -> '{result}'")
        if matches:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    return passed == total


def main():
    """Ejecuta todas las pruebas."""
    print("Iniciando pruebas del FeatureManager\n")
    
    tests = [
        test_jira_key_detection,
        test_normalization, 
        test_title_generation,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"Error en {test.__name__}: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'='*50}")
    print(f"RESUMEN FINAL: {passed}/{total} conjuntos de pruebas pasaron")
    
    if passed == total:
        print("Todas las pruebas pasaron!")
        return 0
    else:
        print("Algunas pruebas fallaron")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)