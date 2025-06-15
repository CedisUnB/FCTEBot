from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def create_menu():
    keyboard = [
        [InlineKeyboardButton("📊 Escolher Curso", callback_data='cursos')],
        [InlineKeyboardButton("ℹ️ Engenharias", callback_data='contexto')],
    ]
    return InlineKeyboardMarkup(keyboard)

def create_cursos_menu():
    keyboard = [
        [InlineKeyboardButton("Engenharia de Software", callback_data='curso_es')],
        [InlineKeyboardButton("Engenharia Eletrônica", callback_data='curso_eelet')],
        [InlineKeyboardButton("Engenharia Automotiva", callback_data='curso_eaut')],
        [InlineKeyboardButton("Engenharia Aeroespacial", callback_data='curso_eaero')],
        [InlineKeyboardButton("Engenharia de Energia", callback_data='curso_een')],
        [InlineKeyboardButton("🔙 Voltar", callback_data='menu')],
    ]
    return InlineKeyboardMarkup(keyboard)
