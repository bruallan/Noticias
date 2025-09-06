# -*- coding: utf-8 -*-

import smtplib
import os
import asyncio # Necessário para o Playwright
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from playwright.async_api import async_playwright
from datetime import datetime

# --- Configurações do Email (lidas dos GitHub Secrets) ---
EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE")
SENHA_REMETENTE = os.environ.get("SENHA_REMETENTE")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO")

# --- FUNÇÃO ATUALIZADA USANDO PLAYWRIGHT ---
# --- FUNÇÃO ATUALIZADA E CORRIGIDA ---
async def buscar_noticias():
    """
    Busca as 5 principais notícias sobre construção civil usando Playwright,
    com os seletores corretos baseados na estrutura atual da página.
    """
    print("Buscando notícias com Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            url = "https://news.google.com/search?q=constru%C3%A7%C3%A3o%20civil&hl=pt-BR&gl=BR&ceid=BR%3Apt-419"
            await page.goto(url, wait_until="domcontentloaded")

            try:
                banner_button = page.get_by_role("button").filter(has_text=re.compile("Accept all|Aceitar tudo", re.IGNORECASE))
                await banner_button.click(timeout=5000)
                print("Banner de consentimento aceite.")
            except Exception:
                print("Banner de consentimento não encontrado ou já aceite, a continuar...")

            # NOVO SELETOR: Espera por um 'article' que contenha um link 'a'
            # Esta é a forma correta de garantir que os artigos carregaram.
            await page.wait_for_selector("article a", timeout=20000)

            artigos = await page.query_selector_all("article")
            noticias = []

            for item in artigos[:5]:
                # O link e o título estão no mesmo elemento <a>
                link_element = await item.query_selector("a")
                if not link_element:
                    continue

                link = await link_element.get_attribute("href")
                
                # O título está dentro de um <div> com a classe "ipQwMb"
                titulo_element = await link_element.query_selector("div.ipQwMb")
                if not titulo_element:
                    continue
                
                titulo = await titulo_element.inner_text()
                
                # Constrói o URL absoluto
                link_absoluto = f"https://news.google.com{link[1:]}" if link.startswith('.') else link
                
                noticias.append({"titulo": titulo, "link": link_absoluto})
            
            print(f"{len(noticias)} notícias encontradas.")
            return noticias
        except Exception as e:
            print(f"Ocorreu um erro ao buscar as notícias: {e}")
            await page.screenshot(path="screenshot_erro.png")
            return []
        finally:
            await browser.close()
# --- O RESTO DO SCRIPT PERMANECE IGUAL ---

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

# --- Função Principal Modificada para rodar o asyncio ---
def main():
    """
    Função principal que orquestra a execução do script.
    """
    noticias = asyncio.run(buscar_noticias())
    if noticias:
        corpo_email = criar_corpo_email(noticias)
        enviar_email(corpo_email)
    else:
        print("Não foi possível buscar as notícias. O email não será enviado.")

if __name__ == "__main__":
    main()



