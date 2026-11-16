import json
import os
import random
import requests
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
import base64

# 1. Configuração da página (Sidebar aberta para facilitar o acesso ao botão)
st.set_page_config(
    page_title="AnamnesIA — Simulador Clínico",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Carregamento seguro da chave de API (.env local ou Secrets na nuvem)
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY", "")
if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        api_key = ""
api_key = api_key.strip().strip('"').strip("'")

if not api_key:
    st.error("⚠️ Chave de API do Gemini não encontrada! Configure o arquivo .env (local) ou Secrets (Streamlit Cloud) com GEMINI_API_KEY.")
    st.stop()

client = genai.Client(api_key=api_key)

MODELOS_FLASH = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.0-flash",
]

# 3. Identidade Visual: Tons Roxos Foscos e Sóbrios + Verde Esmeralda Fosco
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #F8F7FC 0%, #FFFFFF 32%, #FFFFFF 100%);
        color: #2E293D;
    }
    header[data-testid="stHeader"] {
        background: rgba(248, 247, 252, 0.9);
    }
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1.5px solid #E2DEED;
        padding-top: 1rem;
    }
    h1, h2, h3, h4 {
        color: #6D28D9 !important;
    }
    .stMarkdown p, .stMarkdown li, label {
        color: #37304A !important;
    }
    .hero-banner {
        background: linear-gradient(135deg, #6D28D9 0%, #7C3AED 50%, #059669 100%);
        padding: 1.75rem 2rem;
        border-radius: 18px;
        color: #FFFFFF !important;
        margin-bottom: 1.4rem;
        box-shadow: 0 8px 22px rgba(109, 40, 217, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .hero-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 0.75rem;
    }
    .hero-badge {
        background: rgba(255, 255, 255, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.4);
        padding: 4px 13px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.4px;
        color: #FFFFFF !important;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0 0 0.35rem 0;
        color: #FFFFFF !important;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-title .ia-strong {
        color: #047857 !important;
        background: #F0FDF4;
        padding: 0px 8px;
        border-radius: 6px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #F3F0FF !important;
        margin-top: 0.25rem;
        font-weight: 500;
    }
    .spec-card, .level-card {
        background-color: #FFFFFF;
        border: 1.5px solid #E2DEED;
        border-top: 4px solid #8B5CF6;
        border-radius: 14px;
        padding: 1.15rem 1.25rem 0.75rem 1.25rem;
        margin-bottom: 0.55rem;
        min-height: 162px;
        box-shadow: 0 3px 12px rgba(109, 40, 217, 0.04);
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background-color 0.18s ease;
    }
    .spec-card:hover, .level-card:hover {
        background-color: #FAF9FC;
        border-color: #059669;
        border-top-color: #059669;
        box-shadow: 0 6px 18px rgba(5, 150, 105, 0.12);
        transform: translateY(-2px);
    }
    .level-card {
        min-height: 210px;
    }
    .spec-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #6D28D9 !important;
        margin-bottom: 0.35rem;
    }
    .spec-scenario {
        display: inline-block;
        background-color: #ECFDF5;
        color: #047857 !important;
        border: 1px solid #A7F3D0;
        border-radius: 999px;
        padding: 2px 10px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 0.65rem;
    }
    .spec-desc {
        font-size: 0.92rem;
        color: #4A4458 !important;
        line-height: 1.48;
    }
    
    /* Botão de Enviar Diagnóstico em Destaque Forte (Âmbar/Laranja) */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #D97706 0%, #B45309 100%) !important;
        color: #FFFFFF !important;
        border: 2px solid #FCD34D !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        box-shadow: 0 4px 15px rgba(217, 119, 6, 0.4) !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #B45309 100%, #92400E 100%) !important;
        box-shadow: 0 6px 20px rgba(217, 119, 6, 0.6) !important;
        transform: translateY(-1px);
    }
    button[kind="secondary"], [data-testid="baseButton-secondary"] {
        background-color: #F4F1FA !important;
        color: #6D28D9 !important;
        border: 1.5px solid #D5CEE8 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
    }
    button[kind="secondary"]:hover, [data-testid="baseButton-secondary"]:hover {
        background-color: #ECE7F7 !important;
        border-color: #8B5CF6 !important;
        color: #5B21B6 !important;
    }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
        background-color: #FFFFFF !important;
        color: #37304A !important;
        border: 1.5px solid #D5CEE8 !important;
        border-radius: 10px !important;
    }
    [data-testid="stChatMessage"] {
        background-color: #FAF9FC !important;
        border: 1.5px solid #E2DEED !important;
        border-left: 4px solid #059669 !important;
        border-radius: 14px !important;
        padding: 1rem 1.2rem !important;
        margin-bottom: 0.75rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

NIVEIS_DIFICULDADE = {
    "🟢 Fácil": {
        "titulo": "Fácil — Caso Clássico",
        "subtitulo": "Quadro típico de livro-texto",
        "descricao": "Paciente colaborativo que relata os sintomas com clareza. Poucas comorbidades e pistas diagnósticas diretas.",
        "instrucao_ia": "Crie um caso clínico clássico e típico desta especialidade, com apresentação bem característica e paciente colaborativo.",
    },
    "🟡 Médio": {
        "titulo": "Médio — Caso Investigativo",
        "subtitulo": "Pistas ocultas e diagnóstico diferencial",
        "descricao": "Paciente realista que omite detalhes decisivos até que o estudante faça a pergunta certa. Exige investigação ativa.",
        "instrucao_ia": "Crie um caso clínico realista que exija investigação ativa, possuindo 2 pistas ocultas decisivas que só são reveladas se o estudante perguntar.",
    },
    "🔴 Difícil": {
        "titulo": "Difícil — Caso Complexo / Atípico",
        "subtitulo": "Comorbidades, polifarmácia ou quadro atípico",
        "descricao": "Apresentação atípica ou mascarada, múltiplas comorbidades, paciente ansioso e risco clínico oculto.",
        "instrucao_ia": "Crie um caso clínico desafiador e complexo desta especialidade (apresentação atípica, polifarmácia ou comorbidades) com pistas críticas ocultas.",
    },
}

ESPECIALIDADES = {
    "Cardiologia": {"icone": "❤️", "cenario": "Pronto-Socorro", "descricao": "Investigação de dor torácica, dispneia e palpitações."},
    "Saúde Mental (Psiquiatria)": {"icone": "🧠", "cenario": "Urgência", "descricao": "Escuta ativa, acolhimento e transtornos de ansiedade/humor."},
    "Pediatria": {"icone": "👶", "cenario": "Consultório", "descricao": "Anamnese indireta, investigação de febre e doenças da infância."},
    "Gastroenterologia": {"icone": "🤢", "cenario": "Ambulatório", "descricao": "Dor abdominal, síndrome dispéptica e sangramentos."},
    "Pneumologia": {"icone": "🫁", "cenario": "Pronto-Atendimento", "descricao": "Dispneia, sibilância, tosse crônica e gatilhos."},
    "Endocrinologia": {"icone": "⚡", "cenario": "Ambulatório", "descricao": "Distúrbios glicêmicos, tireoidianos e metabólicos."},
    "Nefrologia": {"icone": "💧", "cenario": "Pronto-Atendimento", "descricao": "Dor lombar, alterações urinárias e função renal."},
    "Oftalmologia": {"icone": "👁️", "cenario": "Urgência", "descricao": "Olho vermelho, dor ocular e baixa visual."},
    "Otorrinolaringologia": {"icone": "👂", "cenario": "Ambulatório", "descricao": "Vertigem, zumbido e hipoacusia."},
    "Dermatologia": {"icone": "🩹", "cenario": "Consultório", "descricao": "Lesões cutâneas, prurido e critérios ABCDE."},
    "Cirurgia Geral": {"icone": "🔪", "cenario": "Pronto-Socorro", "descricao": "Abdome agudo e sinais de irritação peritoneal."},
    "Ginecologia": {"icone": "🌸", "cenario": "Consultório", "descricao": "Dor pélvica crônica e alterações menstruais."},
    "Obstetrícia": {"icone": "🤰", "cenario": "PA Obstétrico", "descricao": "Gestação e sinais premonitórios."},
    "Ortopedia": {"icone": "🦴", "cenario": "Pronto-Socorro", "descricao": "Trauma musculoesquelético e regras de Ottawa."},
    "Anestesiologia": {"icone": "💉", "cenario": "Pré-Anestésica", "descricao": "Risco cirúrgico, via aérea e alergias."},
    "Neurologia": {"icone": "⚡", "cenario": "Emergência", "descricao": "Déficit neurológico focal agudo e janela terapêutica."},
    "Infectologia": {"icone": "🦠", "cenario": "Pronto-Atendimento", "descricao": "Síndromes febris agudas e arboviroses."},
    "Reumatologia": {"icone": "🦴", "cenario": "Ambulatório", "descricao": "Poliartrite e rigidez matinal inflamatória."},
    "Urologia": {"icone": "🩺", "cenario": "Consultório", "descricao": "Sintomas do trato urinário e próstata."},
    "Hematologia": {"icone": "🩸", "cenario": "Ambulatório", "descricao": "Síndrome anêmica e sangramentos."},
    "Geriatria": {"icone": "👴", "cenario": "Ambulatório", "descricao": "Polifarmácia e quedas no idoso."},
    "Oncologia": {"icone": "🎗️", "cenario": "Ambulatório", "descricao": "Sintomas constitucionais e perda ponderal."},
    "Medicina de Emergência": {"icone": "🚑", "cenario": "Sala Vermelha", "descricao": "Instabilidade aguda e reações graves."},
    "Clínica Médica": {"icone": "🩺", "cenario": "Ambulatório", "descricao": "Sintomas sistêmicos e fadiga crônica."},
}


def gerar_resposta_ia(contents, instrucao_sistema, temperatura=0.9, json_mode=False):
    for modelo in MODELOS_FLASH:
        try:
            config_args = {
                "system_instruction": instrucao_sistema,
                "temperature": temperatura,
            }
            if json_mode:
                config_args["response_mime_type"] = "application/json"

            response = client.models.generate_content(
                model=modelo,
                contents=contents,
                config=types.GenerateContentConfig(**config_args),
            )
            return response.text
        except Exception:
            continue
    raise Exception("Falha ao comunicar com todos os modelos Gemini disponíveis.")


def criar_caso_por_nivel(especialidade, nivel):
    info_nivel = NIVEIS_DIFICULDADE[nivel]
    semente_aleatoria = random.randint(1000, 99999)

    prompt_gerador = f"""Gere um caso clínico COMPLETAMENTE NOVO, ORIGINAL e INÉDITO para treinamento de anamnese médica.
ID de Variação Única: {semente_aleatoria}

ESPECIALIDADE: {especialidade}
NÍVEL DE DIFICULDADE: {nivel}
DIRETRIZ TÉCNICA: {info_nivel['instrucao_ia']}

ATENÇÃO: Nunca repita casos comuns ou genéricos. Crie um paciente com nome completo diferente, idade variada, profissão e sintomas específicos gerados agora de forma totalmente criativa.

Retorne EXCLUSIVAMENTE um objeto JSON válido com estas exatas 5 chaves:
{{
  "titulo_caso": "Título curto e descritivo do cenário clínico sem entregar o diagnóstico",
  "paciente": "Nome completo fictício e idade",
  "primeira_fala": "Fala inicial natural e realista do paciente ao entrar no consultório, apresentando apenas a queixa principal",
  "prompt_sistema": "Instruções completas em primeira pessoa para a IA atuar como esse paciente: idade, profissão, sintomas detalhados, antecedentes, medicações, alergias, hábitos e a regra estrita de NUNCA revelar o diagnóstico sem o estudante perguntar.",
  "gabarito": "Diagnóstico oficial completo, pistas essenciais e conduta inicial esperada."
}}
"""
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text="Gere o caso clínico em JSON único.")],
        )
    ]

    try:
        resposta_bruta = gerar_resposta_ia(
            contents,
            "You are an expert medical professor creating unique OSCE clinical cases. Respond only with valid JSON.",
            temperatura=0.95,
            json_mode=True,
        )
        texto_limpo = resposta_bruta.strip()
        if texto_limpo.startswith("```"):
            texto_limpo = texto_limpo.split("\n", 1)[-1]
            if texto_limpo.endswith("```"):
                texto_limpo = texto_limpo.rsplit("```", 1)[0]

        dados = json.loads(texto_limpo.strip())
        chaves_obrigatorias = {"titulo_caso", "paciente", "primeira_fala", "prompt_sistema", "gabarito"}
        if chaves_obrigatorias.issubset(dados.keys()):
            return dados
    except Exception:
        pass

    nomes_aleatorios = ["Carlos Alberto", "Mariana Souza", "Roberto Dias", "Juliana Lima", "Renata Antunes", "Tiago Mendes", "Camila Rocha", "Bruno Bernardes"]
    return {
        "titulo_caso": f"Atendimento de Urgência em {especialidade} #{random.randint(10, 99)}",
        "paciente": f"{random.choice(nomes_aleatorios)}, {random.randint(22, 75)} anos",
        "primeira_fala": "Doutor(a), vim direto aqui porque os sintomas começaram de repente e estão me preocupando bastante...",
        "prompt_sistema": f"Você é um paciente com queixa na área de {especialidade}. Responda apenas quando perguntado e mantenha o sigilo do diagnóstico.",
        "gabarito": f"Investigar queixa principal de {especialidade}, antecedentes e solicitar exames direcionados."
    }


def avaliar_consulta(especialidade, nivel, dados_caso, mensagens, hipotese, conduta):
    transcricao = []
    for m in mensagens:
        papel = "Estudante" if m["role"] == "user" else f"Paciente ({dados_caso['paciente']})"
        transcricao.append(f"{papel}: {m['content']}")
    texto_conversa = "\n".join(transcricao)

    prompt_preceptor = f"""Você é um Preceptor Médico experiente avaliando a consulta de um estudante.
ESPECIALIDADE: {especialidade} ({nivel})
GABARITO: {dados_caso['gabarito']}
TRANSCRIÇÃO: {texto_conversa}
HIPÓTESE: {hipotese}
CONDUTA: {conduta}

Avalie o desempenho de 0 a 10 e use esta estrutura Markdown:
### 🎯 Veredito do Diagnóstico
### ⭐ Nota da Anamnese ({nivel}): X.X / 10
### ✅ Pontos Bem Investigados
### 🔍 O que Faltou Perguntar
### 💊 Feedback sobre a Conduta Inicial
"""
    contents = [types.Content(role="user", parts=[types.Part.from_text(text="Avalie minha consulta.")])]
    return gerar_resposta_ia(contents, prompt_preceptor, temperatura=0.3)


@st.dialog("🎓 Encerrar Consulta e Enviar Diagnóstico")
def abrir_modal_diagnostico(esp_atual, nivel_atual, dados_caso):
    st.caption(f"Paciente: **{dados_caso['paciente']}** • {esp_atual} ({nivel_atual})")
    with st.form("form_diagnostico_modal"):
        hipotese = st.text_input("1. Hipótese Diagnóstica principal?", placeholder="Ex: Apendicite, Infarto...")
        conduta = st.text_area("2. Conduta Inicial?", placeholder="Ex: Exames, medicações...", height=90)
        enviar_diag = st.form_submit_button("✅ Confirmar e Ver Nota do Preceptor", type="primary", use_container_width=True)

    if enviar_diag:
        if not hipotese.strip():
            st.warning("⚠️ Digite sua hipótese diagnóstica.")
        else:
            with st.spinner("🩺 O Preceptor Virtual está avaliando..."):
                try:
                    resultado = avaliar_consulta(esp_atual, nivel_atual, dados_caso, st.session_state.messages, hipotese, conduta)
                    st.session_state.parecer_preceptor = resultado
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")


# Gerenciamento de Estado
if "especialidade_ativa" not in st.session_state:
    st.session_state.especialidade_ativa = None
if "nivel_ativo" not in st.session_state:
    st.session_state.nivel_ativo = None
if "caso_atual" not in st.session_state:
    st.session_state.caso_atual = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "parecer_preceptor" not in st.session_state:
    st.session_state.parecer_preceptor = None
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Simulador"


def iniciar_consulta_com_nivel(especialidade, nivel):
    with st.spinner("🎲 Sorteando um novo caso clínico exclusivo com a IA..."):
        caso = criar_caso_por_nivel(especialidade, nivel)
    
    st.session_state.nivel_ativo = nivel
    st.session_state.caso_atual = caso
    st.session_state.parecer_preceptor = None
    st.session_state.messages = [{"role": "assistant", "content": caso["primeira_fala"]}]


# ==============================================================================
# BARRA LATERAL DINÂMICA (Acompanha a consulta e fixa o botão de Enviar Diagnóstico)
# ==============================================================================
with st.sidebar:
    if os.path.exists("logotipo.jpg"):
        st.image("logotipo.jpg", use_container_width=True)
    else:
        st.markdown("## 🧠 AnamnesIA")
    
    # Se estivermos dentro da consulta ativa, mostramos o botão de Enviar Diagnóstico na barra lateral
    if st.session_state.especialidade_ativa and st.session_state.nivel_ativo and st.session_state.caso_atual:
        st.markdown("---")
        st.markdown("### 🎯 Ações da Consulta")
        st.info(f"**Paciente:** {st.session_state.caso_atual['paciente']}")
        
        # Botão super visível que acompanha a tela inteira na barra lateral
        if st.button("🎓 Enviar Diagnóstico Final", type="primary", use_container_width=True):
            abrir_modal_diagnostico(st.session_state.especialidade_ativa, st.session_state.nivel_ativo, st.session_state.caso_atual)
        
        st.markdown("---")

    st.caption("Guia Rápido de Anamnese")
    st.markdown(
        """
        **Roteiro sugerido:**
        1. **Queixa Principal e HDA**
        2. **Antecedentes Pessoais**
        3. **Medicações e Alergias**
        4. **Hábitos e Família**
        """
    )


# Navegação Principal no Topo
col_nav1, col_nav2 = st.columns([1, 1])
with col_nav1:
    if st.button("🩺 Simulador Clínico", type="primary" if st.session_state.pagina_atual == "Simulador" else "secondary", use_container_width=True):
        st.session_state.pagina_atual = "Simulador"
        st.rerun()
with col_nav2:
    if st.button("💡 Enviar Sugestão / Feedback", type="primary" if st.session_state.pagina_atual == "Sugestoes" else "secondary", use_container_width=True):
        st.session_state.pagina_atual = "Sugestoes"
        st.rerun()

st.markdown("---")

if st.session_state.pagina_atual == "Sugestoes":
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-badges"><span class="hero-badge">💡 FEEDBACK</span></div>
            <div class="hero-title">Envie sua Sugestão</div>
            <div class="hero-subtitle">Ajude a melhorar o AnamnesIA.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("form_sugestoes"):
        nome_usuario = st.text_input("Seu Nome (Opcional)")
        tipo_feedback = st.selectbox("Tipo", ["Nova Especialidade", "Novo Caso", "Erro", "Melhoria"])
        mensagem_feedback = st.text_area("Mensagem:")
        enviar_sugestao = st.form_submit_button("📤 Enviar", type="primary", use_container_width=True)

    if enviar_sugestao:
        if not mensagem_feedback.strip():
            st.warning("⚠️ Escreva sua sugestão.")
        else:
            try:
                requests.post("[https://formspree.io/f/mwloljel](https://formspree.io/f/mwloljel)", data={"name": nome_usuario or "Anônimo", "tipo": tipo_feedback, "message": mensagem_feedback})
                st.success("🎉 Sugestão enviada com sucesso!")
            except Exception as e:
                st.error(f"Erro: {e}")

elif st.session_state.especialidade_ativa is None:
    logo_html = ""
    if os.path.exists("logotipo.jpg"):
        with open("logotipo.jpg", "rb") as f:
            encoded_logo = base64.b64encode(f.read()).decode()
            logo_html = f'<img src="data:image/jpeg;base64,{encoded_logo}" style="height: 52px; vertical-align: middle; margin-right: 12px; border-radius: 8px;">'

    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-badges">
                <span class="hero-badge">✨ PACIENTE VIRTUAL</span>
                <span class="hero-badge">🩺 24 ESPECIALIDADES</span>
            </div>
            <div class="hero-title">
                {logo_html} Anamnes<span class="ia-strong">IA</span>
            </div>
            <div class="hero-subtitle">Simulador clínico inteligente para treinamento médico.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    busca = st.text_input("Buscar especialidade", placeholder="🔍 Buscar especialidade...", label_visibility="collapsed")
    especialidades_filtradas = {k: v for k, v in ESPECIALIDADES.items() if busca.lower() in k.lower() or busca.lower() in v["cenario"].lower()}

    lista_itens = list(especialidades_filtradas.items())
    for i in range(0, len(lista_itens), 3):
        cols = st.columns(3)
        for idx, (nome, dados) in enumerate(lista_itens[i : i + 3]):
            with cols[idx]:
                st.markdown(
                    f"""
                    <div class="spec-card">
                        <div class="spec-title">{dados['icone']} {nome}</div>
                        <div class="spec-scenario">📍 {dados['cenario']}</div>
                        <div class="spec-desc">{dados['descricao']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Selecionar ➔", key=f"btn_{nome}", type="primary", use_container_width=True):
                    st.session_state.especialidade_ativa = nome
                    st.session_state.nivel_ativo = None
                    st.session_state.caso_atual = None
                    st.session_state.messages = []
                    st.session_state.parecer_preceptor = None
                    st.rerun()

elif st.session_state.nivel_ativo is None:
    esp_atual = st.session_state.especialidade_ativa
    info_esp = ESPECIALIDADES[esp_atual]

    if st.button("⬅️ Voltar"):
        st.session_state.especialidade_ativa = None
        st.rerun()

    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-badges"><span class="hero-badge">{info_esp['icone']} {esp_atual.upper()}</span></div>
            <div class="hero-title" style="font-size: 1.75rem;">Selecione o Nível</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols_nivel = st.columns(3)
    for idx, (chave_nivel, info_nivel) in enumerate(NIVEIS_DIFICULDADE.items()):
        with cols_nivel[idx]:
            st.markdown(
                f"""
                <div class="level-card">
                    <div class="spec-title">{chave_nivel}</div>
                    <div class="spec-scenario">{info_nivel['subtitulo']}</div>
                    <div class="spec-desc">{info_nivel['descricao']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Iniciar {chave_nivel.split()[-1]} ➔", key=f"nivel_{chave_nivel}", type="primary", use_container_width=True):
                iniciar_consulta_com_nivel(esp_atual, chave_nivel)
                st.rerun()

else:
    esp_atual = st.session_state.especialidade_ativa
    nivel_ativo = st.session_state.nivel_ativo
    info_esp = ESPECIALIDADES[esp_atual]
    dados_caso = st.session_state.caso_atual

    # Botões superiores na tela de atendimento (Especialidades, Trocar Nível, Novo Caso)
    col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
    with col_b1:
        if st.button("⬅️ Especialidades", use_container_width=True):
            st.session_state.especialidade_ativa = None
            st.session_state.nivel_ativo = None
            st.session_state.caso_atual = None
            st.session_state.messages = []
            st.session_state.parecer_preceptor = None
            st.rerun()
    with col_b2:
        if st.button("🎚️ Trocar Nível", use_container_width=True):
            st.session_state.nivel_ativo = None
            st.session_state.caso_atual = None
            st.session_state.messages = []
            st.session_state.parecer_preceptor = None
            st.rerun()
    with col_b3:
        if st.button("🎲 Novo Caso", use_container_width=True):
            iniciar_consulta_com_nivel(esp_atual, nivel_ativo)
            st.rerun()

    st.markdown(
        f"""
        <div class="hero-banner" style="padding: 1.3rem 1.8rem; margin-top: 0.5rem;">
            <div class="headers-badges" style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:0.5rem;">
                <span class="hero-badge">{info_esp['icone']} {esp_atual.upper()}</span>
                <span class="hero-badge">{nivel_ativo.upper()}</span>
                <span class="hero-badge">🧑 {dados_caso['paciente'].upper()}</span>
            </div>
            <div class="hero-title" style="font-size: 1.5rem;">{dados_caso.get('titulo_caso', 'Consultório Virtual')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.parecer_preceptor:
        with st.container(border=True):
            st.success("✅ **Consulta Finalizada! Confira a avaliação do Preceptor:**")
            st.markdown(st.session_state.parecer_preceptor)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🎲 Sortear Outro Caso", type="primary", use_container_width=True):
                    iniciar_consulta_com_nivel(esp_atual, nivel_ativo)
                    st.rerun()
            with c2:
                if st.button("🩺 Outra Especialidade", use_container_width=True):
                    st.session_state.especialidade_ativa = None
                    st.session_state.nivel_ativo = None
                    st.session_state.caso_atual = None
                    st.session_state.messages = []
                    st.session_state.parecer_preceptor = None
                    st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Digite sua pergunta de anamnese para o paciente..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        contents = []
        for m in st.session_state.messages[1:]:
            api_role = "user" if m["role"] == "user" else "model"
            contents.append(types.Content(role=api_role, parts=[types.Part.from_text(text=m["content"])]))

        instrucao_completa = (
            f"{dados_caso['prompt_sistema']}\n\n"
            f"Nível: {nivel_ativo}.\n"
            f"Contexto inicial: \"{dados_caso['primeira_fala']}\""
        )

        with st.chat_message("assistant"):
            with st.spinner("O paciente está respondendo..."):
                text_response = ""
                try:
                    text_response = gerar_resposta_ia(contents, instrucao_completa, temperatura=0.8)
                    st.markdown(text_response)
                    st.session_state.messages.append({"role": "assistant", "content": text_response})
                except Exception as e:
                    st.error(f"Erro ao responder: {e}")
