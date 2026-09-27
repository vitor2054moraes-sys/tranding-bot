# tranding-bot
# 🤖 Bot de Trading

Bot automatizado que roda via **GitHub Actions** a cada 15 minutos durante o pregão da B3 (segunda a sexta, a partir das 10h).

---

## 📁 Estrutura do Projeto

| Arquivo/Pasta | Função |
|---|---|
| `main.py` | Ponto de entrada do bot |
| `strategy.py` | Lógica da estratégia de trading |
| `config.py` | Configurações (ativos, parâmetros) |
| `requirements.txt` | Dependências Python |
| `data/` | Estado do bot e histórico de cotações |
| `reports/` | Relatórios diários gerados |
| `.github/workflows/bot.yml` | Agendamento da execução automática |

---

## 🚀 Como Rodar Localmente

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Execute o bot:

```bash
python main.py
```

---

## ⚙️ Execução Automática

O workflow `.github/workflows/bot.yml`:

- Roda a cada **15 minutos** em dias úteis, durante o horário do pregão
- Executa o `main.py`
- Faz commit automático das alterações em `data/` e `reports/`

Também dá para executar manualmente pela aba **Actions** → **Run workflow**.

---

## 🛠️ Configuração

Edite o `config.py` para ajustar:

- Ativos monitorados
- Parâmetros da estratégia
- Capital inicial e limites de risco

---

## 📊 Relatórios

Os relatórios diários ficam na pasta `reports/`, com as operações e o desempenho do dia.

---

## ⚠️ Aviso

Projeto para fins **educacionais**. Não é recomendação de investimento. Use por sua conta e risco.
