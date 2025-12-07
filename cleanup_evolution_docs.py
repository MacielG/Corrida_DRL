#!/usr/bin/env python3
"""
Script para limpar docs/evolution de documentacao obsoleta
Mantém apenas os 5 arquivos principais + README.md
"""

import os
from pathlib import Path

ROOT = Path(__file__).parent / "docs" / "evolution"

# Arquivos que devem ser MANTIDOS
FILES_TO_KEEP = {
    "README.md",
    "01_ARQUITETURA_BASE.md",
    "02_REWARD_SHAPING.md",
    "03_LOOP_DETECTION.md",
    "04_TESTES_E_VALIDACAO.md",
    "05_CORRECOES_FINAIS.md",
}

# Arquivos que devem ser DELETADOS
FILES_TO_DELETE = [
    "ARQUITETURA_RL_CIENTIFICA.md",
    "CHECKLIST_V2.md",
    "CORRECOES_APLICADAS.md",
    "CORRECOES_CRITICAS_v2.1.md",
    "CORRECOES_FLUXO_E_VISUAL.md",
    "ERROS_ENCONTRADOS.md",
    "GAMIFICACAO_MUDANCAS.md",
    "GAMIFICACAO_README.md",
    "GUIA_FLUXO_AGENTES.md",
    "GUIA_RAPIDO_V2.md",
    "IMPLEMENTACAO_COMPLETA.md",
    "IMPLEMENTACAO_GAMIFICACAO_v2.1.md",
    "IMPLEMENTACAO_RESUMO.md",
    "INDEX_GAMIFICACAO_v2.1.md",
    "README_ATUALIZACOES.md",
    "RESUMO_CORRECOES_FINAIS.md",
    "RESUMO_IMPLEMENTACAO.md",
    "SUMARIO_FINAL_v2.1.md",
    "VALIDACAO_GAMIFICACAO.md",
]

def delete_file(filepath):
    """Delete arquivo se existir"""
    if filepath.exists():
        try:
            filepath.unlink()
            print(f"[OK] Deletado: {filepath.name}")
            return True
        except Exception as e:
            print(f"[ERROR] Erro: {e}")
            return False
    return False

def main():
    print("=" * 60)
    print("LIMPEZA DE docs/evolution/")
    print("=" * 60)
    
    deleted_count = 0
    
    print("\nDeletando arquivos obsoletos:")
    for filename in FILES_TO_DELETE:
        filepath = ROOT / filename
        if delete_file(filepath):
            deleted_count += 1
    
    print(f"\n[OK] Total deletado: {deleted_count} arquivos")
    
    print("\n" + "=" * 60)
    print("MANTIDO EM docs/evolution/")
    print("=" * 60)
    
    kept_count = 0
    print("\nArquivos mantidos:")
    for filename in sorted(FILES_TO_KEEP):
        filepath = ROOT / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"[OK] {filename:<35} ({size:,} bytes)")
            kept_count += 1
    
    print(f"\n[OK] Total mantido: {kept_count} arquivos")
    
    print("\n" + "=" * 60)
    print("[OK] Limpeza concluida!")
    print("=" * 60)

if __name__ == "__main__":
    main()
