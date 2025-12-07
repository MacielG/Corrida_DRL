#!/usr/bin/env python3
"""
Script para limpar e organizar arquivos .txt
Move importantes para docs/, deleta obsoletos
"""

import os
from pathlib import Path

ROOT = Path(__file__).parent

# Arquivos .txt IMPORTANTES (manter)
IMPORTANT_TXT = {
    "00_RESULTADO_FINAL.txt",      # Principal - resultado
    "00_COMECE_AQUI_AGORA.txt",    # Principal - guia rapido
    "requirements.txt",             # Essencial - dependencias
}

# Arquivos .txt a DELETAR (duplicatas/obsoletos)
TXT_TO_DELETE = [
    "TREE_FINAL.txt",              # Duplicado - ja em docs
    "SUMMARY_FINAL.txt",           # Duplicado - ja consolidado
    "README_LIMPEZA.txt",          # Obsoleto
    "ORGANIZACAO_FINAL_RESUMO.txt",# Obsoleto
    "LIMPEZA_COMPLETADA.txt",      # Obsoleto
    "test_output.txt",             # Arquivo de teste
    "00_LEIA_TUDO_FINALIZADO.txt", # Obsoleto - substituido por novo
    "00_LEIA_MELHORIAS.txt",       # Obsoleto
    "00_COMECE_AQUI.txt",          # Duplicado (ja tem _AGORA)
]

# Mapear arquivos para docs/
TXT_TO_DOCS = {
    "00_RESULTADO_FINAL.txt": "docs/RESULTADO.txt",
    "00_COMECE_AQUI_AGORA.txt": "docs/START.txt",
    "requirements.txt": "requirements.txt",  # Manter no raiz
}

def delete_file(filepath):
    """Delete arquivo se existir"""
    if filepath.exists():
        try:
            filepath.unlink()
            print(f"[DEL] {filepath.name}")
            return True
        except Exception as e:
            print(f"[ERR] {filepath.name}: {e}")
            return False
    return False

def move_file(src, dst):
    """Move arquivo"""
    if src.exists():
        try:
            # Ler conteudo
            content = src.read_text(encoding='utf-8')
            # Escrever no destino
            Path(dst).write_text(content, encoding='utf-8')
            # Deletar original
            src.unlink()
            print(f"[MOV] {src.name} -> {Path(dst).name}")
            return True
        except Exception as e:
            print(f"[ERR] Erro ao mover: {e}")
            return False
    return False

def main():
    print("=" * 60)
    print("LIMPEZA E ORGANIZACAO DE ARQUIVOS .txt")
    print("=" * 60)
    
    print("\n1. Deletando duplicatas e obsoletos:")
    deleted = 0
    for filename in TXT_TO_DELETE:
        if delete_file(ROOT / filename):
            deleted += 1
    print(f"   Total: {deleted} deletados")
    
    print("\n2. Movendo importante para docs/:")
    moved = 0
    for src, dst in TXT_TO_DOCS.items():
        if src != "requirements.txt":  # requirements fica no raiz
            if move_file(ROOT / src, ROOT / dst):
                moved += 1
    print(f"   Total: {moved} movidos")
    
    print("\n3. Mantendo essenciais no raiz:")
    kept = []
    for txt in IMPORTANT_TXT:
        filepath = ROOT / txt
        if filepath.exists():
            kept.append(txt)
            print(f"   [OK] {txt}")
    print(f"   Total: {len(kept)} mantidos")
    
    print("\n" + "=" * 60)
    print("ESTRUTURA FINAL DE .txt")
    print("=" * 60)
    
    print("\nNo raiz (essenciais):")
    print("  - requirements.txt")
    
    print("\nEm docs/:")
    print("  - START.txt          (Como comecar)")
    print("  - RESULTADO.txt      (Resultado final)")
    
    print("\nEm logs/:")
    print("  - Logs automaticos de sessoes")
    
    print("\n" + "=" * 60)
    print("[OK] Limpeza de .txt concluida!")
    print("=" * 60)

if __name__ == "__main__":
    main()
