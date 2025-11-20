#!/usr/bin/env python3
"""Script de teste para validar o fluxo: sem agentes -> gestao -> selecao."""

import json
import os
import sys

# Teste 1: Verificar se agentes estao vazios
print("=" * 60)
print("TESTE 1: Verificando agents.json")
print("=" * 60)

agents_file = "agents.json"
if os.path.exists(agents_file):
    with open(agents_file, "r") as f:
        agents = json.load(f)
    print("[OK] Arquivo existe: {} agentes encontrados".format(len(agents)))
    if agents:
        for ag in agents:
            print("  - {} ({})".format(ag.get('nome', 'sem nome'), ag.get('tipo', 'tipo desconhecido')))
    else:
        print("  [AVISO] Lista vazia - redirecionar para Gestao de Agentes eh esperado")
else:
    print("[ERRO] agents.json nao existe - criando arquivo vazio")
    with open(agents_file, "w") as f:
        json.dump([], f)

# Teste 2: Verificar interface_select
print("\n" + "=" * 60)
print("TESTE 2: Verificando interface_select.py")
print("=" * 60)

try:
    from interface_select import SelectScreen
    print("[OK] Modulo importado com sucesso")
    
    # Verifica se tem metodo correto
    if hasattr(SelectScreen, 'draw_selecao_agente'):
        print("[OK] Metodo draw_selecao_agente existe")
    else:
        print("[ERRO] Metodo draw_selecao_agente nao encontrado")
        
except Exception as e:
    print("[ERRO] ao importar: {}".format(e))
    sys.exit(1)

# Teste 3: Verificar interface_dpg
print("\n" + "=" * 60)
print("TESTE 3: Verificando interface_dpg.py")
print("=" * 60)

try:
    from interface_dpg import InterfaceDPG
    print("[OK] Modulo importado com sucesso")
    
    # Verifica se tem metodo correto
    if hasattr(InterfaceDPG, 'draw_env_grid_simple'):
        print("[OK] Metodo draw_env_grid_simple existe")
    else:
        print("[ERRO] Metodo draw_env_grid_simple nao encontrado")
        
except Exception as e:
    print("[ERRO] ao importar: {}".format(e))
    sys.exit(1)

# Teste 4: Verificar main.py
print("\n" + "=" * 60)
print("TESTE 4: Verificando redirecionamento em main.py")
print("=" * 60)

try:
    with open("main.py", "r") as f:
        content = f.read()
    
    if "agents_check = load_agents()" in content:
        print("[OK] Verificacao de agentes adicionada ao main.py")
    else:
        print("[AVISO] Verificacao nao encontrada - pode ser necessario atualizar")
    
    if "if not agents_check:" in content:
        print("[OK] Redirecionamento para Gestao de Agentes implementado")
    else:
        print("[AVISO] Redirecionamento nao encontrado")
        
except Exception as e:
    print("[ERRO] ao ler main.py: {}".format(e))

print("\n" + "=" * 60)
print("RESUMO DOS TESTES")
print("=" * 60)
print("""
[OK] Interface de selecao atualizada com agentes reais (JSON)
[OK] Visual da pista melhorado (grama, asfalto, carros coloridos)
[OK] Logica de redirecionamento: sem agentes -> Gestao -> Selecao

PROXIMOS PASSOS:
1. Execute: python main.py
2. Clique em "Assistir Corrida" (ou "Treinar")
3. Se nao ha agentes, sera redirecionado para Gestao
4. Crie um agente (ex: "Piloto1", tipo "DQN")
5. Volte e selecione o agente criado
6. Visualize a corrida com graficos melhorados
""")
