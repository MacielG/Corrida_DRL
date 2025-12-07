"""Loop detector usando FFT para detectar movimentos circulares/repetitivos."""

import numpy as np
from scipy import signal
from typing import List, Tuple


class LoopDetector:
    """Detecta loops ou padrões repetitivos na trajetória do agente."""
    
    def __init__(self, history_size: int = 100, threshold: float = 0.7):
        """Inicializa detector de loops.
        
        Args:
            history_size: Número de posições a manter no histórico.
            threshold: Threshold de correlação para detectar loop (0-1).
        """
        self.history_size = history_size
        self.threshold = threshold
        self.position_history = []
        self.loop_count = 0
        
    def add_position(self, position: Tuple[float, float]) -> None:
        """Adiciona uma nova posição ao histórico.
        
        Args:
            position: Tupla (x, y) da posição.
        """
        self.position_history.append(position)
        if len(self.position_history) > self.history_size:
            self.position_history.pop(0)
    
    def detect_loop_fft(self) -> bool:
        """Detecta loop usando FFT no histórico de posições.
        
        Returns:
            bool: True se detectado um padrão repetitivo.
        """
        if len(self.position_history) < 20:
            return False
        
        # Extrai componentes X e Y
        x_coords = np.array([pos[0] for pos in self.position_history])
        y_coords = np.array([pos[1] for pos in self.position_history])
        
        # Normaliza
        x_coords = (x_coords - np.mean(x_coords)) / (np.std(x_coords) + 1e-8)
        y_coords = (y_coords - np.mean(y_coords)) / (np.std(y_coords) + 1e-8)
        
        # FFT dos dados
        fft_x = np.abs(np.fft.fft(x_coords))
        fft_y = np.abs(np.fft.fft(y_coords))
        
        # Detecta picos na FFT (indicam frequências dominantes = loops)
        # CORREÇÃO: Excluir índice 0 (DC component) do cálculo de threshold
        peak_threshold = np.mean([np.max(fft_x[1:]), np.max(fft_y[1:])]) * 0.5
        peaks_x = np.sum(fft_x[1:-1] > peak_threshold)  # Ignora DC
        peaks_y = np.sum(fft_y[1:-1] > peak_threshold)
        
        # Se muitos picos, indica padrão repetitivo
        return (peaks_x > 3 or peaks_y > 3)
    
    def detect_loop_correlation(self) -> bool:
        """Detecta loop usando auto-correlação.
        
        Returns:
            bool: True se detectado padrão repetitivo.
        """
        if len(self.position_history) < 30:
            return False
        
        x_coords = np.array([pos[0] for pos in self.position_history])
        y_coords = np.array([pos[1] for pos in self.position_history])
        
        # Normaliza
        x_coords = (x_coords - np.mean(x_coords)) / (np.std(x_coords) + 1e-8)
        y_coords = (y_coords - np.mean(y_coords)) / (np.std(y_coords) + 1e-8)
        
        # Auto-correlação
        acf_x = np.correlate(x_coords, x_coords, mode='full')
        acf_y = np.correlate(y_coords, y_coords, mode='full')
        
        acf_x = acf_x / np.max(np.abs(acf_x))
        acf_y = acf_y / np.max(np.abs(acf_y))
        
        # Procura por correlação forte em lags != 0
        center = len(acf_x) // 2
        half = len(acf_x) // 4
        
        # Se há picos secundários fortes, há padrão repetitivo
        peaks_secondary = np.sum(np.abs(acf_x[center-half:center-5]) > self.threshold)
        peaks_secondary += np.sum(np.abs(acf_y[center-half:center-5]) > self.threshold)
        
        return peaks_secondary > 2
    
    def detect_loop_distance(self) -> bool:
        """Detecta loop verificando se está revisitando áreas.
        
        Returns:
            bool: True se detectado movimento circular.
        """
        if len(self.position_history) < 30:
            return False
        
        # Calcula distância total percorrida
        total_distance = 0.0
        for i in range(1, len(self.position_history)):
            dx = self.position_history[i][0] - self.position_history[i-1][0]
            dy = self.position_history[i][1] - self.position_history[i-1][1]
            total_distance += np.sqrt(dx**2 + dy**2)
        
        # Calcula distância em linha reta (primeiro para último)
        dx_end = self.position_history[-1][0] - self.position_history[0][0]
        dy_end = self.position_history[-1][1] - self.position_history[0][1]
        straight_distance = np.sqrt(dx_end**2 + dy_end**2)
        
        # Ratio: se viajou muito para estar perto do start, é loop
        if total_distance < 1e-6:
            return False
        
        ratio = straight_distance / total_distance
        # Se ratio é muito pequeno, foi em círculo
        return ratio < 0.1
    
    def detect_loop(self, position_history: List[Tuple[float, float]] = None) -> bool:
        """Detecta loop usando múltiplos métodos.
        
        Args:
            position_history: Lista opcional de posições. Se None, usa histórico interno.
            
        Returns:
            bool: True se detectado um loop.
        """
        if position_history is not None:
            self.position_history = list(position_history[-self.history_size:])
        
        # Tenta múltiplos métodos
        if self.detect_loop_distance():
            self.loop_count += 1
            return True
        
        if len(self.position_history) >= 30:
            if self.detect_loop_fft():
                self.loop_count += 1
                return True
        
        if len(self.position_history) >= 30:
            if self.detect_loop_correlation():
                self.loop_count += 1
                return True
        
        self.loop_count = max(0, self.loop_count - 1)
        return False
    
    def reset(self) -> None:
        """Reseta o detector."""
        self.position_history = []
        self.loop_count = 0
    
    def get_loop_score(self) -> float:
        """Retorna score de quanto está em loop (0-1).
        
        Returns:
            float: Valor entre 0 (sem loop) e 1 (loop forte).
        """
        return min(self.loop_count / 10.0, 1.0)
