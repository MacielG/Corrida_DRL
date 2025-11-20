#!/usr/bin/env python3
"""Script para aplicar correções de indentação no environment.py"""

import re

def fix_environment():
    with open('environment.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Garante que todas as linhas usam espaços (8 espaços = 1 nível de indentação)
    fixed_lines = []
    for i, line in enumerate(lines, 1):
        # Converte tabs para espaços
        if '\t' in line:
            line = line.replace('\t', '    ')
        fixed_lines.append(line)
    
    # Agora aplica as mudanças lógicas
    content = ''.join(fixed_lines)
    
    # 1. Adiciona anti-loop no __init__
    content = content.replace(
        '         self.randomize_checkpoint = False  # Garante que sempre existe\n         \n         # Carrega stats do agente',
        '''         self.randomize_checkpoint = False  # Garante que sempre existe
         
         # NOVO: Mecanismos anti-loop
         self.position_history = []  # Track das últimas posições
         self.progress_counter = 0  # Contador de steps sem progresso
         self.max_steps_without_progress = 200  # Falha após ~20s
         self.min_progress_distance = 5 * ENV_SCALE  # Mínimo deslocamento
         
         # Carrega stats do agente'''
    )
    
    # 2. Reset no método reset()
    content = content.replace(
        '         self.current_step = 0\n         self.episode_time = 0.0\n         self.prev_dist_to_checkpoint = None\n         self.prev_angle = None',
        '''         self.current_step = 0
         self.episode_time = 0.0
         self.prev_dist_to_checkpoint = None
         # NOVO: Reset anti-loop
         self.position_history = []
         self.progress_counter = 0
         self.prev_angle = None'''
    )
    
    # 3. Penalidade por não movimento
    content = content.replace(
        '''             if dist_moved > 0.05 and self.checkpoints:
                 reward += 0.2  # Bônus maior por movimento
             if self.checkpoints:''',
        '''             if dist_moved > 0.05 and self.checkpoints:
                 reward += 0.2  # Bônus maior por movimento
             elif dist_moved < 0.01 and self.car1_speed < 0.1:
                 reward -= 0.3  # Penalidade por não movimento
             if self.checkpoints:'''
    )
    
    # 4. Adiciona detecção de loop
    content = content.replace(
        '''         if self.episode_time >= MAX_EPISODE_TIME:
             done = True
         if self.current_step >= self.max_steps:
             done = True''',
        '''         # NOVO: Detecção de loop/inatividade
         if self.current_step % 10 == 0:
             self.position_history.append(self.car1_pos.copy())
             if len(self.position_history) > 20:
                 self.position_history.pop(0)
         
         if len(self.position_history) >= 2:
             total_distance = 0
             for i in range(1, len(self.position_history)):
                 dist = np.linalg.norm(np.array(self.position_history[i]) - np.array(self.position_history[i-1]))
                 total_distance += dist
             
             if total_distance < self.min_progress_distance:
                 self.progress_counter += 1
                 reward -= 0.1
             else:
                 self.progress_counter = 0
         
         if self.progress_counter > self.max_steps_without_progress:
             reward -= 10.0
             done = True
             print(f"[FAIL] Agente em loop por {self.progress_counter} steps")

         if self.episode_time >= MAX_EPISODE_TIME:
             done = True
         if self.current_step >= self.max_steps:
             done = True'''
    )
    
    # 5. Adiciona progress ao info dict
    content = content.replace(
        'info = {"collisions": collisions, "episode_time": self.episode_time, "checkpoint": self.checkpoint_index, "penalty": penalty, "success": success}',
        'info = {"collisions": collisions, "episode_time": self.episode_time, "checkpoint": self.checkpoint_index, "penalty": penalty, "success": success, "progress": self.progress_counter}'
    )
    
    # Escreve o arquivo corrigido
    with open('environment.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] Mudancas aplicadas com sucesso!")

if __name__ == '__main__':
    fix_environment()
