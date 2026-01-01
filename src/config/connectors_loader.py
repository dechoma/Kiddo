"""Load connectors from YAML configuration file."""

import os
import yaml
from pathlib import Path
from typing import List, Dict


def load_connectors_from_file(connectors_file: str = None) -> List[Dict]:
    """Load all connectors from connectors.yaml file."""
    if connectors_file is None:
        connectors_file = os.getenv("CONNECTORS_CONFIG_PATH", "connectors.yaml")
    
    connectors_path = Path(connectors_file)
    
    if not connectors_path.exists():
        return []
    
    try:
        with open(connectors_path, 'r', encoding='utf-8') as f:
            connectors_data = yaml.safe_load(f) or {}
        
        all_connectors = []
        
        # Load all connector types
        connector_types = [
            'gmail_connectors',
            'api_connectors',
            'webhook_connectors',
            'file_connectors',
            'database_connectors'
        ]
        
        for connector_type in connector_types:
            type_name = connector_type.replace('_connectors', '')
            for connector_def in connectors_data.get(connector_type, []):
                connector_def['type'] = type_name
                all_connectors.append(connector_def)
        
        return all_connectors
    except Exception as e:
        print(f"Warning: Could not load connectors config from {connectors_path}: {e}")
        return []

