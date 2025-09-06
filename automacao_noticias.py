# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Documentação
# --------------------------------------------------------------------------
#
# Versão adaptada para rodar com GitHub Actions.
# As credenciais são lidas de forma segura a partir de variáveis de ambiente,
# que devem ser configuradas como "Secrets" no repositório do GitHub.
#
# --------------------------------------------------------------------------

import smtplib
import os # Importamos a biblioteca 'os' para acessar as variáveis de ambiente
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from requests_html import HTMLSession
from datetime import datetime

# --- Configurações do Email (lidas dos GitHub Secrets) ---
# Agora, em vez de colocar as credenciais aqui, pegamos das variáveis de ambiente
EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE")
SENHA_REMETENTE = os.environ.get("SENHA_REMETENTE")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO")

def buscar_noticias():
    """
    Busca as 5 principais notícias sobre construção civil no Google Notícias.
    """
    print("Buscando notícias...")
    session = HTMLSession()
    url = "https://news.google.com/search?q=constru%C3%A7%C3%A3o%20civil&hl=pt-BR&gl=BR&ceid=BR%3Apt-419"

    try:
        response = session.get(url)
        response.raise_for_status()
        response.html.render(sleep=1, timeout=20)
        artigos = response.html.find('article')
        noticias = []

        for item in artigos[:5]:
            try:
                titulo = item.find('h3', first=True).text
                link = list(item.absolute_links)[0]
                noticias.append({"titulo": titulo, "link": link})
            except (AttributeError, IndexError):
                continue

        print(f"{len(noticias)} notícias encontradas.")
        return noticias
    except Exception as e:
        print(f"Ocorreu um erro ao buscar as notícias: {e}")
        return []

def criar_corpo_email(noticias):
    """
    Cria o corpo do email em formato HTML com a lista de notícias.
    """
    if not noticias:
        return "<p>Nenhuma notícia sobre construção civil foi encontrada hoje.</p>"

    data_hoje = datetime.now().strftime('%d/%m/%Y')
    html = f"""
    <html><body>
        <h1>Principais Notícias sobre Construção Civil - {data_hoje}</h1>
        <p>Aqui estão as 5 principais notícias de hoje:</p>
        <ul>
    """
    for noticia in noticias:
        html += f'<li><a href="{noticia["link"]}">{noticia["titulo"]}</a></li>'
    html += "</ul><p>Este é um email automático enviado pelo seu script de notícias via GitHub Actions.</p></body></html>"
    return html

def enviar_email(corpo_html):
    """
    Envia o email com as notícias.
    """
    # Validação para garantir que os secrets foram carregados
    if not all([EMAIL_REMETENTE, SENHA_REMETENTE, EMAIL_DESTINATARIO]):
        print("Erro: As credenciais de email (secrets) não foram configuradas corretamente.")
        return

    print("Preparando para enviar o email...")
    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO
    msg['Subject'] = f"Notícias Diárias sobre Construção Civil - {datetime.now().strftime('%d/%m/%Y')}"
    msg.attach(MIMEText(corpo_html, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_REMETENTE)
        server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
        server.quit()
        print("Email enviado com sucesso!")
    except Exception as e:
        print(f"Ocorreu um erro ao enviar o email: {e}")

def main():
    """
    Função principal que orquestra a execução do script.
    """
    noticias = buscar_noticias()
    if noticias:
        corpo_email = criar_corpo_email(noticias)
        enviar_email(corpo_email)
    else:
        print("Não foi possível buscar as notícias. O email não será enviado.")

if __name__ == "__main__":
    main()