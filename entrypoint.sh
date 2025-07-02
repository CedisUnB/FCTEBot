set -e 

if [ "$SERVICE_TYPE" = "api" ]; then
  echo "Iniciando API Service..."
  exec uvicorn rag_service:app --host 0.0.0.0 --port 8000 --workers 4

elif [ "$SERVICE_TYPE" = "bot" ]; then
  echo "Iniciando Bot Worker..."
  exec python bot.py

else
  echo "Erro: Variável de ambiente SERVICE_TYPE não definida ou inválida: $SERVICE_TYPE"
  exit 1
fi