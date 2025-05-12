#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import json
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters
from io import BytesIO
import pandas as pd
import uuid
import calendar
import locale
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from decimal import Decimal

# Configuração para gráficos bonitos
matplotlib.use('Agg')
plt.style.use('ggplot')
plt.rcParams['font.size'] = 12
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False

# Emojis que serão usados no bot
EMOJI = {
    "entrada": "💹",
    "saida": "📉",
    "transacao": "💸",
    "saldo": "💰",
    "relatorio": "📊",
    "calendario": "📅",
    "config": "⚙️",
    "voltar": "⬅️",
    "confirmar": "✅",
    "cancelar": "❌",
    "adicionar": "➕",
    "remover": "➖",
    "editar": "✏️",
    "exportar": "📤",
    "historico": "📋",
    "fechamento": "🔒",
    "dinheiro": "💵",
    "moeda": "🪙",
    "grafico": "📈",
    "alerta": "⚠️",
    "erro": "❗",
    "info": "ℹ️",
    "sucesso": "✅",
    "carteira": "👛",
    "lupa": "🔍",
    "hora": "⏰"
}

# Configurando o locale para português brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        pass  # Se não conseguir configurar o locale, usa o padrão

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Estados para o ConversationHandler
(
    MENU_PRINCIPAL,
    REGISTRAR_TRANSACAO, 
    ESCOLHER_TIPO_TRANSACAO,
    INFORMAR_CATEGORIA,
    INFORMAR_VALOR,
    INFORMAR_DESCRICAO,
    CONFIRMAR_TRANSACAO,
    RELATORIO,
    ESCOLHER_PERIODO_RELATORIO,
    CONFIRMAR_FECHAMENTO_CAIXA,
    CONFIGURACOES,
    ADICIONAR_CATEGORIA,
    REMOVER_CATEGORIA,
    EDITAR_CATEGORIA,
    DEFINIR_META,
    AJUSTAR_SALDO,
    CONFIRMAR_APAGAR_DADOS
) = range(17)

# Diretório para armazenar os dados do bot
DATA_DIR = "bot_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Função para carregar os dados de um usuário
def carregar_dados_usuario(user_id):
    arquivo = f"{DATA_DIR}/dados_{user_id}.json"
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            
            # Garantir que todas as chaves necessárias existam (para compatibilidade com versões anteriores)
            if "metas" not in dados:
                dados["metas"] = {
                    "economia_mensal": 0,
                    "limite_gastos": 0,
                }
            
            if "notificacoes" not in dados:
                dados["notificacoes"] = {
                    "alerta_limite": True,
                    "lembrete_diario": False
                }
                
            return dados
    except (FileNotFoundError, json.JSONDecodeError):
        # Estrutura inicial dos dados
        return {
            "transacoes": [],
            "categorias_entrada": ["Venda", "Investimento", "Salário", "Outro"],
            "categorias_saida": ["Mercadoria", "Pagamento", "Compra", "Alimentação", "Transporte", "Outro"],
            "saldo_atual": 0,
            "data_ultimo_fechamento": None,
            "metas": {
                "economia_mensal": 0,
                "limite_gastos": 0,
            },
            "notificacoes": {
                "alerta_limite": True,
                "lembrete_diario": False
            }
        }

# Função para salvar os dados de um usuário
def salvar_dados_usuario(user_id, dados):
    arquivo = f"{DATA_DIR}/dados_{user_id}.json"
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2, default=str)

# Função para formatar valor em reais
def formatar_valor(valor):
    try:
        # Converter para Decimal para maior precisão
        valor_decimal = Decimal(str(valor))
        # Formatar com 2 casas decimais
        return f"R$ {valor_decimal:.2f}".replace('.', ',')
    except:
        return f"R$ {float(valor):.2f}".replace('.', ',')

# Função para obter a data atual formatada
def obter_data_atual_formatada():
    agora = datetime.datetime.now()
    return agora.strftime("%d/%m/%Y %H:%M:%S")

# Função para obter a data atual como string (apenas a data)
def obter_data_hoje():
    agora = datetime.datetime.now()
    return agora.strftime("%d/%m/%Y")

# Função para analisar a data no formato brasileiro
def analisar_data_br(data_str):
    day, month, year = map(int, data_str.split('/'))
    return datetime.datetime(year, month, day)

# Função para obter o primeiro e último dia do mês
def obter_datas_mes(ano, mes):
    primeiro_dia = datetime.datetime(ano, mes, 1)
    _, ultimo_dia_num = calendar.monthrange(ano, mes)
    ultimo_dia = datetime.datetime(ano, mes, ultimo_dia_num, 23, 59, 59)
    return primeiro_dia, ultimo_dia

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # Carregar ou criar dados do usuário
    dados = carregar_dados_usuario(user_id)
    context.user_data['dados'] = dados
    
    # Mensagem de boas-vindas com design melhorado
    await update.message.reply_text(
        f"🎉 *Olá, {user_name}!* 🎉\n\n"
        f"Bem-vindo ao seu *Assistente Financeiro Pessoal*.\n\n"
        f"{EMOJI['saldo']} Saldo atual: *{formatar_valor(dados['saldo_atual'])}*\n\n"
        f"Este assistente vai ajudar você a controlar suas finanças de forma simples e eficiente.\n\n"
        f"{EMOJI['info']} Use os botões abaixo para navegar:",
        parse_mode='Markdown',
        reply_markup=criar_menu_principal()
    )
    
    return MENU_PRINCIPAL

# Função para criar o menu principal
def criar_menu_principal():
    keyboard = [
        [
            InlineKeyboardButton(f"{EMOJI['entrada']} Registrar Entrada", callback_data='registrar_entrada'),
            InlineKeyboardButton(f"{EMOJI['saida']} Registrar Saída", callback_data='registrar_saida')
        ],
        [
            InlineKeyboardButton(f"{EMOJI['relatorio']} Relatórios", callback_data='relatorios'),
            InlineKeyboardButton(f"{EMOJI['historico']} Histórico", callback_data='historico')
        ],
        [
            InlineKeyboardButton(f"{EMOJI['fechamento']} Fechamento de Caixa", callback_data='fechamento_caixa'),
            InlineKeyboardButton(f"{EMOJI['config']} Configurações", callback_data='configuracoes')
        ],
        [
            InlineKeyboardButton(f"{EMOJI['dinheiro']} Ajustar Saldo", callback_data='ajustar_saldo'),
            InlineKeyboardButton(f"{EMOJI['grafico']} Definir Metas", callback_data='definir_metas')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Função para voltar ao menu principal
async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    if query:
        await query.answer()
        await query.edit_message_text(
            text=f"{EMOJI['carteira']} *Menu Principal*\n\n"
                 f"{EMOJI['saldo']} Saldo atual: *{formatar_valor(dados['saldo_atual'])}*",
            parse_mode='Markdown',
            reply_markup=criar_menu_principal()
        )
    else:
        await update.message.reply_text(
            text=f"{EMOJI['carteira']} *Menu Principal*\n\n"
                 f"{EMOJI['saldo']} Saldo atual: *{formatar_valor(dados['saldo_atual'])}*",
            parse_mode='Markdown',
            reply_markup=criar_menu_principal()
        )
    return MENU_PRINCIPAL

# Callback para o menu principal
async def callback_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    opcao = query.data
    user_id = update.effective_user.id
    
    logger.info(f"Callback menu principal: {opcao}")
    
    # Carregar dados atualizados
    dados = carregar_dados_usuario(user_id)
    context.user_data['dados'] = dados
    
    if opcao == 'registrar_entrada':
        context.user_data['transacao_temp'] = {'tipo': 'entrada'}
        categorias = dados['categorias_entrada']
        
        # Layout de botões em grade (2 por linha, quando possível)
        keyboard = []
        row = []
        for i, cat in enumerate(categorias):
            row.append(InlineKeyboardButton(f"{EMOJI['entrada']} {cat}", callback_data=f"cat_{cat}"))
            if len(row) == 2 or i == len(categorias) - 1:
                keyboard.append(row)
                row = []
        
        keyboard.append([InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')])
        
        await query.edit_message_text(
            text=f"{EMOJI['entrada']} *Registrar Entrada*\n\nSelecione a categoria:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return INFORMAR_CATEGORIA
        
    elif opcao == 'registrar_saida':
        context.user_data['transacao_temp'] = {'tipo': 'saida'}
        categorias = dados['categorias_saida']
        
        # Layout de botões em grade (2 por linha, quando possível)
        keyboard = []
        row = []
        for i, cat in enumerate(categorias):
            row.append(InlineKeyboardButton(f"{EMOJI['saida']} {cat}", callback_data=f"cat_{cat}"))
            if len(row) == 2 or i == len(categorias) - 1:
                keyboard.append(row)
                row = []
                
        keyboard.append([InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')])
        
        await query.edit_message_text(
            text=f"{EMOJI['saida']} *Registrar Saída*\n\nSelecione a categoria:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return INFORMAR_CATEGORIA
        
    elif opcao == 'relatorios':
        keyboard = [
            [
                InlineKeyboardButton(f"{EMOJI['calendario']} Relatório do Dia", callback_data='relatorio_dia'),
                InlineKeyboardButton(f"{EMOJI['calendario']} Relatório da Semana", callback_data='relatorio_semana')
            ],
            [
                InlineKeyboardButton(f"{EMOJI['calendario']} Relatório do Mês", callback_data='relatorio_mes'),
                InlineKeyboardButton(f"{EMOJI['lupa']} Relatório Personalizado", callback_data='relatorio_personalizado')
            ],
            [InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]
        ]
        await query.edit_message_text(
            text=f"{EMOJI['relatorio']} *Relatórios Financeiros*\n\nEscolha o tipo de relatório que deseja visualizar:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return RELATORIO
        
    elif opcao == 'historico':
        # Exibir histórico de transações recentes
        await mostrar_historico(update, context)
        return MENU_PRINCIPAL
    elif opcao == 'grafico_historico':
        await mostrar_grafico_historico(update, context)
        return MENU_PRINCIPAL
    elif opcao == 'exportar_historico':
        await exportar_historico(update, context)
        return MENU_PRINCIPAL
        
    elif opcao == 'fechamento_caixa':
        # Verificar se já houve fechamento hoje
        data_hoje = obter_data_hoje()
        ultimo_fechamento = dados.get('data_ultimo_fechamento', None)
        
        logger.info(f"Verificando fechamento: data_hoje={data_hoje}, ultimo_fechamento={ultimo_fechamento}")
        
        if ultimo_fechamento == data_hoje:
            keyboard = [
                [InlineKeyboardButton(f"{EMOJI['confirmar']} Sim, fazer novo fechamento", callback_data='novo_fechamento')],
                [InlineKeyboardButton(f"{EMOJI['cancelar']} Não, voltar ao menu", callback_data='voltar_menu')]
            ]
            await query.edit_message_text(
                text=f"{EMOJI['alerta']} *Atenção*\n\n"
                     f"Você já realizou um fechamento de caixa hoje ({data_hoje}).\n\n"
                     f"Deseja realizar um novo fechamento?",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return CONFIRMAR_FECHAMENTO_CAIXA
        else:
            await preparar_fechamento_caixa(update, context)
            return CONFIRMAR_FECHAMENTO_CAIXA
        
    elif opcao == 'novo_fechamento':
        logger.info("Iniciando novo fechamento")
        await preparar_fechamento_caixa(update, context)
        return CONFIRMAR_FECHAMENTO_CAIXA
        
    elif opcao == 'configuracoes':
        keyboard = [
            [
                InlineKeyboardButton(f"{EMOJI['adicionar']} Categoria Entrada", callback_data='add_cat_entrada'),
                InlineKeyboardButton(f"{EMOJI['adicionar']} Categoria Saída", callback_data='add_cat_saida')
            ],
            [
                InlineKeyboardButton(f"{EMOJI['editar']} Editar Cat. Entrada", callback_data='editar_cat_entrada'),
                InlineKeyboardButton(f"{EMOJI['editar']} Editar Cat. Saída", callback_data='editar_cat_saida')
            ],
            [
                InlineKeyboardButton(f"{EMOJI['remover']} Remover Cat. Entrada", callback_data='remover_cat_entrada'),
                InlineKeyboardButton(f"{EMOJI['remover']} Remover Cat. Saída", callback_data='remover_cat_saida')
            ],
            [
                InlineKeyboardButton(f"{EMOJI['exportar']} Exportar Dados", callback_data='exportar_dados'),
                InlineKeyboardButton(f"{EMOJI['alerta']} Notificações", callback_data='config_notificacoes')
            ],
            [
                InlineKeyboardButton(f"{EMOJI['erro']} Apagar Dados", callback_data='apagar_dados')
            ],
            [InlineKeyboardButton(f"{EMOJI['voltar']} Voltar ao Menu Principal", callback_data='voltar_menu')]
        ]
        await query.edit_message_text(
            f"{EMOJI['config']} *Configurações*\n\n"
            f"Personalize seu assistente financeiro:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIGURACOES
    
    elif opcao == 'definir_metas':
        # Interface para definir metas financeiras
        metas = dados.get('metas', {'economia_mensal': 0, 'limite_gastos': 0})
        
        keyboard = [
            [InlineKeyboardButton(f"{EMOJI['grafico']} Definir Meta de Economia", callback_data='meta_economia')],
            [InlineKeyboardButton(f"{EMOJI['alerta']} Definir Limite de Gastos", callback_data='meta_limite')],
            [InlineKeyboardButton(f"{EMOJI['voltar']} Voltar ao Menu", callback_data='voltar_menu')]
        ]
        
        await query.edit_message_text(
            text=f"{EMOJI['grafico']} *Metas Financeiras*\n\n"
                 f"• Meta de economia mensal: *{formatar_valor(metas['economia_mensal'])}*\n"
                 f"• Limite de gastos mensal: *{formatar_valor(metas['limite_gastos'])}*\n\n"
                 f"Selecione uma opção para definir ou atualizar suas metas:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return DEFINIR_META
        
    elif opcao == 'ajustar_saldo':
        # Interface para ajustar o saldo manualmente
        await query.edit_message_text(
            text=f"{EMOJI['dinheiro']} *Ajustar Saldo*\n\n"
                 f"Saldo atual: *{formatar_valor(dados['saldo_atual'])}*\n\n"
                 f"Digite o novo valor do saldo (use ponto para decimais):",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Cancelar", callback_data='voltar_menu')]])
        )
        
        return AJUSTAR_SALDO
        
    elif opcao == 'voltar_menu':
        return await menu_principal(update, context)
    
    return MENU_PRINCIPAL

# Função para ajustar saldo manualmente
async def ajustar_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == 'voltar_menu':
            return await menu_principal(update, context)
        return AJUSTAR_SALDO
    
    valor_texto = update.message.text.strip().replace(',', '.')
    try:
        novo_saldo = float(valor_texto)
        if novo_saldo < 0:
            await update.message.reply_text(
                f"{EMOJI['erro']} O saldo não pode ser negativo. Por favor, digite novamente:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Cancelar", callback_data='voltar_menu')]])
            )
            return AJUSTAR_SALDO
    except ValueError:
        await update.message.reply_text(
            f"{EMOJI['erro']} Valor inválido. Por favor, digite apenas números (ex: 1500.50):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Cancelar", callback_data='voltar_menu')]])
        )
        return AJUSTAR_SALDO
    
    # Atualizar o saldo
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    # Registrar o ajuste como uma transação especial
    ajuste = novo_saldo - dados['saldo_atual']
    
    if ajuste != 0:
        transacao = {
            'tipo': 'entrada' if ajuste > 0 else 'saida',
            'categoria': 'Ajuste Manual',
            'valor': abs(ajuste),
            'descricao': 'Ajuste manual de saldo',
            'data': obter_data_atual_formatada(),
            'id': str(uuid.uuid4())
        }
        
        dados['transacoes'].append(transacao)
    
    # Atualizar o saldo
    dados['saldo_atual'] = novo_saldo
    salvar_dados_usuario(user_id, dados)
    
    # Confirmar para o usuário
    await update.message.reply_text(
        f"{EMOJI['sucesso']} Saldo ajustado com sucesso!\n\n"
        f"Saldo atual: *{formatar_valor(novo_saldo)}*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar ao Menu", callback_data='voltar_menu')]])
    )
    
    return MENU_PRINCIPAL

# Função para definir metas
async def definir_meta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if not query:
        # Recebendo valor digitado pelo usuário
        if 'meta_atual' not in context.user_data:
            await update.message.reply_text(
                f"{EMOJI['erro']} Ocorreu um erro. Por favor, tente novamente através do menu.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
            )
            return MENU_PRINCIPAL
        
        tipo_meta = context.user_data['meta_atual']
        valor_texto = update.message.text.strip().replace(',', '.')
        
        try:
            valor_meta = float(valor_texto)
            if valor_meta < 0:
                await update.message.reply_text(
                    f"{EMOJI['erro']} O valor não pode ser negativo. Por favor, digite novamente:",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Cancelar", callback_data='voltar_menu')]])
                )
                return DEFINIR_META
        except ValueError:
            await update.message.reply_text(
                f"{EMOJI['erro']} Valor inválido. Por favor, digite apenas números (ex: 1000.50):",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Cancelar", callback_data='voltar_menu')]])
            )
            return DEFINIR_META
        
        # Salvar a meta
        user_id = update.effective_user.id
        dados = carregar_dados_usuario(user_id)
        
        if tipo_meta == 'economia':
            dados['metas']['economia_mensal'] = valor_meta
            mensagem = "Meta de economia mensal"
        else:  # limite
            dados['metas']['limite_gastos'] = valor_meta
            mensagem = "Limite de gastos mensal"
        
        salvar_dados_usuario(user_id, dados)
        
        # Confirmar para o usuário
        await update.message.reply_text(
            f"{EMOJI['sucesso']} {mensagem} definido com sucesso!\n\n"
            f"Valor: *{formatar_valor(valor_meta)}*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar ao Menu", callback_data='voltar_menu')]])
        )
        
        # Limpar dados temporários
        if 'meta_atual' in context.user_data:
            del context.user_data['meta_atual']
        
        return MENU_PRINCIPAL
    
    # Processando callback
    await query.answer()
    
    if query.data == 'voltar_menu':
        return await menu_principal(update, context)
    
    if query.data == 'meta_economia':
        context.user_data['meta_atual'] = 'economia'
        await query.edit_message_text(
            text=f"{EMOJI['grafico']} *Definir Meta de Economia Mensal*\n\n"
                 f"Digite o valor da sua meta de economia mensal (quanto deseja guardar por mês):",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Cancelar", callback_data='voltar_menu')]])
        )
        return DEFINIR_META
    
    elif query.data == 'meta_limite':
        context.user_data['meta_atual'] = 'limite'
        await query.edit_message_text(
            text=f"{EMOJI['alerta']} *Definir Limite de Gastos Mensal*\n\n"
                 f"Digite o valor máximo que deseja gastar por mês:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Cancelar", callback_data='voltar_menu')]])
        )
        return DEFINIR_META
    
    return DEFINIR_META

# Função para selecionar categoria
async def selecionar_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'voltar_menu':
        return await menu_principal(update, context)
    
    # Extrair a categoria da callback_data
    categoria = query.data[4:]  # Remove o prefixo "cat_"
    context.user_data['transacao_temp']['categoria'] = categoria
    
    tipo_emoji = EMOJI['entrada'] if context.user_data['transacao_temp']['tipo'] == 'entrada' else EMOJI['saida']
    
    await query.edit_message_text(
        text=f"{tipo_emoji} *Registro de {context.user_data['transacao_temp']['tipo'].capitalize()}*\n\n"
             f"Categoria: *{categoria}*\n\n"
             f"Digite o valor (apenas números, use ponto para decimais):",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
    )
    
    return INFORMAR_VALOR

# Função para informar valor
async def informar_valor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == 'voltar_menu':
            return await menu_principal(update, context)
        return INFORMAR_VALOR
    
    valor_texto = update.message.text.strip().replace(',', '.')
    try:
        valor = float(valor_texto)
        if valor <= 0:
            await update.message.reply_text(
                f"{EMOJI['erro']} O valor deve ser maior que zero. Por favor, digite novamente:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
            )
            return INFORMAR_VALOR
    except ValueError:
        await update.message.reply_text(
            f"{EMOJI['erro']} Valor inválido. Por favor, digite apenas números (ex: 100.50):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
        return INFORMAR_VALOR
    
    context.user_data['transacao_temp']['valor'] = valor
    
    tipo_emoji = EMOJI['entrada'] if context.user_data['transacao_temp']['tipo'] == 'entrada' else EMOJI['saida']
    categoria = context.user_data['transacao_temp']['categoria']
    
    await update.message.reply_text(
        f"{tipo_emoji} *Registro de {context.user_data['transacao_temp']['tipo'].capitalize()}*\n\n"
        f"Categoria: *{categoria}*\n"
        f"Valor: *{formatar_valor(valor)}*\n\n"
        f"Agora, digite uma descrição breve para esta transação:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
    )
    
    return INFORMAR_DESCRICAO

# Função para informar descrição
async def informar_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == 'voltar_menu':
            return await menu_principal(update, context)
        return INFORMAR_DESCRICAO
    
    descricao = update.message.text.strip()
    if not descricao:
        await update.message.reply_text(
            f"{EMOJI['erro']} A descrição não pode estar vazia. Por favor, digite uma descrição:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
        return INFORMAR_DESCRICAO
    
    context.user_data['transacao_temp']['descricao'] = descricao
    
# Continuação do código

    # Preparar resumo da transação para confirmação
    transacao = context.user_data['transacao_temp']
    tipo = "Entrada" if transacao['tipo'] == 'entrada' else "Saída"
    tipo_emoji = EMOJI['entrada'] if transacao['tipo'] == 'entrada' else EMOJI['saida']
    
    await update.message.reply_text(
        f"{tipo_emoji} *Resumo da Transação*\n\n"
        f"• Tipo: *{tipo}*\n"
        f"• Categoria: *{transacao['categoria']}*\n"
        f"• Valor: *{formatar_valor(transacao['valor'])}*\n"
        f"• Descrição: *{transacao['descricao']}*\n\n"
        f"Confirma esta transação?",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{EMOJI['confirmar']} Confirmar", callback_data='confirmar_transacao')],
            [InlineKeyboardButton(f"{EMOJI['cancelar']} Cancelar", callback_data='voltar_menu')]
        ])
    )
    
    return CONFIRMAR_TRANSACAO

# Função para confirmar transação
async def confirmar_transacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'voltar_menu':
        return await menu_principal(update, context)
    
    user_id = update.effective_user.id
    dados = context.user_data['dados']
    transacao = context.user_data['transacao_temp']
    
    # Adicionar data e ID à transação
    transacao['data'] = obter_data_atual_formatada()
    transacao['id'] = str(uuid.uuid4())
    
    # Atualizar saldo
    if transacao['tipo'] == 'entrada':
        dados['saldo_atual'] += transacao['valor']
    else:
        dados['saldo_atual'] -= transacao['valor']
    
    # Adicionar à lista de transações
    dados['transacoes'].append(transacao)
    
    # Verificar limites (para saídas)
    mensagem_alerta = ""
    if transacao['tipo'] == 'saida' and dados.get('notificacoes', {}).get('alerta_limite', True):
        # Calcular gastos do mês atual
        hoje = datetime.datetime.now()
        primeiro_dia, ultimo_dia = obter_datas_mes(hoje.year, hoje.month)
        
        gastos_mes = 0
        for t in dados['transacoes']:
            if t['tipo'] == 'saida':
                try:
                    data_t = datetime.datetime.strptime(t['data'], "%d/%m/%Y %H:%M:%S")
                    if primeiro_dia <= data_t <= ultimo_dia:
                        gastos_mes += t['valor']
                except:
                    continue
        
        # Verificar se ultrapassou o limite
        limite_gastos = dados.get('metas', {}).get('limite_gastos', 0)
        if limite_gastos > 0 and gastos_mes > limite_gastos:
            mensagem_alerta = f"\n\n{EMOJI['alerta']} *Alerta de Limite*\n" \
                             f"Você ultrapassou seu limite mensal de gastos! " \
                             f"Gastos no mês: {formatar_valor(gastos_mes)}\n" \
                             f"Seu limite: {formatar_valor(limite_gastos)}"
    
    # Salvar dados
    salvar_dados_usuario(user_id, dados)
    
    # Confirmar para o usuário
    tipo = "Entrada" if transacao['tipo'] == 'entrada' else "Saída"
    tipo_emoji = EMOJI['entrada'] if transacao['tipo'] == 'entrada' else EMOJI['saida']
    
    await query.edit_message_text(
        f"{EMOJI['sucesso']} *{tipo} registrada com sucesso!*\n\n"
        f"• Categoria: *{transacao['categoria']}*\n"
        f"• Valor: *{formatar_valor(transacao['valor'])}*\n"
        f"• Descrição: *{transacao['descricao']}*\n\n"
        f"{EMOJI['saldo']} Seu saldo atual é: *{formatar_valor(dados['saldo_atual'])}*"
        f"{mensagem_alerta}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{EMOJI['adicionar']} Nova Transação", callback_data=f"registrar_{transacao['tipo']}")],
            [InlineKeyboardButton(f"{EMOJI['voltar']} Voltar ao Menu", callback_data='voltar_menu')]
        ])
    )
    
    # Limpar dados temporários
    if 'transacao_temp' in context.user_data:
        del context.user_data['transacao_temp']
    
    return MENU_PRINCIPAL

# Função para mostrar histórico
async def mostrar_historico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    logger.info("Iniciando mostrar_historico")
    
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    # Obter as últimas 10 transações (ou menos, se houver menos)
    transacoes = dados['transacoes'][-10:]
    transacoes.reverse()  # Mais recentes primeiro
    
    if not transacoes:
        logger.info("Nenhuma transação encontrada")
        await query.edit_message_text(
            f"{EMOJI['info']} Não há transações registradas ainda.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
        return
    
    logger.info(f"Encontradas {len(transacoes)} transações")
    
    # Formatar o histórico
    texto = f"{EMOJI['historico']} *Últimas Transações*\n\n"
    
    for t in transacoes:
        tipo_emoji = EMOJI['entrada'] if t['tipo'] == 'entrada' else EMOJI['saida']
        valor_formatado = formatar_valor(t['valor'])
        
        texto += f"{tipo_emoji} *{t['data'].split()[0]}* - {t['categoria']}\n"
        texto += f"    {valor_formatado} - {t['descricao']}\n\n"
    
    texto += f"{EMOJI['saldo']} *Saldo Atual*: {formatar_valor(dados['saldo_atual'])}"
    
    # Botões para navegação
    keyboard = [
        [
            InlineKeyboardButton(f"{EMOJI['grafico']} Ver Gráfico", callback_data='grafico_historico'),
            InlineKeyboardButton(f"{EMOJI['exportar']} Exportar", callback_data='exportar_historico')
        ],
        [InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]
    ]
    
    logger.info("Enviando mensagem com histórico")
    await query.edit_message_text(
        texto,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Função para exportar histórico
async def exportar_historico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    logger.info("Iniciando exportar_historico")
    
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    # Obter as últimas 10 transações
    transacoes = dados['transacoes'][-10:]
    transacoes.reverse()  # Mais recentes primeiro
    
    if not transacoes:
        logger.info("Nenhuma transação para exportar")
        await query.edit_message_text(
            f"{EMOJI['info']} Não há transações para exportar.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
        return
    
    try:
        logger.info(f"Exportando {len(transacoes)} transações")
        
        # Criar CSV em memória
        output = BytesIO()
        output.write("Tipo,Data,Categoria,Valor,Descrição\n".encode('utf-8'))
        
        for t in transacoes:
            valor_str = str(t['valor']).replace('.', ',')
            linha = f"{t['tipo']},{t['data']},{t['categoria']},{valor_str},\"{t['descricao']}\"\n"
            output.write(linha.encode('utf-8'))
        
        output.seek(0)
        
        # Enviar arquivo
        data_atual = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=output,
            filename=f"historico_{data_atual}.csv",
            caption=f"{EMOJI['exportar']} Exportação das últimas {len(transacoes)} transações"
        )
        
        logger.info("Arquivo enviado com sucesso")
        
        # Atualizar mensagem
        await query.edit_message_text(
            f"{EMOJI['sucesso']} Histórico exportado com sucesso!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
        
    except Exception as e:
        logger.error(f"Erro ao exportar histórico: {str(e)}")
        await query.edit_message_text(
            f"{EMOJI['erro']} Ocorreu um erro ao exportar o histórico. Por favor, tente novamente.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
    
    return MENU_PRINCIPAL

# Função para exibir gráfico do histórico
async def mostrar_grafico_historico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    logger.info("Iniciando mostrar_grafico_historico")
    
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    # Verificar se há transações suficientes
    if len(dados['transacoes']) < 2:
        logger.info("Transações insuficientes para gerar gráfico")
        await query.edit_message_text(
            f"{EMOJI['info']} Não há transações suficientes para gerar um gráfico.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
        return
    
    logger.info("Gerando gráficos")
    
    try:
        # Criar DataFrame para análise
        df = pd.DataFrame(dados['transacoes'])
        
        # Converter datas
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y %H:%M:%S')
        df['date_only'] = df['data'].dt.date
        
        # Separar entradas e saídas
        entradas = df[df['tipo'] == 'entrada'].copy()
        saidas = df[df['tipo'] == 'saida'].copy()
        
        # Agrupar por data
        if not entradas.empty:
            entradas_por_data = entradas.groupby('date_only')['valor'].sum()
        else:
            entradas_por_data = pd.Series()
        
        if not saidas.empty:
            saidas_por_data = saidas.groupby('date_only')['valor'].sum()
        else:
            saidas_por_data = pd.Series()
        
        # Criar figura
        plt.figure(figsize=(10, 6))
        
        # Personalizar o gráfico para um visual mais moderno
        plt.style.use('ggplot')
        
        # Plotar gráfico
        if not entradas_por_data.empty:
            plt.plot(entradas_por_data.index, entradas_por_data.values, 'g-', linewidth=2.5, marker='o', markersize=6, label='Entradas')
        
        if not saidas_por_data.empty:
            plt.plot(saidas_por_data.index, saidas_por_data.values, 'r-', linewidth=2.5, marker='o', markersize=6, label='Saídas')
        
        plt.title('Fluxo de Caixa - Últimos Dias', fontsize=16, fontweight='bold')
        plt.xlabel('Data', fontsize=12)
        plt.ylabel('Valor (R$)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=12)
        
        # Formatar eixo Y para valores monetários
        from matplotlib.ticker import FuncFormatter
        def format_real(x, pos):
            return f'R${x:.0f}'
        plt.gca().yaxis.set_major_formatter(FuncFormatter(format_real))
        
        # Ajustar layout
        plt.tight_layout()
        
        # Salvar em memória
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        
        logger.info("Enviando primeiro gráfico")
        # Enviar primeiro gráfico
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=buf,
            caption=f"{EMOJI['grafico']} Gráfico de Fluxo de Caixa por Dia"
        )
        
        # Criar um gráfico adicional de categorias
        plt.figure(figsize=(10, 6))
        
        # Agrupar por categoria para o gráfico de pizza
        if not saidas.empty:
            categorias_saida = saidas.groupby('categoria')['valor'].sum()
            
            # Criar gráfico de pizza
            plt.pie(categorias_saida.values, labels=categorias_saida.index, autopct='%1.1f%%', 
                    startangle=90, shadow=True, explode=[0.05]*len(categorias_saida),
                    textprops={'fontsize': 12})
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            plt.title('Distribuição de Gastos por Categoria', fontsize=16, fontweight='bold')
            
            # Salvar em memória
            buf2 = BytesIO()
            plt.tight_layout()
            plt.savefig(buf2, format='png', dpi=100)
            buf2.seek(0)
            
            logger.info("Enviando segundo gráfico")
            # Enviar segundo gráfico
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=buf2,
                caption=f"{EMOJI['grafico']} Distribuição de Gastos por Categoria"
            )
        
        # Voltar ao menu
        await query.edit_message_text(
            f"{EMOJI['sucesso']} Gráficos gerados com sucesso!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar gráficos: {str(e)}")
        await query.edit_message_text(
            f"{EMOJI['erro']} Ocorreu um erro ao gerar os gráficos. Por favor, tente novamente.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
    
    return MENU_PRINCIPAL

# Função para geração de relatórios
async def callback_relatorios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    opcao = query.data
    
    if opcao == 'voltar_menu':
        return await menu_principal(update, context)
    
    hoje = datetime.datetime.now()
    transacoes = dados['transacoes']
    
    # Definir período com base na opção selecionada
    if opcao == 'relatorio_dia':
        # Relatório do dia atual
        data_inicio = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
        data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
        titulo = f"Relatório do Dia {hoje.strftime('%d/%m/%Y')}"
        
    elif opcao == 'relatorio_semana':
        # Relatório da semana atual
        data_inicio = hoje - datetime.timedelta(days=hoje.weekday())
        data_inicio = data_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
        titulo = f"Relatório da Semana ({data_inicio.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')})"
        
    elif opcao == 'relatorio_mes':
        # Relatório do mês atual
        data_inicio, data_fim = obter_datas_mes(hoje.year, hoje.month)
        titulo = f"Relatório do Mês de {calendar.month_name[hoje.month]} de {hoje.year}"
        
    elif opcao == 'relatorio_personalizado':
        # Solicitar período personalizado
        await query.edit_message_text(
            f"{EMOJI['calendario']} *Relatório Personalizado*\n\n"
            f"Para gerar um relatório personalizado, envie as datas de início e fim no formato DD/MM/AAAA - DD/MM/AAAA\n\n"
            f"Exemplo: 01/05/2025 - 15/05/2025",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
        return ESCOLHER_PERIODO_RELATORIO
    
    if opcao != 'relatorio_personalizado':
        # Gerar relatório baseado no período selecionado
        await gerar_relatorio(update, context, data_inicio, data_fim, titulo)
    
    return RELATORIO

# Função para processar período personalizado
async def escolher_periodo_relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == 'voltar_menu':
            return await menu_principal(update, context)
        return ESCOLHER_PERIODO_RELATORIO
    
    # Processar a entrada do usuário
    texto = update.message.text.strip()
    try:
        # Tentar extrair as datas
        datas = texto.split('-')
        if len(datas) != 2:
            raise ValueError("Formato inválido")
        
        data_inicio_str = datas[0].strip()
        data_fim_str = datas[1].strip()
        
        data_inicio = analisar_data_br(data_inicio_str)
        data_fim = analisar_data_br(data_fim_str)
        data_fim = data_fim.replace(hour=23, minute=59, second=59)
        
        titulo = f"Relatório de {data_inicio_str} a {data_fim_str}"
        
        # Gerar relatório
        await gerar_relatorio(update, context, data_inicio, data_fim, titulo, is_message=True)
        
        return RELATORIO
        
    except Exception as e:
        await update.message.reply_text(
            f"{EMOJI['erro']} Formato de data inválido. Por favor, use o formato DD/MM/AAAA - DD/MM/AAAA\n\n"
            f"Exemplo: 01/05/2025 - 15/05/2025",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
        return ESCOLHER_PERIODO_RELATORIO

# Função para gerar relatório
async def gerar_relatorio(update: Update, context, data_inicio, data_fim, titulo, is_message=False):
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    # Converter strings de data para datetime
    transacoes_filtradas = []
    for t in dados['transacoes']:
        try:
            data_transacao = datetime.datetime.strptime(t['data'], "%d/%m/%Y %H:%M:%S")
            if data_inicio <= data_transacao <= data_fim:
                transacoes_filtradas.append(t)
        except Exception:
            # Ignorar transações com formato de data inválido
            continue
    
    # Calcular totais
    total_entradas = sum(t['valor'] for t in transacoes_filtradas if t['tipo'] == 'entrada')
    total_saidas = sum(t['valor'] for t in transacoes_filtradas if t['tipo'] == 'saida')
    saldo_periodo = total_entradas - total_saidas
    
    # Agrupar por categorias
    categorias_entrada = {}
    categorias_saida = {}
    
    for t in transacoes_filtradas:
        if t['tipo'] == 'entrada':
            categorias_entrada[t['categoria']] = categorias_entrada.get(t['categoria'], 0) + t['valor']
        else:
            categorias_saida[t['categoria']] = categorias_saida.get(t['categoria'], 0) + t['valor']
    
    # Preparar texto do relatório
    texto = f"{EMOJI['relatorio']} *{titulo}*\n\n"
    
    texto += f"{EMOJI['saldo']} *Resumo Financeiro*\n"
    texto += f"• Total de Entradas: *{formatar_valor(total_entradas)}*\n"
    texto += f"• Total de Saídas: *{formatar_valor(total_saidas)}*\n"
    texto += f"• Saldo do Período: *{formatar_valor(saldo_periodo)}*\n\n"
    
    # Calcular o progresso das metas
    metas = dados.get('metas', {})
    meta_economia = metas.get('economia_mensal', 0)
    limite_gastos = metas.get('limite_gastos', 0)
    
    # Adicionar informações sobre metas apenas se as datas abrangerem o mês atual
    hoje = datetime.datetime.now()
    primeiro_dia_mes, ultimo_dia_mes = obter_datas_mes(hoje.year, hoje.month)
    
    # Verificar se o período inclui o mês atual
    if (data_inicio <= hoje <= data_fim) or (data_inicio >= primeiro_dia_mes and data_inicio <= ultimo_dia_mes):
        if meta_economia > 0:
            progresso_economia = (saldo_periodo / meta_economia) * 100 if saldo_periodo > 0 else 0
            texto += f"{EMOJI['grafico']} *Meta de Economia*\n"
            texto += f"• Meta: *{formatar_valor(meta_economia)}*\n"
            texto += f"• Economia: *{formatar_valor(saldo_periodo)}*\n"
            texto += f"• Progresso: *{progresso_economia:.1f}%*\n\n"
        
        if limite_gastos > 0:
            porcentagem_gasto = (total_saidas / limite_gastos) * 100
            texto += f"{EMOJI['alerta']} *Limite de Gastos*\n"
            texto += f"• Limite: *{formatar_valor(limite_gastos)}*\n"
            texto += f"• Gastos: *{formatar_valor(total_saidas)}*\n"
            texto += f"• Utilizado: *{porcentagem_gasto:.1f}%*\n\n"
    
    if categorias_entrada:
        texto += f"{EMOJI['entrada']} *Entradas por Categoria*\n"
        for cat, valor in sorted(categorias_entrada.items(), key=lambda x: x[1], reverse=True):
            percentual = (valor / total_entradas * 100) if total_entradas > 0 else 0
            texto += f"• {cat}: *{formatar_valor(valor)}* ({percentual:.1f}%)\n"
        texto += "\n"
    
    if categorias_saida:
        texto += f"{EMOJI['saida']} *Saídas por Categoria*\n"
        for cat, valor in sorted(categorias_saida.items(), key=lambda x: x[1], reverse=True):
            percentual = (valor / total_saidas * 100) if total_saidas > 0 else 0
            texto += f"• {cat}: *{formatar_valor(valor)}* ({percentual:.1f}%)\n"
        texto += "\n"
    
    texto += f"Total de transações no período: *{len(transacoes_filtradas)}*"
    
    # Botões para navegação
    keyboard = [
        [
            InlineKeyboardButton(f"{EMOJI['grafico']} Ver Gráfico", callback_data='grafico_relatorio'),
            InlineKeyboardButton(f"{EMOJI['exportar']} Exportar CSV", callback_data='exportar_relatorio')
        ],
        [InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]
    ]
    
    # Armazenar dados para uso posterior
    context.user_data['relatorio_atual'] = {
        'transacoes': transacoes_filtradas,
        'periodo': (data_inicio, data_fim),
        'titulo': titulo,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas
    }
    
    # Enviar relatório
    if is_message:
        await update.message.reply_text(
            texto,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        query = update.callback_query
        await query.edit_message_text(
            texto,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    return RELATORIO

# Função para exportar relatório como CSV
async def exportar_relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if 'relatorio_atual' not in context.user_data:
        await query.edit_message_text(
            f"{EMOJI['erro']} Não há relatório para exportar. Por favor, gere um relatório primeiro.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
        return MENU_PRINCIPAL
    
    relatorio = context.user_data['relatorio_atual']
    transacoes = relatorio['transacoes']
    titulo = relatorio['titulo'].replace(" ", "_").replace(":", "_")
    
    if not transacoes:
        await query.edit_message_text(
            f"{EMOJI['info']} Não há transações para exportar neste período.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_relatorios')]])
        )
        return RELATORIO
    
    # Criar CSV em memória
    output = BytesIO()
    output.write("Tipo,Data,Categoria,Valor,Descrição\n".encode('utf-8'))
    
    for t in transacoes:
        valor_str = str(t['valor']).replace('.', ',')
        linha = f"{t['tipo']},{t['data']},{t['categoria']},{valor_str},\"{t['descricao']}\"\n"
        output.write(linha.encode('utf-8'))
    
    output.seek(0)
    
    # Enviar arquivo
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=output,
        filename=f"relatorio_{titulo}.csv",
        caption=f"{EMOJI['exportar']} Exportação de {len(transacoes)} transações"
    )
    
    # Atualizar mensagem
    await query.edit_message_text(
        f"{EMOJI['sucesso']} Relatório exportado com sucesso como CSV: {len(transacoes)} transações.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{EMOJI['relatorio']} Voltar aos Relatórios", callback_data='voltar_relatorios')],
            [InlineKeyboardButton(f"{EMOJI['voltar']} Menu Principal", callback_data='voltar_menu')]
        ])
    )
    
    return RELATORIO

# Função para gerar gráfico do relatório
async def grafico_relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if 'relatorio_atual' not in context.user_data:
        await query.edit_message_text(
            f"{EMOJI['erro']} Não há relatório para visualizar. Por favor, gere um relatório primeiro.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
        return MENU_PRINCIPAL
    
    relatorio = context.user_data['relatorio_atual']
    transacoes = relatorio['transacoes']
    titulo = relatorio['titulo']
    
    if not transacoes:
        await query.edit_message_text(
            f"{EMOJI['info']} Não há transações para visualizar neste período.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_relatorios')]])
        )
        return RELATORIO
    
    # Criar DataFrame para análise
    df = pd.DataFrame(transacoes)
    
    # Converter datas
    df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y %H:%M:%S')
    df['date_only'] = df['data'].dt.date
    
    # Criar gráficos
    
    # 1. Gráfico de Barras: Entradas vs Saídas
    plt.figure(figsize=(10, 6))
    entradas_total = relatorio['total_entradas']
    saidas_total = relatorio['total_saidas']
    
    barras = plt.bar([0, 1], [entradas_total, saidas_total], color=['green', 'red'], width=0.5)
    
    # Adicionar rótulos com os valores
    for bar in barras:
        height = bar.get_height()
        plt.annotate(f'R${height:.2f}'.replace('.', ','),
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 3),  # 3 points vertical offset
                   textcoords="offset points",
                   ha='center', va='bottom', fontsize=12)
    
    plt.xticks([0, 1], ['Entradas', 'Saídas'], fontsize=12)
    plt.title(f'Entradas vs Saídas - {titulo}', fontsize=16, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    
    # Remover eixo x
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)
    
    # Salvar em memória
    buf1 = BytesIO()
    plt.tight_layout()
    plt.savefig(buf1, format='png', dpi=100)
    buf1.seek(0)
    
    # 2. Gráfico de pizza para categorias de saída
    if saidas_total > 0:
        plt.figure(figsize=(10, 6))
        
        # Agrupar por categoria para o gráfico de pizza
        saidas = df[df['tipo'] == 'saida']
        categorias_saida = saidas.groupby('categoria')['valor'].sum()
        
        # Ordenar do maior para o menor
        categorias_saida = categorias_saida.sort_values(ascending=False)
        
        # Pegar as top 5 categorias e agrupar o resto como "Outros"
        if len(categorias_saida) > 5:
            top_categorias = categorias_saida.head(5)
            outros = pd.Series({'Outros': categorias_saida[5:].sum()})
            categorias_plot = pd.concat([top_categorias, outros])
        else:
            categorias_plot = categorias_saida
            
        # Cores atraentes
        cores = plt.cm.tab10(np.linspace(0, 1, len(categorias_plot)))
        
        # Gráfico de pizza com percentuais
        explode = [0.05] * len(categorias_plot)  # Explode all slices
        wedges, texts, autotexts = plt.pie(
            categorias_plot.values, 
            labels=categorias_plot.index, 
            autopct='%1.1f%%', 
            startangle=90, 
            shadow=True, 
            explode=explode,
            colors=cores,
            textprops={'fontsize': 12}
        )
        
        # Tornar os percentuais em negrito
        for autotext in autotexts:
            autotext.set_fontweight('bold')
            
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.title('Distribuição de Gastos por Categoria', fontsize=16, fontweight='bold')
        
        # Salvar em memória
        buf2 = BytesIO()
        plt.tight_layout()
        plt.savefig(buf2, format='png', dpi=100)
        buf2.seek(0)
    else:
        buf2 = None
    
    # 3. Gráfico de linha para fluxo diário, se houver dados suficientes
    if len(df['date_only'].unique()) > 1:
        plt.figure(figsize=(10, 6))
        
        # Agrupar por data
        fluxo_diario = df.groupby(['date_only', 'tipo'])['valor'].sum().unstack().fillna(0)
        
        # Calcular saldo diário acumulado
        if 'entrada' not in fluxo_diario.columns:
            fluxo_diario['entrada'] = 0
        if 'saida' not in fluxo_diario.columns:
            fluxo_diario['saida'] = 0
            
        fluxo_diario['saldo'] = fluxo_diario['entrada'] - fluxo_diario['saida']
        fluxo_diario['saldo_acumulado'] = fluxo_diario['saldo'].cumsum()
        
        # Plotar linhas
        plt.plot(fluxo_diario.index, fluxo_diario['entrada'], 'g-', linewidth=2.5, marker='o', label='Entradas')
        plt.plot(fluxo_diario.index, fluxo_diario['saida'], 'r-', linewidth=2.5, marker='o', label='Saídas')
        plt.plot(fluxo_diario.index, fluxo_diario['saldo_acumulado'], 'b-', linewidth=2.5, marker='s', label='Saldo Acumulado')
        
        plt.title('Fluxo de Caixa Diário', fontsize=16, fontweight='bold')
        plt.xlabel('Data', fontsize=12)
        plt.ylabel('Valor (R$)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=12)
        
        # Formatar datas no eixo x
        plt.gcf().autofmt_xdate()
        
        # Salvar em memória
        buf3 = BytesIO()
        plt.tight_layout()
        plt.savefig(buf3, format='png', dpi=100)
        buf3.seek(0)
    else:
        buf3 = None
        
    # 4. Gráfico de barras horizontais para top categorias
    plt.figure(figsize=(10, 6))
    
    # Agrupar por categoria e tipo
    categorias = df.groupby(['categoria', 'tipo'])['valor'].sum().unstack().fillna(0)
    
    # Ordenar por valor total
    categorias['total'] = categorias['entrada'] - categorias['saida']
    categorias = categorias.sort_values('total', ascending=True)
    
    # Pegar as top 10 categorias
    top_categorias = categorias.head(10)
    
    # Criar gráfico de barras horizontais
    y_pos = np.arange(len(top_categorias))
    plt.barh(y_pos, top_categorias['entrada'], color='green', alpha=0.7, label='Entradas')
    plt.barh(y_pos, -top_categorias['saida'], color='red', alpha=0.7, label='Saídas')
    
    plt.yticks(y_pos, top_categorias.index)
    plt.xlabel('Valor (R$)', fontsize=12)
    plt.title('Top 10 Categorias por Movimentação', fontsize=16, fontweight='bold')
    plt.legend()
    plt.grid(axis='x', alpha=0.3)
    
    # Salvar em memória
    buf4 = BytesIO()
    plt.tight_layout()
    plt.savefig(buf4, format='png', dpi=100)
    buf4.seek(0)
    
    # Enviar os gráficos
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=buf1,
        caption=f"{EMOJI['grafico']} Entradas vs Saídas - {titulo}"
    )
    
    if buf2:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=buf2,
            caption=f"{EMOJI['grafico']} Distribuição de Gastos por Categoria"
        )
    
    if buf3:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=buf3,
            caption=f"{EMOJI['grafico']} Fluxo de Caixa Diário"
        )
        
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=buf4,
        caption=f"{EMOJI['grafico']} Top 10 Categorias por Movimentação"
    )
    
    # Atualizar mensagem
    await query.edit_message_text(
        f"{EMOJI['sucesso']} Gráficos gerados com sucesso para o {titulo}!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{EMOJI['relatorio']} Voltar aos Relatórios", callback_data='voltar_relatorios')],
            [InlineKeyboardButton(f"{EMOJI['voltar']} Menu Principal", callback_data='voltar_menu')]
        ])
    )
    
    return RELATORIO

# Função para voltar ao menu de relatórios
async def voltar_relatorios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton(f"{EMOJI['calendario']} Relatório do Dia", callback_data='relatorio_dia'),
            InlineKeyboardButton(f"{EMOJI['calendario']} Relatório da Semana", callback_data='relatorio_semana')
        ],
        [
            InlineKeyboardButton(f"{EMOJI['calendario']} Relatório do Mês", callback_data='relatorio_mes'),
            InlineKeyboardButton(f"{EMOJI['lupa']} Relatório Personalizado", callback_data='relatorio_personalizado')
        ],
        [InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]
    ]
    
    await query.edit_message_text(
        f"{EMOJI['relatorio']} *Relatórios Financeiros*\n\nEscolha o tipo de relatório que deseja visualizar:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return RELATORIO

# Função para preparar fechamento de caixa
async def preparar_fechamento_caixa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    logger.info("Preparando fechamento de caixa")
    
    # Obter data atual
    hoje = datetime.datetime.now()
    data_inicio = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
    data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Filtrar transações do dia
    transacoes_dia = []
    for t in dados['transacoes']:
        try:
            data_transacao = datetime.datetime.strptime(t['data'], "%d/%m/%Y %H:%M:%S")
            if data_inicio <= data_transacao <= data_fim:
                transacoes_dia.append(t)
        except Exception as e:
            logger.error(f"Erro ao processar data da transação: {str(e)}")
            continue
    
    logger.info(f"Encontradas {len(transacoes_dia)} transações no dia")
    
    # Calcular totais
    total_entradas = sum(t['valor'] for t in transacoes_dia if t['tipo'] == 'entrada')
    total_saidas = sum(t['valor'] for t in transacoes_dia if t['tipo'] == 'saida')
    saldo_dia = total_entradas - total_saidas
    
    # Agrupar por categorias
    categorias_entrada = {}
    categorias_saida = {}
    
    for t in transacoes_dia:
        if t['tipo'] == 'entrada':
            categorias_entrada[t['categoria']] = categorias_entrada.get(t['categoria'], 0) + t['valor']
        else:
            categorias_saida[t['categoria']] = categorias_saida.get(t['categoria'], 0) + t['valor']
    
    # Armazenar dados para confirmação
    context.user_data['fechamento'] = {
        'data': obter_data_hoje(),
        'saldo_inicial': dados['saldo_atual'] - saldo_dia,
        'saldo_final': dados['saldo_atual'],
        'total_entradas': total_entradas,
        'total_saidas': total_saidas
    }
    
    # Preparar texto de fechamento
    texto = f"{EMOJI['fechamento']} *Fechamento de Caixa*\n\n"
    texto += f"{EMOJI['calendario']} Data: *{obter_data_hoje()}*\n\n"
    texto += f"{EMOJI['saldo']} Saldo Inicial: *{formatar_valor(dados['saldo_atual'] - saldo_dia)}*\n"
    texto += f"{EMOJI['entrada']} Total de Entradas: *{formatar_valor(total_entradas)}*\n"
    texto += f"{EMOJI['saida']} Total de Saídas: *{formatar_valor(total_saidas)}*\n"
    texto += f"{EMOJI['saldo']} Saldo Final: *{formatar_valor(dados['saldo_atual'])}*\n\n"
    
    if categorias_entrada:
        texto += f"{EMOJI['entrada']} *Entradas por Categoria*\n"
        for cat, valor in sorted(categorias_entrada.items(), key=lambda x: x[1], reverse=True):
            texto += f"• {cat}: *{formatar_valor(valor)}*\n"
        texto += "\n"
    
    if categorias_saida:
        texto += f"{EMOJI['saida']} *Saídas por Categoria*\n"
        for cat, valor in sorted(categorias_saida.items(), key=lambda x: x[1], reverse=True):
            texto += f"• {cat}: *{formatar_valor(valor)}*\n"
        texto += "\n"
    
    texto += f"Total de transações: *{len(transacoes_dia)}*\n\n"
    texto += "Deseja confirmar este fechamento de caixa?"
    
    # Botões para confirmação
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['confirmar']} Confirmar Fechamento", callback_data='confirmar_fechamento')],
        [InlineKeyboardButton(f"{EMOJI['cancelar']} Cancelar", callback_data='voltar_menu')]
    ]
    
    logger.info("Enviando mensagem de fechamento")
    await query.edit_message_text(
        texto,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CONFIRMAR_FECHAMENTO_CAIXA

# Função para confirmar fechamento de caixa
async def confirmar_fechamento_caixa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    logger.info("Processando confirmação de fechamento")
    
    if query.data == 'voltar_menu':
        return await menu_principal(update, context)
    
    if query.data != 'confirmar_fechamento':
        logger.error(f"Callback inválido: {query.data}")
        await query.edit_message_text(
            f"{EMOJI['erro']} Erro ao processar o fechamento de caixa. Por favor, tente novamente.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar ao Menu", callback_data='voltar_menu')]])
        )
        return MENU_PRINCIPAL
    
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    # Registrar fechamento
    if 'fechamento' in context.user_data:
        fechamento = context.user_data['fechamento']
        
        logger.info(f"Registrando fechamento: {fechamento}")
        
        # Adicionar ao histórico de fechamentos
        if 'fechamentos' not in dados:
            dados['fechamentos'] = []
        
        dados['fechamentos'].append(fechamento)
        dados['data_ultimo_fechamento'] = fechamento['data']
        
        # Salvar dados
        salvar_dados_usuario(user_id, dados)
        
        # Gerar relatório do fechamento
        texto = f"{EMOJI['sucesso']} *Fechamento de Caixa Realizado*\n\n"
        texto += f"{EMOJI['calendario']} Data: *{fechamento['data']}*\n\n"
        texto += f"{EMOJI['saldo']} Saldo Inicial: *{formatar_valor(fechamento['saldo_inicial'])}*\n"
        texto += f"{EMOJI['entrada']} Total de Entradas: *{formatar_valor(fechamento['total_entradas'])}*\n"
        texto += f"{EMOJI['saida']} Total de Saídas: *{formatar_valor(fechamento['total_saidas'])}*\n"
        texto += f"{EMOJI['saldo']} Saldo Final: *{formatar_valor(fechamento['saldo_final'])}*\n\n"
        texto += "O fechamento de caixa foi registrado com sucesso!"
        
        # Criar um arquivo de comprovante
        output = BytesIO()
        output.write(texto.encode('utf-8'))
        output.seek(0)
        
        # Enviar arquivo
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=output,
            filename=f"fechamento_{fechamento['data'].replace('/', '-')}.txt",
            caption=f"{EMOJI['fechamento']} Comprovante de Fechamento de Caixa"
        )
        
        # Atualizar mensagem
        await query.edit_message_text(
            f"{EMOJI['sucesso']} *Fechamento de Caixa Realizado*\n\n"
            f"O fechamento de caixa para *{fechamento['data']}* foi registrado com sucesso!\n\n"
            f"Saldo atual: *{formatar_valor(fechamento['saldo_final'])}*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar ao Menu", callback_data='voltar_menu')]])
        )
        
        # Limpar dados temporários
        if 'fechamento' in context.user_data:
            del context.user_data['fechamento']
    else:
        logger.error("Dados de fechamento não encontrados em context.user_data")
        await query.edit_message_text(
            f"{EMOJI['erro']} Erro ao processar o fechamento de caixa. Por favor, tente novamente.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar ao Menu", callback_data='voltar_menu')]])
        )
    
    return MENU_PRINCIPAL

# Funções para configurações
async def callback_configuracoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    opcao = query.data
    
    if opcao == 'voltar_menu':
        return await menu_principal(update, context)
    
    elif opcao == 'add_cat_entrada':
        await query.edit_message_text(
            f"{EMOJI['adicionar']} *Adicionar Categoria de Entrada*\n\n"
            f"Digite o nome da nova categoria de entrada:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]])
        )
        context.user_data['add_categoria_tipo'] = 'entrada'
        return ADICIONAR_CATEGORIA
    
    elif opcao == 'add_cat_saida':
        await query.edit_message_text(
            f"{EMOJI['adicionar']} *Adicionar Categoria de Saída*\n\n"
            f"Digite o nome da nova categoria de saída:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]])
        )
        context.user_data['add_categoria_tipo'] = 'saida'
        return ADICIONAR_CATEGORIA
    
    elif opcao == 'editar_cat_entrada':
        user_id = update.effective_user.id
        dados = carregar_dados_usuario(user_id)
        categorias = dados['categorias_entrada']
        
        keyboard = []
        row = []
        for i, cat in enumerate(categorias):
            if cat != "Outro":  # Não permitir editar a categoria "Outro"
                row.append(InlineKeyboardButton(f"{EMOJI['editar']} {cat}", callback_data=f"edit_cat_entrada_{cat}"))
                
                # Dois botões por linha
                if len(row) == 2 or i == len(categorias) - 1:
                    keyboard.append(row)
                    row = []
                    
        keyboard.append([InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')])
        
        await query.edit_message_text(
            f"{EMOJI['editar']} *Editar Categoria de Entrada*\n\n"
            f"Selecione a categoria que deseja editar:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return EDITAR_CATEGORIA
    
    elif opcao == 'editar_cat_saida':
        user_id = update.effective_user.id
        dados = carregar_dados_usuario(user_id)
        categorias = dados['categorias_saida']
        
        keyboard = []
        row = []
        for i, cat in enumerate(categorias):
            if cat != "Outro":  # Não permitir editar a categoria "Outro"
                row.append(InlineKeyboardButton(f"{EMOJI['editar']} {cat}", callback_data=f"edit_cat_saida_{cat}"))
                
                # Dois botões por linha
                if len(row) == 2 or i == len(categorias) - 1:
                    keyboard.append(row)
                    row = []
                    
        keyboard.append([InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')])
        
        await query.edit_message_text(
            f"{EMOJI['editar']} *Editar Categoria de Saída*\n\n"
            f"Selecione a categoria que deseja editar:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return EDITAR_CATEGORIA
    
    elif opcao == 'remover_cat_entrada':
        user_id = update.effective_user.id
        dados = carregar_dados_usuario(user_id)
        categorias = dados['categorias_entrada']
        
        if len(categorias) <= 1:
            await query.edit_message_text(
                f"{EMOJI['alerta']} Não é possível remover mais categorias de entrada. Deve haver pelo menos uma categoria.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]])
            )
            return CONFIGURACOES
        
        keyboard = []
        row = []
        for i, cat in enumerate(categorias):
            if cat != "Outro":  # Não permitir remover a categoria "Outro"
                row.append(InlineKeyboardButton(f"{EMOJI['remover']} {cat}", callback_data=f"rem_cat_entrada_{cat}"))
                
                # Dois botões por linha
                if len(row) == 2 or i == len(categorias) - 1:
                    keyboard.append(row)
                    row = []
                    
        keyboard.append([InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')])
        
        await query.edit_message_text(
            f"{EMOJI['remover']} *Remover Categoria de Entrada*\n\n"
            f"Selecione a categoria que deseja remover:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return REMOVER_CATEGORIA
    
    elif opcao == 'remover_cat_saida':
        user_id = update.effective_user.id
        dados = carregar_dados_usuario(user_id)
        categorias = dados['categorias_saida']
        
        if len(categorias) <= 1:
            await query.edit_message_text(
                f"{EMOJI['alerta']} Não é possível remover mais categorias de saída. Deve haver pelo menos uma categoria.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]])
            )
            return CONFIGURACOES
        
        keyboard = []
        row = []
        for i, cat in enumerate(categorias):
            if cat != "Outro":  # Não permitir remover a categoria "Outro"
                row.append(InlineKeyboardButton(f"{EMOJI['remover']} {cat}", callback_data=f"rem_cat_saida_{cat}"))
                
                # Dois botões por linha
                if len(row) == 2 or i == len(categorias) - 1:
                    keyboard.append(row)
                    row = []
                    
        keyboard.append([InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')])
        
        await query.edit_message_text(
            f"{EMOJI['remover']} *Remover Categoria de Saída*\n\n"
            f"Selecione a categoria que deseja remover:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return REMOVER_CATEGORIA
    
    elif opcao == 'exportar_dados':
        await exportar_todos_dados(update, context)
        return CONFIGURACOES
    
    elif opcao == 'config_notificacoes':
        # Configurar notificações
        user_id = update.effective_user.id
        dados = carregar_dados_usuario(user_id)
        
        notificacoes = dados.get('notificacoes', {
            'alerta_limite': True,
            'lembrete_diario': False
        })
        
        keyboard = [
            [InlineKeyboardButton(
                f"{'✅' if notificacoes.get('alerta_limite', True) else '❌'} Alertas de Limite",
                callback_data='toggle_alerta_limite'
            )],
            [InlineKeyboardButton(
                f"{'✅' if notificacoes.get('lembrete_diario', False) else '❌'} Lembretes Diários",
                callback_data='toggle_lembrete_diario'
            )],
            [InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]
        ]
        
        await query.edit_message_text(
            f"{EMOJI['alerta']} *Configurações de Notificações*\n\n"
            f"Personalize como deseja receber notificações:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIGURACOES
    
    elif opcao == 'toggle_alerta_limite' or opcao == 'toggle_lembrete_diario':
        user_id = update.effective_user.id
        dados = carregar_dados_usuario(user_id)
        
        if 'notificacoes' not in dados:
            dados['notificacoes'] = {
                'alerta_limite': True,
                'lembrete_diario': False
            }
        
        if opcao == 'toggle_alerta_limite':
            dados['notificacoes']['alerta_limite'] = not dados['notificacoes'].get('alerta_limite', True)
        else:
            dados['notificacoes']['lembrete_diario'] = not dados['notificacoes'].get('lembrete_diario', False)
        
        salvar_dados_usuario(user_id, dados)
        
        # Atualizar menu de notificações
        notificacoes = dados['notificacoes']
        
        keyboard = [
            [InlineKeyboardButton(
                f"{'✅' if notificacoes.get('alerta_limite', True) else '❌'} Alertas de Limite",
                callback_data='toggle_alerta_limite'
            )],
            [InlineKeyboardButton(
                f"{'✅' if notificacoes.get('lembrete_diario', False) else '❌'} Lembretes Diários",
                callback_data='toggle_lembrete_diario'
            )],
            [InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]
        ]
        
        await query.edit_message_text(
            f"{EMOJI['alerta']} *Configurações de Notificações*\n\n"
            f"Configurações atualizadas! Personalize como deseja receber notificações:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIGURACOES
    
    elif opcao == 'voltar_config':
        keyboard = [
            [
                InlineKeyboardButton(f"{EMOJI['adicionar']} Categoria Entrada", callback_data='add_cat_entrada'),
                InlineKeyboardButton(f"{EMOJI['adicionar']} Categoria Saída", callback_data='add_cat_saida')
            ],
            [
                InlineKeyboardButton(f"{EMOJI['editar']} Editar Cat. Entrada", callback_data='editar_cat_entrada'),
                InlineKeyboardButton(f"{EMOJI['editar']} Editar Cat. Saída", callback_data='editar_cat_saida')
            ],
            [
                InlineKeyboardButton(f"{EMOJI['remover']} Remover Cat. Entrada", callback_data='remover_cat_entrada'),
                InlineKeyboardButton(f"{EMOJI['remover']} Remover Cat. Saída", callback_data='remover_cat_saida')
            ],
            [
                InlineKeyboardButton(f"{EMOJI['exportar']} Exportar Dados", callback_data='exportar_dados'),
                InlineKeyboardButton(f"{EMOJI['alerta']} Notificações", callback_data='config_notificacoes')
            ],
            [
                InlineKeyboardButton(f"{EMOJI['erro']} Apagar Dados", callback_data='apagar_dados')
            ],
            [InlineKeyboardButton(f"{EMOJI['voltar']} Voltar ao Menu Principal", callback_data='voltar_menu')]
        ]
        await query.edit_message_text(
            f"{EMOJI['config']} *Configurações*\n\n"
            f"Personalize seu assistente financeiro:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIGURACOES
    
    elif opcao == 'apagar_dados':
        keyboard = [
            [InlineKeyboardButton(f"{EMOJI['alerta']} Sim, apagar todos os dados", callback_data='confirmar_apagar_dados')],
            [InlineKeyboardButton(f"{EMOJI['voltar']} Não, voltar", callback_data='voltar_config')]
        ]
        
        await query.edit_message_text(
            f"{EMOJI['alerta']} *Atenção!*\n\n"
            f"Você está prestes a apagar TODOS os seus dados financeiros, incluindo:\n"
            f"• Todas as transações\n"
            f"• Histórico de fechamentos\n"
            f"• Categorias personalizadas\n"
            f"• Metas e configurações\n\n"
            f"Esta ação NÃO pode ser desfeita!\n\n"
            f"Tem certeza que deseja continuar?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIRMAR_APAGAR_DADOS
    
    return CONFIGURACOES

# Função para adicionar categoria
async def adicionar_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == 'voltar_config':
            return await callback_configuracoes(update, context)
        return ADICIONAR_CATEGORIA
    
    nome_categoria = update.message.text.strip()
    
    if not nome_categoria or len(nome_categoria) < 2:
        await update.message.reply_text(
            f"{EMOJI['erro']} Nome de categoria inválido. O nome deve ter pelo menos 2 caracteres.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]])
        )
        return ADICIONAR_CATEGORIA
    
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    tipo = context.user_data.get('add_categoria_tipo', 'entrada')
    campo = f"categorias_{tipo}"
    
    # Verificar se a categoria já existe
    if nome_categoria in dados[campo]:
        await update.message.reply_text(
            f"{EMOJI['alerta']} A categoria '{nome_categoria}' já existe para {tipo}s.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]])
        )
        return ADICIONAR_CATEGORIA
    
    # Adicionar nova categoria
    dados[campo].append(nome_categoria)
    salvar_dados_usuario(user_id, dados)
    
    # Atualizar os dados em context
    context.user_data['dados'] = dados
    
    # Confirmar para o usuário
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['adicionar']} Adicionar Outra Categoria", callback_data=f"add_cat_{tipo}")],
        [InlineKeyboardButton(f"{EMOJI['voltar']} Voltar às Configurações", callback_data='voltar_config')],
        [InlineKeyboardButton(f"{EMOJI['voltar']} Menu Principal", callback_data='voltar_menu')]
    ]
    
    await update.message.reply_text(
        f"{EMOJI['sucesso']} Categoria '*{nome_categoria}*' adicionada com sucesso às categorias de {tipo}!",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CONFIGURACOES

# Função para exportar todos os dados
async def exportar_todos_dados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    # Verificar se há dados para exportar
    if not dados['transacoes']:
        await query.edit_message_text(
            f"{EMOJI['info']} Não há transações para exportar.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]])
        )
        return
    
    # Criar DataFrame para transações
    df = pd.DataFrame(dados['transacoes'])
    
    # Criar CSV em memória
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)
    
    # Enviar arquivo CSV
    data_atual = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=output,
        filename=f"financas_{data_atual}.csv",
        caption=f"{EMOJI['exportar']} Exportação de {len(dados['transacoes'])} transações (CSV)"
    )
    
    # Exportar como JSON também
    output_json = BytesIO()
    output_json.write(json.dumps(dados, ensure_ascii=False, indent=2, default=str).encode('utf-8'))
    output_json.seek(0)
    
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=output_json,
        filename=f"financas_{data_atual}.json",
        caption=f"{EMOJI['exportar']} Exportação completa em formato JSON"
    )
    
    # Criar relatórios detalhados
    try:
        # Relatório de entradas por categoria
        entradas_df = df[df['tipo'] == 'entrada'].copy()
        if not entradas_df.empty:
            output_entradas = BytesIO()
            entradas_df.to_csv(output_entradas, index=False, encoding='utf-8')
            output_entradas.seek(0)
            
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=output_entradas,
                filename=f"entradas_{data_atual}.csv",
                caption=f"{EMOJI['entrada']} Relatório detalhado de entradas"
            )
        
        # Relatório de saídas por categoria
        saidas_df = df[df['tipo'] == 'saida'].copy()
        if not saidas_df.empty:
            output_saidas = BytesIO()
            saidas_df.to_csv(output_saidas, index=False, encoding='utf-8')
            output_saidas.seek(0)
            
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=output_saidas,
                filename=f"saidas_{data_atual}.csv",
                caption=f"{EMOJI['saida']} Relatório detalhado de saídas"
            )
            
        # Relatório de fechamentos
        if 'fechamentos' in dados and dados['fechamentos']:
            fechamentos_df = pd.DataFrame(dados['fechamentos'])
            output_fechamentos = BytesIO()
            fechamentos_df.to_csv(output_fechamentos, index=False, encoding='utf-8')
            output_fechamentos.seek(0)
            
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=output_fechamentos,
                filename=f"fechamentos_{data_atual}.csv",
                caption=f"{EMOJI['fechamento']} Histórico de fechamentos de caixa"
            )
            
        # Relatório de metas
        if 'metas' in dados:
            metas_df = pd.DataFrame([dados['metas']])
            output_metas = BytesIO()
            metas_df.to_csv(output_metas, index=False, encoding='utf-8')
            output_metas.seek(0)
            
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=output_metas,
                filename=f"metas_{data_atual}.csv",
                caption=f"{EMOJI['grafico']} Metas financeiras"
            )
            
    except Exception as e:
        logger.error(f"Erro ao exportar relatórios detalhados: {e}")
    
    # Atualizar mensagem
    await query.edit_message_text(
        f"{EMOJI['sucesso']} *Dados exportados com sucesso!*\n\n"
        f"• {len(dados['transacoes'])} transações exportadas\n"
        f"• Formatos: CSV e JSON\n"
        f"• Relatórios detalhados de entradas e saídas\n"
        f"• Histórico de fechamentos\n"
        f"• Metas financeiras\n\n"
        f"Os arquivos foram enviados acima.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]])
    )

# Função para remover categoria
async def remover_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'voltar_config':
        return await callback_configuracoes(update, context)
    
    # Extrair informações da callback_data
    partes = query.data.split('_')
    tipo = partes[2]  # entrada ou saida
    categoria = '_'.join(partes[3:])  # nome da categoria (pode conter underscores)
    
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    # Verificar se a categoria está em uso
    categoria_em_uso = False
    for transacao in dados['transacoes']:
        if transacao['categoria'] == categoria:
            categoria_em_uso = True
            break
    
    if categoria_em_uso:
        keyboard = [
            [InlineKeyboardButton(f"{EMOJI['confirmar']} Sim, trocar para 'Outro'", callback_data=f'confirm_rem_{tipo}_{categoria}')],
            [InlineKeyboardButton(f"{EMOJI['cancelar']} Não, cancelar", callback_data='voltar_config')]
        ]
        
        await query.edit_message_text(
            f"{EMOJI['alerta']} *Atenção*\n\n"
            f"A categoria '{categoria}' está sendo usada em {sum(1 for t in dados['transacoes'] if t['categoria'] == categoria)} transações.\n\n"
            f"Deseja realmente removê-la? Todas as transações desta categoria serão alteradas para 'Outro'.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return REMOVER_CATEGORIA
    
    # Se não estiver em uso, remover diretamente
    await remover_categoria_confirmado(update, context, tipo, categoria)
    
    return CONFIGURACOES

# Função para confirmar remoção de categoria em uso
async def remover_categoria_confirmado(update: Update, context, tipo=None, categoria=None):
    query = update.callback_query
    
    # Se for chamado por confirmação de callback
    if tipo is None and categoria is None:
        partes = query.data.split('_')
        tipo = partes[2]  # entrada ou saida
        categoria = '_'.join(partes[3:])  # nome da categoria (pode conter underscores)
    
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    # Atualizar categorias nas transações
    count_alteracoes = 0
    for transacao in dados['transacoes']:
        if transacao['categoria'] == categoria:
            transacao['categoria'] = 'Outro'
            count_alteracoes += 1
    
    # Remover a categoria
    campo = f"categorias_{tipo}"
    if categoria in dados[campo]:
        dados[campo].remove(categoria)
        salvar_dados_usuario(user_id, dados)
        
        mensagem_sucesso = (
            f"{EMOJI['sucesso']} Categoria '*{categoria}*' removida com sucesso das categorias de {tipo}!"
        )
        
        if count_alteracoes > 0:
            mensagem_sucesso += f"\n\n{count_alteracoes} transações foram atualizadas para a categoria 'Outro'."
        
        await query.edit_message_text(
            mensagem_sucesso,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{EMOJI['remover']} Remover Outra Categoria", callback_data=f'remover_cat_{tipo}')],
                [InlineKeyboardButton(f"{EMOJI['voltar']} Voltar às Configurações", callback_data='voltar_config')],
                [InlineKeyboardButton(f"{EMOJI['voltar']} Menu Principal", callback_data='voltar_menu')]
            ])
        )
    else:
        await query.edit_message_text(
            f"{EMOJI['erro']} Erro: Categoria '{categoria}' não encontrada.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]])
        )
    
    return CONFIGURACOES

# Função para lidar com mensagens não reconhecidas
async def mensagem_desconhecida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{EMOJI['info']} Desculpe, não entendi esse comando. Por favor, use o menu ou digite /start para começar.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Menu Principal", callback_data='voltar_menu')]])
    )
    return MENU_PRINCIPAL

# Função para editar categoria
async def editar_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'voltar_config':
        return await callback_configuracoes(update, context)
    
    # Extrair informações da callback_data
    partes = query.data.split('_')
    tipo = partes[2]  # entrada ou saida
    categoria_antiga = '_'.join(partes[3:])  # nome da categoria (pode conter underscores)
    
    context.user_data['edit_categoria'] = {
        'tipo': tipo,
        'categoria_antiga': categoria_antiga
    }
    
    await query.edit_message_text(
        f"{EMOJI['editar']} *Editar Categoria*\n\n"
        f"Digite o novo nome para a categoria '*{categoria_antiga}*':",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]])
    )
    
    return EDITAR_CATEGORIA

# Função para processar a edição da categoria
async def processar_edicao_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == 'voltar_config':
            return await callback_configuracoes(update, context)
        return EDITAR_CATEGORIA
    
    nova_categoria = update.message.text.strip()
    
    if not nova_categoria or len(nova_categoria) < 2:
        await update.message.reply_text(
            f"{EMOJI['erro']} Nome de categoria inválido. O nome deve ter pelo menos 2 caracteres.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]])
        )
        return EDITAR_CATEGORIA
    
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    edit_info = context.user_data.get('edit_categoria', {})
    tipo = edit_info.get('tipo')
    categoria_antiga = edit_info.get('categoria_antiga')
    
    if not tipo or not categoria_antiga:
        await update.message.reply_text(
            f"{EMOJI['erro']} Erro ao processar a edição. Por favor, tente novamente.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]])
        )
        return CONFIGURACOES
    
    campo = f"categorias_{tipo}"
    
    # Verificar se a nova categoria já existe
    if nova_categoria in dados[campo]:
        await update.message.reply_text(
            f"{EMOJI['alerta']} A categoria '*{nova_categoria}*' já existe para {tipo}s.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_config')]])
        )
        return EDITAR_CATEGORIA
    
    # Contar quantas transações serão afetadas
    transacoes_afetadas = sum(1 for t in dados['transacoes'] if t['categoria'] == categoria_antiga)
    
    # Atualizar a categoria em todas as transações
    for transacao in dados['transacoes']:
        if transacao['categoria'] == categoria_antiga:
            transacao['categoria'] = nova_categoria
    
    # Atualizar a lista de categorias
    try:
        idx = dados[campo].index(categoria_antiga)
        dados[campo][idx] = nova_categoria
    except ValueError:
        # Se a categoria não for encontrada, adicionar a nova
        dados[campo].append(nova_categoria)
    
    # Salvar as alterações
    salvar_dados_usuario(user_id, dados)
    
    # Limpar dados temporários
    if 'edit_categoria' in context.user_data:
        del context.user_data['edit_categoria']
    
    # Confirmar para o usuário
    mensagem_sucesso = (
        f"{EMOJI['sucesso']} Categoria '*{categoria_antiga}*' renomeada para '*{nova_categoria}*' com sucesso!"
    )
    
    if transacoes_afetadas > 0:
        mensagem_sucesso += f"\n\n{transacoes_afetadas} transações foram atualizadas com o novo nome."
    
    keyboard = [
        [InlineKeyboardButton(f"{EMOJI['editar']} Editar Outra Categoria", callback_data=f'editar_cat_{tipo}')],
        [InlineKeyboardButton(f"{EMOJI['voltar']} Voltar às Configurações", callback_data='voltar_config')],
        [InlineKeyboardButton(f"{EMOJI['voltar']} Menu Principal", callback_data='voltar_menu')]
    ]
    
    await update.message.reply_text(
        mensagem_sucesso,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CONFIGURACOES

# Função para gerar gráficos de análise
async def gerar_grafico_analise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    dados = carregar_dados_usuario(user_id)
    
    if not dados['transacoes'] or len(dados['transacoes']) < 5:
        await query.edit_message_text(
            f"{EMOJI['info']} Você precisa ter pelo menos 5 transações para gerar análises detalhadas.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
        return MENU_PRINCIPAL
    
    # Criar DataFrame para análise
    df = pd.DataFrame(dados['transacoes'])
    df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y %H:%M:%S')
    df['mes'] = df['data'].dt.month
    df['ano'] = df['data'].dt.year
    
    # Análise por mês
    try:
        # Agrupar por mês e tipo
        analise_mensal = df.groupby(['ano', 'mes', 'tipo'])['valor'].sum().unstack(fill_value=0).reset_index()
        
        # Criar rótulos para o eixo x
        analise_mensal['mes_ano'] = analise_mensal.apply(lambda row: f"{row['mes']}/{row['ano']}", axis=1)
        
        # Criar gráfico de barras para análise mensal
        plt.figure(figsize=(12, 6))
        
        # Se não houver colunas de entrada ou saída, adicionar como zeros
        if 'entrada' not in analise_mensal.columns:
            analise_mensal['entrada'] = 0
        if 'saida' not in analise_mensal.columns:
            analise_mensal['saida'] = 0
        
        # Calcular o saldo mensal
        analise_mensal['saldo'] = analise_mensal['entrada'] - analise_mensal['saida']
        
        # Criar gráfico de barras agrupadas
        bar_width = 0.25
        indices = np.arange(len(analise_mensal))
        
        plt.bar(indices - bar_width, analise_mensal['entrada'], bar_width, label='Entradas', color='green', alpha=0.7)
        plt.bar(indices, analise_mensal['saida'], bar_width, label='Saídas', color='red', alpha=0.7)
        plt.bar(indices + bar_width, analise_mensal['saldo'], bar_width, label='Saldo', color='blue', alpha=0.7)
        
        # Adicionar rótulos e título
        plt.xlabel('Mês/Ano', fontsize=12)
        plt.ylabel('Valor (R$)', fontsize=12)
        plt.title('Análise Financeira Mensal', fontsize=16, fontweight='bold')
        plt.xticks(indices, analise_mensal['mes_ano'], rotation=45)
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        # Salvar em memória
        buf1 = BytesIO()
        plt.savefig(buf1, format='png', dpi=100)
        buf1.seek(0)
        
        # Enviar primeiro gráfico
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=buf1,
            caption=f"{EMOJI['grafico']} Análise Financeira Mensal"
        )
        
        # Gráfico de tendência de saldo
        plt.figure(figsize=(12, 6))
        
        # Ordenar por data e criar uma coluna de saldo acumulado
        df_ordenado = df.sort_values('data')
        df_ordenado['valor_ajustado'] = df_ordenado.apply(lambda row: row['valor'] if row['tipo'] == 'entrada' else -row['valor'], axis=1)
        df_ordenado['saldo_acumulado'] = df_ordenado['valor_ajustado'].cumsum()
        
        # Plotar a tendência do saldo
        plt.plot(df_ordenado['data'], df_ordenado['saldo_acumulado'], 'b-', linewidth=2.5, marker='o', markersize=4)
        
        plt.xlabel('Data', fontsize=12)
        plt.ylabel('Saldo Acumulado (R$)', fontsize=12)
        plt.title('Evolução do Saldo ao Longo do Tempo', fontsize=16, fontweight='bold')
        plt.grid(True, alpha=0.3)
        
        # Formatar eixo Y para valores monetários
        from matplotlib.ticker import FuncFormatter
        def format_real(x, pos):
            return f'R${x:.0f}'
        plt.gca().yaxis.set_major_formatter(FuncFormatter(format_real))
        
        # Formatar datas no eixo x
        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        
        # Salvar em memória
        buf2 = BytesIO()
        plt.savefig(buf2, format='png', dpi=100)
        buf2.seek(0)
        
        # Enviar segundo gráfico
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=buf2,
            caption=f"{EMOJI['grafico']} Evolução do Saldo ao Longo do Tempo"
        )
        
        # Atualizar mensagem
        await query.edit_message_text(
            f"{EMOJI['sucesso']} Análise financeira gerada com sucesso!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar ao Menu", callback_data='voltar_menu')]])
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar análise: {e}")
        await query.edit_message_text(
            f"{EMOJI['erro']} Ocorreu um erro ao gerar a análise financeira. Por favor, tente novamente.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar", callback_data='voltar_menu')]])
        )
    
    return MENU_PRINCIPAL

async def confirmar_apagar_dados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'voltar_config':
        return await callback_configuracoes(update, context)
    
    if query.data == 'confirmar_apagar_dados':
        user_id = update.effective_user.id
        
        # Criar estrutura inicial dos dados
        dados_iniciais = {
            "transacoes": [],
            "categorias_entrada": ["Venda", "Investimento", "Salário", "Outro"],
            "categorias_saida": ["Mercadoria", "Pagamento", "Compra", "Alimentação", "Transporte", "Outro"],
            "saldo_atual": 0,
            "data_ultimo_fechamento": None,
            "metas": {
                "economia_mensal": 0,
                "limite_gastos": 0,
            },
            "notificacoes": {
                "alerta_limite": True,
                "lembrete_diario": False
            }
        }
        
        # Salvar dados iniciais
        salvar_dados_usuario(user_id, dados_iniciais)
        
        # Atualizar dados em context
        context.user_data['dados'] = dados_iniciais
        
        await query.edit_message_text(
            f"{EMOJI['sucesso']} *Dados apagados com sucesso!*\n\n"
            f"Todos os seus dados foram resetados para o estado inicial.\n\n"
            f"Seu saldo atual é: *{formatar_valor(0)}*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{EMOJI['voltar']} Voltar ao Menu", callback_data='voltar_menu')]])
        )
        
        return MENU_PRINCIPAL
    
    return CONFIRMAR_APAGAR_DADOS

# Função principal
def main():
    # Obter o token do bot (substitua pelo seu token real)
    TOKEN = "7965686857:AAHyp28GLe1p5xklh-pcS-QZCByE45T90J8"
    
    # Criar o aplicativo
    application = Application.builder().token(TOKEN).build()
    
    # Adicionar handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU_PRINCIPAL: [
                CallbackQueryHandler(callback_menu_principal)
            ],
            REGISTRAR_TRANSACAO: [
                CallbackQueryHandler(callback_menu_principal)
            ],
            ESCOLHER_TIPO_TRANSACAO: [
                CallbackQueryHandler(callback_menu_principal)
            ],
            INFORMAR_CATEGORIA: [
                CallbackQueryHandler(selecionar_categoria)
            ],
            INFORMAR_VALOR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, informar_valor),
                CallbackQueryHandler(informar_valor)
            ],
            INFORMAR_DESCRICAO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, informar_descricao),
                CallbackQueryHandler(informar_descricao)
            ],
            CONFIRMAR_TRANSACAO: [
                CallbackQueryHandler(confirmar_transacao)
            ],
            RELATORIO: [
                CallbackQueryHandler(menu_principal, pattern='^voltar_menu$'),
                CallbackQueryHandler(voltar_relatorios, pattern='^voltar_relatorios$'),
                CallbackQueryHandler(exportar_relatorio, pattern='^exportar_relatorio$'),
                CallbackQueryHandler(grafico_relatorio, pattern='^grafico_relatorio$'),
                CallbackQueryHandler(callback_relatorios)
            ],
            ESCOLHER_PERIODO_RELATORIO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, escolher_periodo_relatorio),
                CallbackQueryHandler(escolher_periodo_relatorio)
            ],
            CONFIRMAR_FECHAMENTO_CAIXA: [
                CallbackQueryHandler(confirmar_fechamento_caixa, pattern='^confirmar_fechamento$'),
                CallbackQueryHandler(menu_principal, pattern='^voltar_menu$'),
                CallbackQueryHandler(preparar_fechamento_caixa, pattern='^novo_fechamento$')
            ],
            CONFIGURACOES: [
                CallbackQueryHandler(callback_configuracoes)
            ],
            ADICIONAR_CATEGORIA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, adicionar_categoria),
                CallbackQueryHandler(adicionar_categoria)
            ],
            REMOVER_CATEGORIA: [
                CallbackQueryHandler(remover_categoria_confirmado, pattern='^confirm_rem_'),
                CallbackQueryHandler(remover_categoria)
            ],
            EDITAR_CATEGORIA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, processar_edicao_categoria),
                CallbackQueryHandler(editar_categoria)
            ],
            DEFINIR_META: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, definir_meta),
                CallbackQueryHandler(definir_meta)
            ],
            AJUSTAR_SALDO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ajustar_saldo),
                CallbackQueryHandler(ajustar_saldo)
            ],
            CONFIRMAR_APAGAR_DADOS: [
                CallbackQueryHandler(confirmar_apagar_dados, pattern='^confirmar_apagar_dados$'),
                CallbackQueryHandler(callback_configuracoes, pattern='^voltar_config$')
            ]
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    application.add_handler(conv_handler)
    
    # Adicionar handler para mensagens desconhecidas
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensagem_desconhecida))
    
    # Iniciar o bot
    application.run_polling()

if __name__ == '__main__':
    main()