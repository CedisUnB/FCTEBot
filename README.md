# FCTEBot - Chatbot Inteligente para Informações Acadêmicas da FCTE/UnB

## Alunos

| Matrícula | Aluno                                                            |
| --------- | -----------------------------------------------------------------|
| 202015984	| [Breno Henrique de Souza](https://github.com/breno-hs)            |
| 180121308 | [Giulia Alcantara](https://github.com/alcantaragiubs)            |

## Descrição

O FCTEBot é um sistema de chatbot inteligente desenvolvido como Trabalho de Conclusão de Curso (TCC) para fornecer informações administrativas da Faculdade de Ciências e Tecnologias em Engenharia (FCTE) da Universidade de Brasília (UnB). O sistema utiliza tecnologias de Retrieval-Augmented Generation (RAG) para oferecer respostas precisas e contextualizadas sobre cursos de engenharia, procedimentos administrativos, matrículas, estágios e outras informações relevantes aos estudantes.

## Arquitetura do Sistema

### Componentes Principais

1. **Bot Telegram/WhatsApp**: Interface de interação com os estudantes.
2. **API FastAPI**: Gerencia requisições e lógica de consulta RAG.
3. **Sistema RAG**: Busca e geração de respostas usando LLM.
4. **Banco de Dados MySQL**: Armazena informações estruturadas e feedbacks.
5. **Pinecone Vector DB**: Busca semântica de dados.
6. **Modelo Gemini (Google)**: Geração de linguagem natural.

### Tecnologias Utilizadas

- **Python 3.11+**
- **FastAPI**
- **python-telegram-bot**
- **LangChain**
- **Pinecone**
- **Google Gemini API**
- **MySQL (TiDBCloud)**
- **Docker** (opcional para deploy)

## Estrutura do Projeto

```
FCTBot/
├── main.py                  # Inicialização e roteamento FastAPI
├── rag_logic.py             # Lógica de consulta RAG
├── requirements.txt         # Dependências do projeto
├── handlers/                # Handlers do Telegram/WhatsApp
│   ├── callbacks.py
│   ├── perguntas.py
│   └── menus.py
├── utils/                   # Utilidades
│   ├── db_helper.py
│   ├── api_helper.py
│   └── logger.py
├── scripts/                 # Scripts de manutenção
│   ├── create-index-pinecone.py
│   ├── csv-to-sql.py
│   └── md-to-csv.py
├── Infos Adms FCTE/         # Base de conhecimento em Markdown
└── imgs/                    # Imagens e fluxogramas
```

## Configuração do Ambiente

### Variáveis de Ambiente (.env)

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Configurações do Bot Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Configurações do Banco de Dados MySQL (TiDBCloud)
DB_HOST=your_tidb_host
DB_USER=your_tidb_user
DB_PASSWORD=your_tidb_password
DB_NAME=your_database_name
DB_PORT=4000

# Configurações do Google Gemini
GOOGLE_API_KEY=your_google_api_key

# Configurações do Pinecone
PINECONE_API_KEY=your_pinecone_api_key

# Configurações da API (Opcional)
RAG_API_URL=http://127.0.0.1:8000/responder
PORT=8000
```

### Configuração do TiDBCloud

O projeto utiliza TiDBCloud como plataforma de banco de dados MySQL. Para configurar:

1. Acesse [TiDBCloud](https://tidbcloud.com/)
2. Crie um cluster MySQL compatível
3. Configure as credenciais de acesso no arquivo `.env`
4. Execute o script de criação das tabelas:

```sql
CREATE TABLE infosadmunb (
    id INT PRIMARY KEY,
    nome VARCHAR(255),
    texto TEXT,
    fonte VARCHAR(500),
    data_atualizacao DATE
);

CREATE TABLE feedbacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    helped BOOLEAN NOT NULL,
    suggestion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Instalação e Execução

### 1. Instalação das Dependências

```bash
pip install -r requirements.txt
```

### 2. Preparação da Base de Dados

#### Conversão de Markdown para CSV

```bash
python md-to-csv.py
```

#### Importação para MySQL

```bash
python csv-to-sql.py
```

#### Criação do Índice Pinecone

```bash
python create-index-pinecone.py
```

### 3. Execução da Aplicação

#### Modo Desenvolvimento

```bash
python main.py
```

#### Modo Produção

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Funcionalidades

### Bot Telegram

- **Menu Interativo**: Seleção de curso específico ou contexto geral
- **Perguntas Naturais**: Processamento de linguagem natural
- **Exemplos Contextuais**: Sugestões baseadas no curso selecionado
- **Sistema de Feedback**: Coleta de avaliações dos usuários
- **Timeout Inteligente**: Gerenciamento automático de sessões

### Sistema RAG

- **Busca Semântica**: Utiliza embeddings para encontrar conteúdo relevante
- **Geração Contextualizada**: Respostas baseadas em contexto específico
- **Fontes Citadas**: Inclui origem e data de atualização das informações
- **Rate Limiting**: Controle de requisições com retry automático

### API REST

- **Endpoint /responder**: Processa consultas via POST
- **Endpoint /**: Health check do sistema
- **Documentação Automática**: Swagger UI disponível em `/docs`

## Estrutura de Dados

### Base de Conhecimento

A base de conhecimento é organizada em arquivos Markdown na pasta `Infos Adms UnB/`:

- Informações gerais sobre cursos de engenharia
- Procedimentos administrativos
- Fluxogramas curriculares
- Calendário acadêmico
- Serviços estudantis
- Contatos importantes

### Metadados

Cada documento possui metadados estruturados:

- **Nome**: Título do documento
- **Fonte**: URL ou referência original
- **Data de Atualização**: Timestamp da última modificação
- **Texto**: Conteúdo processado

## Monitoramento e Logging

O sistema implementa logging estruturado com diferentes níveis:

- **INFO**: Operações normais
- **WARNING**: Situações de atenção (rate limits)
- **ERROR**: Erros recuperáveis
- **CRITICAL**: Falhas críticas do sistema

Logs incluem informações sobre:

- Requisições de usuários
- Performance de consultas
- Erros de API
- Estatísticas de uso

## Deploy e Infraestrutura

### Dependências de Serviços Externos

1. **TiDBCloud**: Banco de dados MySQL serverless
2. **Pinecone**: Banco vetorial para embeddings
3. **Google Cloud**: API Gemini para LLM
4. **Telegram**: Plataforma de bot

### Considerações de Produção

- Configure variáveis de ambiente adequadamente
- Monitore usage limits das APIs
- Implemente backup regular da base de dados
- Configure SSL/TLS para conexões seguras
- Monitore logs e métricas de performance

## Desenvolvimento e Manutenção

### Atualizando a Base de Conhecimento

1. Edite arquivos em `Infos Adms UnB/`
2. Execute `python md-to-csv.py`
3. Execute `python csv-to-sql.py`
4. Execute `python create-index-pinecone.py`

### Adicionando Novas Funcionalidades

- Handlers do Telegram: `handlers/`
- Lógica de negócio: `utils/`
- Endpoints API: `main.py`

## Limitações e Considerações

- **Rate Limits**: APIs externas possuem limites de requisições
- **Contexto**: Respostas limitadas ao conhecimento da base de dados
- **Idioma**: Otimizado para português brasileiro
- **Escopo**: Focado em informações da FGA/UnB

## Contribuição

Este projeto foi desenvolvido como TCC e serve como base para futuras melhorias no atendimento estudantil da FGA/UnB. Contribuições são bem-vindas para:

- Expansão da base de conhecimento
- Melhorias na interface do usuário
- Otimizações de performance
- Novas funcionalidades
