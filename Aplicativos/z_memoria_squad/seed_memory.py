from kernel import SquadMemory
from pathlib import Path

def seed_from_rules():
    # Localiza o rules.md
    base_dir = Path(__file__).parent.parent.parent
    rules_path = base_dir / ".agents" / "rules.md"
    
    if not rules_path.exists():
        print(f"Erro: Arquivo {rules_path} não encontrado.")
        return

    with open(rules_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Divide o conteúdo em blocos (parágrafos ou seções) para melhor granularidade
    sections = content.split("##")
    
    mem = SquadMemory()
    print("Iniciando indexação vetorial...")

    for i, section in enumerate(sections):
        if not section.strip():
            continue
            
        clean_text = section.strip()
        metadata = {
            "source": "rules.md",
            "section_id": i,
            "type": "business_rule"
        }
        
        doc_id = f"rules_sec_{i}"
        mem.add_record(clean_text, metadata=metadata, doc_id=doc_id)
        print(f" -> Seção {i} indexada com sucesso.")

    print("\n[✓] Memória Vetorial alimentada com Protocolo Mestre!")

if __name__ == "__main__":
    seed_from_rules()
