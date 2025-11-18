import pytest
import sys
import types

@pytest.mark.timeout(10)
def test_interface_instanciacao():
    print("Iniciando test_interface_instanciacao")
    import interface_dpg
    Interface = interface_dpg.InterfaceDPG
    inst = Interface(width=800, height=600, n_parallel=1)
    assert inst.width == 800
    assert inst.height == 600
    assert hasattr(inst, 'draw_corridor')
    assert hasattr(inst, 'draw_barriers')
    inst.close()  # Fecha pygame
    print("Finalizando test_interface_instanciacao")

@pytest.mark.timeout(10)
def test_compare_algorithms_main(monkeypatch):
    print("Iniciando test_compare_algorithms_main")
    import compare_algorithms
    # Monkeypatch funções pesadas
    monkeypatch.setattr(compare_algorithms, 'run_experiment', lambda *a, **kw: [0]*100)
    monkeypatch.setattr(compare_algorithms, 'plt', types.SimpleNamespace(figure=lambda *a, **k: None, plot=lambda *a, **k: None, title=lambda *a, **k: None, xlabel=lambda *a, **k: None, ylabel=lambda *a, **k: None, legend=lambda *a, **k: None, grid=lambda *a, **k: None, savefig=lambda *a, **k: None, close=lambda *a, **k: None))
    compare_algorithms.main()
    print("Finalizando test_compare_algorithms_main")

@pytest.mark.timeout(10)
def test_main_imports(monkeypatch):
    print("Iniciando test_main_imports")
    import main
    # Monkeypatch funções pesadas
    monkeypatch.setattr(main, 'Agent', lambda *a, **k: type('FakeAgent', (), {'predict': lambda self, x: 0, 'train': lambda self, **kw: None, 'load': lambda self, x: None})())
    monkeypatch.setattr(main, 'Interface', lambda *a, **k: type('FakeInterface', (), {'process_events': lambda self: None, 'clear': lambda self: None, 'draw_env_grid': lambda self, env, idx: None, 'draw_dashboard': lambda self, *a, **k: None, 'update': lambda self: None, 'close': lambda self: None, 'paused': False, 'should_restart': lambda self: False, 'clear_restart': lambda self: None})())
    monkeypatch.setattr(main, 'Metrics', lambda *a, **k: type('FakeMetrics', (), {'update': lambda self, *a, **k: None, 'export_metrics': lambda self, x: None})())
    monkeypatch.setattr(main, 'TrainingLogger', lambda *a, **k: type('FakeLogger', (), {'log': lambda self, *a, **k: None, 'close': lambda self: None})())
    # Testa make_env
    env_fn = main.make_env('corridor')
    assert callable(env_fn)
    # Testa update_curriculum
    main.update_curriculum(100)
    print("Finalizando test_main_imports")
