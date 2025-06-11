import os
import re
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Pasta com os arquivos .md
folder_path = './Infos Adms UnB'
entries = []

def extract_metadata(content):
    """Extrai fonte e data de atualização do texto completo."""
    fonte = ""
    data_atualizacao = None

    fonte_match = re.search(r'Fonte:\s*\[(.*?)\]\((.*?)\)', content)
    if fonte_match:
        fonte = f"{fonte_match.group(1)} - {fonte_match.group(2)}"

    data_match = re.search(r'Atualização:\s*(\d{2}/\d{2}/\d{4})', content)
    if data_match:
        data_atualizacao = datetime.strptime(data_match.group(1), "%d/%m/%Y").date()

    return fonte, data_atualizacao


def extract_sections(content, fonte, data_atualizacao):
    """Extrai seções com base nos títulos e subtítulos, associando metadata."""
    title_main = ""
    lines = content.splitlines()
    current_subtitle = ""
    current_text = []

    for line in lines:
        line = line.strip()

        if line.startswith('# ') and not title_main:
            title_main = line[2:].strip()

        elif line.startswith('## '):
            # salva seção anterior
            if current_subtitle and current_text:
                entries.append({
                    "nome": f"{title_main} {current_subtitle}",
                    "texto": "\n".join(current_text).strip(),
                    "fonte": fonte,
                    "data_atualizacao": data_atualizacao
                })
                current_text = []

            current_subtitle = line[3:].strip()

        elif current_subtitle:
            current_text.append(line)

    # salva última seção
    if current_subtitle and current_text:
        entries.append({
            "nome": f"{title_main} {current_subtitle}",
            "texto": "\n".join(current_text).strip(),
            "fonte": fonte,
            "data_atualizacao": data_atualizacao
        })

# Processa todos os arquivos .md
for filename in os.listdir(folder_path):
    if filename.endswith('.md'):
        filepath = os.path.join(folder_path, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            print(f"📄 Processando: {filename}")
            fonte, data_atualizacao = extract_metadata(content)
            extract_sections(content, fonte, data_atualizacao)

# Gera CSV
df = pd.DataFrame(entries)
df.index += 1  # Começa o id em 1
df.reset_index(inplace=True)
df.rename(columns={'index': 'id'}, inplace=True)

csv_output_path = 'infosadmunb.csv'
df.to_csv(csv_output_path, index=False, encoding='utf-8')
print(f"\n✅ CSV gerado com sucesso: {csv_output_path}")
print(f"📦 Total de seções extraídas: {len(entries)}")
