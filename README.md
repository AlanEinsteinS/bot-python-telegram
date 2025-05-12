# Bot Financeiro Telegram

Um bot do Telegram para controle financeiro pessoal, desenvolvido em Python.

## Funcionalidades

- Registro de entradas e saídas
- Categorização de transações
- Relatórios e gráficos
- Fechamento de caixa
- Metas financeiras
- Exportação de dados
- Configurações personalizáveis

## Requisitos

- Python 3.8+
- Dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/bot-python-telegram.git
cd bot-python-telegram
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o token do bot:
Edite o arquivo `src/config/settings.py` e substitua o valor de `TOKEN` pelo seu token do BotFather.

## Executando o Bot

```bash
py telegram_bot.py
```

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes. 