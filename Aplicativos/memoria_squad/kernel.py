import chromadb
from chromadb.config import Settings
import os
from pathlib import Path
from datetime import datetime

class SquadMemory:
    def __init__(self, persist_directory: str = None):
        if persist_directory is None:
            # Define o caminho padrão na pasta .agents/memory
            base_dir = Path(__file__).parent.parent.parent
            self.persist_dir = str(base_dir / ".agents" / "memory_db")
        else:
            self.persist_dir = persist_directory
            
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Cliente persistente
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        
        # Coleção principal
        self.collection = self.client.get_or_create_collection(
            name="squad_knowledge",
            metadata={"hnsw:space": "cosine"} # Similaridade por cosseno
        )

    def add_record(self, text: str, metadata: dict = None, doc_id: str = None):
        """Adiciona um registro de conhecimento à memória."""
        if doc_id is None:
            doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )
        return doc_id

    def query(self, question: str, n_results: int = 3):
        """Busca os registros mais semanticamente próximos da pergunta."""
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results
        )
        return results

if __name__ == "__main__":
    # Teste rápido de inicialização
    mem = SquadMemory()
    print(f"Memória inicializada em: {mem.persist_dir}")
