# novo arquivo: test_pygame_window.py
from interface_dpg import Interface
import time

interface = Interface(width=800, height=600, fase_desc="Teste", n_parallel=1)
for _ in range(300):
    interface.process_events()
    interface.clear()
    interface.draw_dashboard([[]], [[]], [[]], 0, 0.0, 0)
    interface.update()
    time.sleep(0.05)
interface.close()