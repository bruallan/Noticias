import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# --- 1. CONFIGURAÇÃO E BUSCA DAS NOTÍCIAS ---

# Pega as informações das Secrets do GitHub (ou variáveis de ambiente locais)
# É a forma segura de não expor seus dados no código
API_KEY = os.getenv('GNEWS_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL')

# Parâmetros da busca de notícias
TEMA_PESQUISA = 'mercado imobiliario'
QUANTIDADE_NOTICIAS = 10
IDIOMA = 'pt'
PAIS = 'br'

# Monta a URL para a chamada da API
url = f'https://gnews.io/api/v4/search?q="{TEMA_PESQUISA}"&lang={IDIOMA}&country={PAIS}&max={QUANTIDADE_NOTICIAS}&apikey={API_KEY}'

# --- 2. LÓGICA PARA FORMATAR O CORPO DO E-MAIL ---

corpo_email_html = f"<h1>🗞️ Sua Newsletter Diária sobre '{TEMA_PESQUISA.title()}'</h1>"
corpo_email_html += f"<p>Notícias coletadas em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p><hr>"

try:
    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()
        artigos = dados.get('articles', [])
        
        if not artigos:
            corpo_email_html += "<p>Nenhuma notícia encontrada hoje sobre este tema.</p>"
        else:
            # Formata cada notícia em HTML para o e-mail
            for artigo in artigos:
                titulo = artigo['title']
                link = artigo['url']
                fonte = artigo['source']['name']
                corpo_email_html += f"<h2><a href='{link}'>{titulo}</a></h2>"
                corpo_email_html += f"<p><i>Fonte: {fonte}</i></p><br>"
    else:
        corpo_email_html += f"<p>Ocorreu um erro ao buscar as notícias. Código: {response.status_code}</p>"

except requests.exceptions.RequestException as e:
    corpo_email_html += f"<p>Ocorreu um erro de conexão: {e}</p>"

# --- 3. LÓGICA PARA O ENVIO DO E-MAIL ---

print("Preparando para enviar o e-mail...")

# Configurações do servidor SMTP do Gmail
smtp_server = "smtp.gmail.com"
port = 587 

# Montando o e-mail
message = MIMEMultipart()
message["From"] = SENDER_EMAIL
message["To"] = RECEIVER_EMAIL
message["Subject"] = f"Notícias sobre '{TEMA_PESQUISA.title()}' - {datetime.now().strftime('%d/%m')}"

# Anexa o corpo do e-mail em formato HTML
message.attach(MIMEText(corpo_email_html, "html"))

try:
    # Inicia a conexão com o servidor SMTP
    server = smtplib.SMTP(smtp_server, port)
    server.starttls() # Inicia a criptografia TLS
    
    # Faz login na sua conta
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    
    # Envia o e-mail
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
    
    print("E-mail enviado com sucesso!")
    
except Exception as e:
    print(f"Falha ao enviar o e-mail: {e}")
    
finally:
    # Fecha a conexão

    server.quit()
