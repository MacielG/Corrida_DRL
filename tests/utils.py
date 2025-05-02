from unittest.mock import Mock

def create_mock_env():
    env = Mock()
    # Basic attributes and methods
    env.width = 800
    env.height = 600
    env.reset.return_value = ([0] * 15, {})
    env.step.return_value = ([0] * 15, 0.0, False, False, {})
    # Attributes accessed in run_curriculum and other tests
    env.car1_pos = (0, 0)
    env.car1_angle = 0.0
    # Add other commonly accessed attributes here if needed
    return env
