#!/usr/bin/env python3
"""
Script pour corriger l'erreur de timezone dans dynamic_route_manager.py
"""

import os
import sys

def fix_timezone_error():
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    file_path = os.path.join(backend_path, 'app', 'services', 'dynamic_route_manager.py')
    
    print(f"🔧 Correction de l'erreur timezone dans: {file_path}")
    
    # Lire le fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer les lignes problématiques
    replacements = [
        (
            "days_since_last_deal = (datetime.now() - last_deal[0]).days",
            "# Gérer les datetimes avec/sans timezone\n            if last_deal[0].tzinfo is not None:\n                # Si la date a un timezone, utiliser UTC\n                from datetime import timezone\n                current_time = datetime.now(timezone.utc)\n            else:\n                # Sinon, utiliser datetime sans timezone\n                current_time = datetime.now()\n            days_since_last_deal = (current_time - last_deal[0]).days"
        ),
        (
            "thirty_days_ago = datetime.now() - timedelta(days=30)",
            "# Utiliser la même timezone que la base de données\n        from datetime import timezone\n        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30) if hasattr(datetime.now(), 'tzinfo') else datetime.now() - timedelta(days=30)"
        ),
        (
            "seven_days_ago = datetime.now() - timedelta(days=7)",
            "# Utiliser la même timezone que la base de données\n        from datetime import timezone\n        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7) if hasattr(datetime.now(), 'tzinfo') else datetime.now() - timedelta(days=7)"
        )
    ]
    
    # Appliquer les corrections
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"✅ Corrigé: {old[:50]}...")
    
    # Ajouter l'import timezone au début si nécessaire
    if "from datetime import timezone" not in content:
        # Trouver la ligne d'import datetime
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "from datetime import" in line and "timezone" not in line:
                lines[i] = line.rstrip() + ", timezone"
                break
        content = '\n'.join(lines)
    
    # Sauvegarder
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Corrections appliquées!")
    
    # Solution alternative plus simple
    print("\n💡 Solution alternative rapide:")
    print("Remplacez toutes les occurrences de 'datetime.now()' par 'datetime.utcnow()' dans dynamic_route_manager.py")

if __name__ == "__main__":
    fix_timezone_error()