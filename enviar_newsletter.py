import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import google.generativeai as genai

# --- 1. CONFIGURAÇÃO E COLETA DE DADOS ---

# Carrega as chaves das Secrets
API_KEY_GNEWS = os.getenv('GNEWS_API_KEY')
API_KEY_GEMINI = os.getenv('GEMINI_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECEIVER_EMAILS_STR = os.getenv('RECEIVER_EMAIL')

# Configura a API do Gemini
genai.configure(api_key=API_KEY_GEMINI)

# Converte strings de e-mails para lista
RECEIVER_EMAILS_LIST = [email.strip() for email in RECEIVER_EMAILS_STR.split(',')]

# TEMAS DE PESQUISA (ajustados para o novo objetivo)
TEMAS_LIST = [
    "mercado imobiliário Sergipe", 
    "construção civil Sergipe",
    "lançamentos imobiliários Aracaju"
]

contexto_noticias = ""
print("Iniciando a busca de notícias...")

# Busca notícias para cada tema e as acumula em uma única string de contexto
for tema in TEMAS_LIST:
    url = f'https://gnews.io/api/v4/search?q="{tema}"&lang=pt&country=br&max=3&apikey={API_KEY_GNEWS}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            artigos = response.json().get('articles', [])
            for artigo in artigos:
                contexto_noticias += f"Título: {artigo['title']}\n"
                contexto_noticias += f"Fonte: {artigo['source']['name']}\n"
                contexto_noticias += f"Conteúdo: {artigo.get('description', '')}\n---\n"
    except Exception as e:
        print(f"Erro ao buscar notícias sobre '{tema}': {e}")

# --- 2. GERAÇÃO DO TEXTO COM IA (GEMINI) ---

corpo_email_final = ""

if not contexto_noticias:
    corpo_email_final = "<h1>Nenhuma notícia relevante encontrada hoje.</h1><p>Não foi possível gerar a análise do mercado de hoje.</p>"
else:
    # O prompt que definimos anteriormente
    prompt_template = """
    Você é um analista sênior do mercado imobiliário e da construção civil, com foco especializado no estado de Sergipe. Sua missão é escrever o corpo de uma newsletter informativa e analítica. O tom da sua escrita deve ser confiante, claro e direto, trazendo insights valiosos para investidores, construtores e o público interessado.
    Sua tarefa é criar um texto coeso e original que aborde as principais tendências, desafios e oportunidades no setor, com base exclusivamente nas notícias recentes fornecidas abaixo.
    **Instruções:**
    1. Comece com um parágrafo introdutório que capture a atenção do leitor e apresente o panorama geral do mercado em Sergipe.
    2. Desenvolva de 2 a 3 parágrafos de análise, conectando as informações das diferentes notícias para formar argumentos e identificar padrões.
    3. Finalize com um parágrafo de conclusão, oferecendo uma perspectiva futura ou um conselho prático.
    4. **NÃO FAÇA um resumo de cada notícia.** Use as notícias como a base de conhecimento para fundamentar a sua análise.
    5. O texto deve ser formatado em Markdown (usando títulos, negrito e listas se necessário).
    
    **Notícias de Base:**
    ---
    {noticias}
    ---
    """
    
    prompt_completo = prompt_template.format(noticias=contexto_noticias)
    
    print("Enviando contexto para a IA para geração do texto...")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest') # Modelo rápido e eficiente
        response = model.generate_content(prompt_completo)
        
        # Converte a saída Markdown da IA para HTML básico para o e-mail
        texto_gerado_html = response.text.replace('\n', '<br>')
        texto_gerado_html = texto_gerado_html.replace('**', '<b>', 100).replace('**', '</b>', 100) # Negrito
        texto_gerado_html = texto_gerado_html.replace('* ', '<br>• ') # Listas
        
        corpo_email_final = f"<h1>Análise do Mercado Imobiliário e Construção Civil em Sergipe</h1>{texto_gerado_html}"
        
    except Exception as e:
        print(f"Erro ao gerar conteúdo com a IA: {e}")
        corpo_email_final = "<h1>Erro na Geração da Análise</h1><p>Houve um problema ao conectar com a IA para gerar o texto da newsletter hoje.</p>"

# --- 3. LÓGICA DE ENVIO DO E-MAIL ---
# (Esta parte é a mesma de antes)
print("Preparando para enviar o e-mail...")

message = MIMEMultipart()
message["From"] = SENDER_EMAIL
message["To"] = ", ".join(RECEIVER_EMAILS_LIST)
message["Subject"] = f"Análise do Mercado Imobiliário (SE) - {datetime.now().strftime('%d/%m/%Y')}"

message.attach(MIMEText(corpo_email_final, "html", "utf-8"))

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS_LIST, message.as_string())
    print("Newsletter enviada com sucesso!")
except Exception as e:
    print(f"Falha ao enviar o e-mail: {e}")
finally:
    server.quit()
