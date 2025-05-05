from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def create_menu():
    keyboard = [
        [
            InlineKeyboardButton("📄 Matrícula", callback_data='matricula'),
            InlineKeyboardButton("💼 Estágio", callback_data='estagio')
        ],
        [
            InlineKeyboardButton("📊 Fluxos de Curso", callback_data='fluxos'),
            InlineKeyboardButton("💬 Digite sua dúvida", callback_data='duvida')
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def create_matricula_menu():
    keyboard = [
        [InlineKeyboardButton("Matrícula Geral", callback_data='matricula_geral')],
        [InlineKeyboardButton("Rematrícula", callback_data='rematricula')],
        [InlineKeyboardButton("Extraordinária", callback_data='extraordinaria')],
        [InlineKeyboardButton("🔙 Voltar", callback_data='menu')],
    ]
    return InlineKeyboardMarkup(keyboard)

def create_estagio_menu():
    keyboard = [
        [InlineKeyboardButton("Estágio Obrigatório", callback_data='estagio_obrigatorio')],
        [InlineKeyboardButton("Estágio Não Obrigatório", callback_data='estagio_nao_obrigatorio')],
        [InlineKeyboardButton("🔙 Voltar", callback_data='menu')],
    ]
    return InlineKeyboardMarkup(keyboard)

def create_fluxos_menu():
    keyboard = [
        [InlineKeyboardButton("Engenharia de Software", callback_data='fluxo_es')],
        [InlineKeyboardButton("Engenharia Eletrônica", callback_data='fluxo_eelet')],
        [InlineKeyboardButton("Engenharia Automotiva", callback_data='fluxo_eaut')],
        [InlineKeyboardButton("Engenharia Aeroespacial", callback_data='fluxo_eaero')],
        [InlineKeyboardButton("Engenharia de Energia", callback_data='fluxo_een')],
        [InlineKeyboardButton("🔙 Voltar", callback_data='menu')],
    ]
    return InlineKeyboardMarkup(keyboard)

def create_duvida_curso_menu():
    keyboard = [
        [
            InlineKeyboardButton("Engenharia de Software", callback_data='duvida_software'),
            InlineKeyboardButton("Engenharia Eletrônica", callback_data='duvida_eletronica'),
        ],
        [
            InlineKeyboardButton("Engenharia Automotiva", callback_data='duvida_automotiva'),
            InlineKeyboardButton("Engenharia Aeroespacial", callback_data='duvida_aeroespacial'),
        ],
        [
            InlineKeyboardButton("Engenharia de Energia", callback_data='duvida_energia'),
            InlineKeyboardButton("🔙 Voltar", callback_data='menu')
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
