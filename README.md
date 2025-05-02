# Corrida DRL

## Introdução

Corrida DRL é um ambiente de corrida customizado para experimentos de Aprendizado por Reforço (RL), com suporte a currículo de fases, visualização gráfica, métricas pedagógicas e logging avançado. O projeto permite treinar agentes RL em mapas de corredor reto e curva, com checkpoints, barreiras e dashboard interativo.

## Requisitos de Ambiente

- Recomenda-se utilizar **Python 3.10** ou **Python 3.11** para máxima compatibilidade com as bibliotecas RL (Stable-Baselines3, Torch, Gym, etc.).
- O projeto foi testado no Windows, mas também é compatível com Linux e Mac.
- Evite Python 3.12 ou superior, pois pode haver incompatibilidades com algumas dependências RL.

Para instalar o Python recomendado, acesse: https://www.python.org/downloads/

## Instalação

1. Clone o repositório:
   ```bash
   git clone <url-do-repo>
   cd corrida_drl
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

Execute o treinamento e visualização com:
```bash
python main.py
```

Opções de linha de comando:
- `--skip-training`: Pula o treinamento e carrega modelo pré-treinado (se existir).

Durante a execução, escolha o mapa/fase desejado pelo prompt interativo.

## Exemplo de config.json

Você pode criar um arquivo `config.json` no diretório raiz para definir hiperparâmetros e configurações do experimento. O conteúdo pode ser, por exemplo:

```json
{
  "learning_rate": 0.0003,
  "gamma": 0.98,
  "n_parallel": 4,
  "map_type": "corridor"
}
```

Para usar, basta rodar:

```
python main.py --config config.json
```

Argumentos passados pela linha de comando sobrescrevem os valores do JSON.

## Exemplos

- Interface gráfica mostrando o ambiente, carros, barreiras e checkpoints.
- Dashboard em tempo real com gráficos de recompensa, colisão e penalização.

![Exemplo da interface](docs/interface_exemplo.png)
![Dashboard](docs/dashboard_exemplo.png)

## Resultados

Exemplo de gráfico de desempenho após treinamento:

![Gráfico de recompensas](docs/grafico_recompensa.png)

- Recompensa média crescente indica aprendizado.
- Colisões diminuindo ao longo do tempo.

## Estrutura do Projeto

- `main.py`: Loop principal de treinamento, avaliação e interface.
- `environment.py`: Ambiente customizado Gym, lógica de física, checkpoints e recompensas.
- `agent.py`: Classe do agente RL (DQN), treinamento, avaliação e callbacks.
- `interface.py`: Visualização gráfica (pygame) e dashboard (matplotlib/tkinter).
- `metrics.py`: Utilitários para métricas e gráficos.
- `config.py`: Parâmetros globais, fases e currículo.
- `logger.py`: Configuração de logging avançado.
- `tests/`: Testes unitários com pytest.
- `requirements.txt`: Dependências do projeto.

## Como Contribuir

- Para adicionar novos mapas: edite `environment.py` e `config.py`.
- Para novos algoritmos: crie uma nova classe em `agent.py`.
- Testes: adicione funções em `tests/` usando pytest.
- Sugestões e issues são bem-vindos!

## Testes

Execute todos os testes unitários com:
```bash
pytest tests/
```

## Licença

MIT. Sinta-se livre para usar e modificar.
