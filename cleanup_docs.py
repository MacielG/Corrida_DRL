#!/usr/bin/env python3
"""
Script para limpar e organizar documentação

Deleta arquivos de documentação duplicados e desnecessários
Move tudo para docs/ com estrutura organizada
"""

import os
import shutil
from pathlib import Path

# Raiz do projeto
ROOT = Path(__file__).parent

# Arquivos de documentation que devem ser DELETADOS (duplicatas)
FILES_TO_DELETE = [
    # Arquivos "Semanas" (antigos)
    "SEMANAS_COMPLETAS_FINALIZADAS.md",
    "STATUS_SEMANA_1.txt",
    "STATUS_FINAL_SEMANAS_2_3.txt",
    "STATUS_FINAL.txt",
    
    # Planos obsoletos
    "PLANO_ACAO.md",
    "PLANO_ACAO_IMEDIATO.md",
    "PLANO_SEMANA_1_COMPLETO.md",
    "PROXIMOS_PASSOS.md",
    "CHECKLIST_PROXIMAS_SEMANAS.md",
    
    # Resumos/Sumários duplicados
    "RESUMO_ANALISE_VISUAL.txt",
    "RESUMO_CORRECOES_NOVO.md",
    "RESUMO_EXECUTIVO.txt",
    "RESUMO_FINAL.txt",
    "RESUMO_MELHORIAS_EXECUTIVAS.md",
    "RESUMO_PLANO_ACAO.txt",
    "SUMARIO_CONSOLIDADO.txt",
    "SUMARIO_FINAL.txt",
    "SUMARIO_ORGANIZACAO.txt",
    
    # Outras documentações antigas
    "ANALISE_COMPLETA_PROJETO.md",
    "CONCLUSAO_ORGANIZACAO.md",
    "CORRECOES_FINAIS_APLICADAS.md",
    "CORRECOES_LOOP_E_FASES.md",
    "COMO_USAR_MAIN_REFATORADO.md",
    "FIX_RAPIDO_TESTES.md",
    "INDICE_DOCUMENTACAO.md",
    "INTERFACE_AGENTES_REFACTORACAO.md",
    "LEIA_PRIMEIRO.md",
    "LEIA_PRIMEIRO_MELHORIAS.txt",
    "MELHORIAS_APLICADAS.md",
    "METRICAS_TECNICAS.md",
    "ORGANIZACAO_DOCS.md",
    "ROADMAP_VISUAL.txt",
    "ROTEIRO_FINAL_VALIDACAO.md",
    "SOLUCAO_FINAL.md",
    "START_HERE.md",
    
    # Outros
    "FINAL_SUMMARY.txt",
    "BENCHMARKS.md",
]

# Arquivos TXT que podem ser deletados
TXT_TO_DELETE = [
    "00_COMECE_AQUI.txt",
    "00_LEIA_MELHORIAS.txt",
    "FINAL_SUMMARY.txt",
]

def delete_file(filepath):
    """Delete arquivo se existir"""
    if filepath.exists():
        try:
            filepath.unlink()
            print(f"[OK] Deletado: {filepath.name}")
            return True
        except Exception as e:
            print(f"[ERROR] Erro ao deletar {filepath.name}: {e}")
            return False
    return False

def main():
    print("=" * 60)
    print("LIMPEZA DE DOCUMENTACAO")
    print("=" * 60)
    
    deleted_count = 0
    
    # Deletar arquivos do raiz
    print("\n1. Deletando documentacao duplicada do raiz:")
    for filename in FILES_TO_DELETE:
        filepath = ROOT / filename
        if delete_file(filepath):
            deleted_count += 1
    
    print(f"\n[OK] Total deletado: {deleted_count} arquivos")
    
    print("\n" + "=" * 60)
    print("DOCUMENTACAO FINAL ORGANIZADA")
    print("=" * 60)
    
    print("\nEstrutura de documentacao:")
    docs_structure = """
    docs/
    00_INDEX.md                 [INDICE PRINCIPAL - comece aqui]
    QUICKSTART.md               [5 minutos para começar]
    TUTORIAL.md                 [Guia completo]
    API.md                      [Referencia tecnica]
    ARQUITETURA.md              [Design do sistema]
    REWARD_SHAPING.md           [Detalhes de rewards]
    LOOP_DETECTION.md           [Deteccao de loops]
    RACE_MANAGEMENT.md          [Gerenciamento]
    TESTES.md                   [Suite de testes]
    CI_CD.md                    [Automacao]

    evolution/                  [DESENVOLVIMENTO - 6 HORAS]
    README.md                 [Timeline completo]
    01_ARQUITETURA_BASE.md    [Horas 0-2]
    02_REWARD_SHAPING.md      [Horas 2-4]
    03_LOOP_DETECTION.md      [Horas 4-5]
    04_TESTES_E_VALIDACAO.md  [Horas 5-6a]
    05_CORRECOES_FINAIS.md    [Horas 5-6b]

    examples/                   [EXEMPLOS PRATICOS]
    """
    print(docs_structure)
    
    print("\n[OK] Limpeza concluida!")
    print("\nProximo passo: Leia docs/00_INDEX.md")

if __name__ == "__main__":
    main()
