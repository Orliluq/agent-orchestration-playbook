"""
Storage layer for agent orchestration.
Abstrae el almacenamiento persistente para desacoplar la lógica de negocio.
"""
import asyncio
import json
import aiofiles
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class StorageError(Exception):
    """Error en operaciones de almacenamiento"""
    pass

class FileStorage:
    """Almacenamiento basado en archivos con soporte async"""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    async def save(self, data: Dict[str, Any], collection: str = "default") -> str:
        """Guardar datos con timestamp y ID único"""
        try:
            timestamp = datetime.now().isoformat()
            record_id = f"{timestamp}_{hash(str(data))}"
            file_path = self.base_path / collection / f"{record_id}.json"
            
            file_path.parent.mkdir(exist_ok=True)
            
            record = {
                "id": record_id,
                "timestamp": timestamp,
                "data": data
            }
            
            # Escritura atómica
            temp_path = file_path.with_suffix(".tmp")
            async with aiofiles.open(temp_path, 'w') as f:
                await f.write(json.dumps(record, indent=2, ensure_ascii=False))
            
            temp_path.rename(file_path)
            return record_id
            
        except Exception as e:
            raise StorageError(f"Failed to save record: {e}")
    
    async def get(self, record_id: str, collection: str = "default") -> Optional[Dict[str, Any]]:
        """Recuperar un registro específico"""
        try:
            file_path = self.base_path / collection / f"{record_id}.json"
            if not file_path.exists():
                return None
                
            async with asyncio.aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                return json.loads(content)
                
        except Exception as e:
            raise StorageError(f"Failed to get record {record_id}: {e}")
    
    async def list(self, collection: str = "default", limit: int = 100) -> List[Dict[str, Any]]:
        """Listar registros con paginación"""
        try:
            collection_path = self.base_path / collection
            if not collection_path.exists():
                return []
            
            records = []
            for file_path in sorted(collection_path.glob("*.json"))[:limit]:
                async with asyncio.aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    records.append(json.loads(content))
            
            return records
            
        except Exception as e:
            raise StorageError(f"Failed to list records: {e}")
    
    async def delete(self, record_id: str, collection: str = "default") -> bool:
        """Eliminar un registro"""
        try:
            file_path = self.base_path / collection / f"{record_id}.json"
            if file_path.exists():
                file_path.unlink()
                return True
            return False
            
        except Exception as e:
            raise StorageError(f"Failed to delete record {record_id}: {e}")

class MemoryStorage:
    """Almacenamiento en memoria para pruebas y desarrollo"""
    
    def __init__(self):
        self._data: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    
    async def save(self, data: Dict[str, Any], collection: str = "default") -> str:
        """Guardar en memoria"""
        if collection not in self._data:
            self._data[collection] = []
        
        timestamp = datetime.now().isoformat()
        record_id = f"{timestamp}_{hash(str(data))}"
        
        record = {
            "id": record_id,
            "timestamp": timestamp,
            "data": data
        }
        
        self._data[collection].append(record)
        return record_id
    
    async def get(self, record_id: str, collection: str = "default") -> Optional[Dict[str, Any]]:
        """Recuperar de memoria"""
        if collection not in self._data:
            return None
        
        for record in self._data[collection]:
            if record["id"] == record_id:
                return record
        return None
    
    async def list(self, collection: str = "default", limit: int = 100) -> List[Dict[str, Any]]:
        """Listar de memoria"""
        if collection not in self._data:
            return []
        
        return self._data[collection][-limit:]
    
    async def delete(self, record_id: str, collection: str = "default") -> bool:
        """Eliminar de memoria"""
        if collection not in self._data:
            return False
        
        for i, record in enumerate(self._data[collection]):
            if record["id"] == record_id:
                del self._data[collection][i]
                return True
        return False
