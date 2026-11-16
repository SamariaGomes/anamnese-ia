import json
import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Configuração da página
st.set_page_config(
    page_title="AnamnesIA — Simulador Clínico",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
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
    /* Fundo principal em tom claro neutro com toque fosco */
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
    }

    /* Títulos em Roxo Fosco Sóbrio e textos legíveis */
    h1, h2, h3, h4 {
        color: #6D28D9 !important;
    }
    .stMarkdown p, .stMarkdown li, label {
        color: #37304A !important;
    }

    /* Banner Hero em Degradê Roxo Fosco -> Verde Esmeralda Fosco */
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

    /* Cards Brancos com Borda Roxa Fosca Suave */
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

    /* Botões Principais (Verde Esmeralda Fosco) */
    button[kind="primary"], [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    button[kind="primary"]:hover, [data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, #047857 0%, #065F46 100%) !important;
        box-shadow: 0 6px 16px rgba(5, 150, 105, 0.28) !important;
        transform: translateY(-1px);
    }
    button[kind="primary"] p, [data-testid="baseButton-primary"] p {
        color: #FFFFFF !important;
    }

    /* Botões Secundários com Roxo Fosco */
    button[kind="secondary"], [data-testid="baseButton-secondary"] {
        background-color: #F4F1FA !important;
        color: #6D28D9 !important;
        border: 1.5px solid #D5CEE8 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover, [data-testid="baseButton-secondary"]:hover {
        background-color: #ECE7F7 !important;
        border-color: #8B5CF6 !important;
        color: #5B21B6 !important;
    }
    button[kind="secondary"] p, [data-testid="baseButton-secondary"] p {
        color: #6D28D9 !important;
    }

    /* Inputs e Campos de Busca */
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
        background-color: #FFFFFF !important;
        color: #37304A !important;
        border: 1.5px solid #D5CEE8 !important;
        border-radius: 10px !important;
    }
    [data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {
        border-color: #059669 !important;
        box-shadow: 0 0 0 2px rgba(5, 150, 105, 0.15) !important;
    }

    /* Mensagens do Chat */
    [data-testid="stChatMessage"] {
        background-color: #FAF9FC !important;
        border: 1px solid #E2DEED !important;
        border-left: 4px solid #059669 !important;
        border-radius: 14px !important;
        padding: 1rem 1.2rem !important;
        margin-bottom: 0.75rem !important;
        box-shadow: 0 2px 8px rgba(109, 40, 217, 0.03) !important;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
        color: #37304A !important;
    }

    /* Barra inferior do chat */
    [data-testid="stChatInput"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #D5CEE8 !important;
        border-radius: 14px !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #37304A !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 4. Níveis de Dificuldade da Anamnese
NIVEIS_DIFICULDADE = {
    "🟢 Fácil": {
        "titulo": "Fácil — Caso Clássico",
        "subtitulo": "Quadro típico de livro-texto",
        "descricao": "Paciente colaborativo que relata os sintomas com clareza. Poucas comorbidades e pistas diagnósticas diretas. Ideal para treinar a estrutura básica da anamnese.",
        "instrucao_ia": (
            "NÍVEL FÁCIL: Crie um caso clínico clássico e típico desta especialidade, com apresentação bem característica de livro-texto. "
            "O paciente deve ser colaborativo, objetivo e responder com clareza às perguntas do estudante, sem comorbidades confusas ou apresentações atípicas. "
            "Inclua 1 antecedente ou hábito relevante que o paciente revela facilmente quando perguntado."
        ),
    },
    "🟡 Médio": {
        "titulo": "Médio — Caso Investigativo",
        "subtitulo": "Pistas ocultas e diagnóstico diferencial",
        "descricao": "Paciente realista que omite detalhes decisivos (alergias, medicações, hábitos ou gatilhos) até que o estudante faça a pergunta certa. Exige investigação ativa.",
        "instrucao_ia": (
            "NÍVEL MÉDIO: Crie um caso clínico realista desta especialidade que exija investigação ativa e raciocínio diferencial. "
            "O paciente deve possuir 2 pistas ocultas decisivas (ex.: uso contínuo de medicamento, alergia grave a antibiótico/analgésico de primeira linha, hábito de risco ou gatilho ambiental/emocional) "
            "que ele NÃO menciona espontaneamente e só revela se o estudante perguntar especificamente."
        ),
    },
    "🔴 Difícil": {
        "titulo": "Difícil — Caso Complexo / Atípico",
        "subtitulo": "Comorbidades, polifarmácia ou quadro atípico",
        "descricao": "Apresentação atípica ou mascarada, múltiplas comorbidades, paciente ansioso ou poliqueixoso e risco clínico oculto. Desafia o raciocínio diagnóstico sob pressão.",
        "instrucao_ia": (
            "NÍVEL DIFÍCIL: Crie um caso clínico desafiador e complexo desta especialidade (ex.: apresentação atípica, sintoma mascarado, polifarmácia, múltiplas comorbidades ou paciente ansioso/resistente/poliqueixoso que mistura queixas secundárias com sinais de alarme). "
            "Inclua pistas críticas ocultas que mudam totalmente a conduta (contraindicação absoluta, interação medicamentosa ou emergência silenciosa) e só são reveladas se o estudante investigar a fundo."
        ),
    },
}

# 5. Catálogo Completo com 24 Especialidades Médicas (+ Caso Base de Contingência)
ESPECIALIDADES = {
    "Cardiologia": {
        "icone": "❤️",
        "cenario": "Pronto-Socorro",
        "descricao": "Investigação de dor torácica, dispneia, palpitações, síncope e fatores de risco cardiovascular.",
        "fallback": {
            "titulo_caso": "Dor Torácica Aguda no Pronto-Socorro",
            "paciente": "Carlos, 54 anos",
            "primeira_fala": "Doutor(a)... por favor, me ajuda. Meu peito tá apertando muito faz quase duas horas e começou a puxar pro braço esquerdo...",
            "prompt_sistema": (
                "Você é Carlos, 54 anos, motorista de aplicativo, no pronto-socorro. "
                "Queixa: dor torácica opressiva retroesternal há 2 horas, intensidade 8/10, irradiando para braço esquerdo e mandíbula, com sudorese fria e náusea. "
                "Antecedentes (só revele se perguntado): hipertenso há 10 anos (toma losartana irregularmente), tabagista (1 maço/dia há 25 anos), pai faleceu de infarto aos 58 anos. Nega alergias. "
                "REGRAS: Responda apenas como o paciente, em português natural, frases curtas e ansioso pela dor. Nunca diga o diagnóstico nem revele antecedentes sem ser perguntado."
            ),
            "gabarito": "Diagnóstico: Síndrome Coronariana Aguda / Infarto Agudo do Miocárdio (IAM). Pistas essenciais: dor opressiva irradiada, sudorese fria, hipertensão mal controlada, tabagismo e história familiar precoce. Conduta: MOV, ECG em até 10 min, troponina, AAS 200-300mg mastigado e analgesia.",
        },
    },
    "Saúde Mental (Psiquiatria)": {
        "icone": "🧠",
        "cenario": "Urgência / Acolhimento",
        "descricao": "Escuta ativa, acolhimento emocional, transtornos de ansiedade, humor e diagnóstico diferencial.",
        "fallback": {
            "titulo_caso": "Crise Súbita de Falta de Ar e Taquicardia",
            "paciente": "Mariana, 27 anos",
            "primeira_fala": "Doutor(a), eu não consigo respirar direito, meu coração tá disparado e parece que eu vou desmaiar ou morrer agora...",
            "prompt_sistema": (
                "Você é Mariana, 27 anos, analista financeira. "
                "Queixa: início súbito há 30 minutos de palpitações, falta de ar, formigamento nas mãos, tontura e medo intenso de morrer. "
                "Contexto (só revele se perguntado): teve outros 2 episódios parecidos no último mês após sobrecarga no trabalho; toma muito café e dorme 4h por noite. Nega doenças cardíacas ou alergias. "
                "REGRAS: Responda apenas como Mariana, assustada. Não revele o gatilho emocional antes de ser perguntada."
            ),
            "gabarito": "Diagnóstico: Transtorno de Pânico / Crise de Ansiedade Aguda. Pistas essenciais: início súbito com pico rápido, sintomas autonômicos, medo de morrer, recorrência e gatilho de estresse/privação de sono, excluindo causas orgânicas. Conduta: acolhimento verbal, respiração lenta, ECG/glicemia para exclusão orgânica e encaminhamento psiquiátrico/psicológico.",
        },
    },
    "Pediatria": {
        "icone": "👶",
        "cenario": "Consultório Pediátrico",
        "descricao": "Anamnese indireta com acompanhante, investigação de febre, exantemas e doenças da infância.",
        "fallback": {
            "titulo_caso": "Febre Alta e Recusa Alimentar na Infância",
            "paciente": "Lucas, 4 anos (mãe: Fernanda)",
            "primeira_fala": "Oi doutor(a), trouxe o Lucas porque ele tá com febre alta desde ontem e hoje não quis comer nada, só fica choramingando.",
            "prompt_sistema": (
                "Você é Fernanda, mãe de Lucas (4 anos). "
                "Queixa: febre de 39,2°C desde ontem à noite, dor de garganta e recusa alimentar. "
                "Detalhes (só revele se perguntado): sem tosse nem coriza; placas esbranquiçadas na garganta e gânglios doloridos no pescoço; vacinas em dia; alergia grave à penicilina/amoxicilina (urticária generalizada aos 2 anos). "
                "REGRAS: Responda como a mãe preocupada. Só mencione a alergia a penicilina/amoxicilina se perguntada sobre alergias."
            ),
            "gabarito": "Diagnóstico: Faringoamigdalite Bacteriana Aguda em paciente alérgico a penicilinas. Pistas essenciais: febre alta, odinofagia, ausência de tosse/coriza, exsudato amigdaliano e ALERGIA À PENICILINA. Conduta: macrolídeo (Azitromicina/Claritromicina, evitando amoxicilina), antitérmico e hidratação.",
        },
    },
    "Gastroenterologia": {
        "icone": "🤢",
        "cenario": "Ambulatório",
        "descricao": "Avaliação de dor abdominal, síndrome dispéptica, sangramentos digestivos e hábitos.",
        "fallback": {
            "titulo_caso": "Dor Epigástrica Crônica em Piora",
            "paciente": "Roberto, 46 anos",
            "primeira_fala": "Doutor(a), tô com uma queimação e uma dor forte na boca do estômago que vem piorando faz umas três semanas.",
            "prompt_sistema": (
                "Você é Roberto, 46 anos, representante comercial. "
                "Queixa: dor epigástrica em queimação há 3 semanas, piora em jejum e de madrugada. "
                "Detalhes (só revele se perguntado): usa diclofenaco/ibuprofeno diariamente há 2 meses por dor no joelho; fezes ficaram pretas e pastosas (melena) nos últimos 2 dias; alergia a dipirona. "
                "REGRAS: Responda como Roberto. Só fale do anti-inflamatório e das fezes escuras se perguntado."
            ),
            "gabarito": "Diagnóstico: Úlcera Péptica induzida por AINEs com Hemorragia Digestiva Alta (melena). Pistas essenciais: dor epigástrica, uso crônico de AINEs e melena. Conduta: suspender AINE, iniciar IBP venoso/oral, hemograma e Endoscopia Digestiva Alta (EDA) urgente.",
        },
    },
    "Pneumologia": {
        "icone": "🫁",
        "cenario": "Pronto-Atendimento",
        "descricao": "Investigação de dispneia, sibilância, tosse crônica, gatilhos ambientais e tabagismo.",
        "fallback": {
            "titulo_caso": "Sibilância e Dispneia após Exposição Ambiental",
            "paciente": "Juliana, 22 anos",
            "primeira_fala": "Doutor(a)... tô com o peito chiando muito e uma falta de ar que começou depois que eu limpei um quarto fechado lá em casa.",
            "prompt_sistema": (
                "Você é Juliana, 22 anos, estudante universitária. "
                "Queixa: falta de ar, chiado no peito e tosse seca há 1 hora após contato com poeira. "
                "Detalhes (só revele se perguntado): teve asma na infância, sem crises há 5 anos; rinite alérgica associada; sem alergias medicamentosas. "
                "REGRAS: Responda com leve falta de ar. Só revele o histórico de asma na infância se perguntada."
            ),
            "gabarito": "Diagnóstico: Crise Aguda de Asma desencadeada por alérgeno. Pistas essenciais: dispneia, sibilância, gatilho de poeira e antecedente de asma/atopia. Conduta: beta-2 agonista de curta ação (Salbutamol inalatório), corticoide sistêmico e oximetria.",
        },
    },
    "Endocrinologia": {
        "icone": "⚡",
        "cenario": "Ambulatório",
        "descricao": "Rastreamento metabólico, distúrbios glicêmicos, tireoidianos e antecedentes familiares.",
        "fallback": {
            "titulo_caso": "Fadiga Intensa e Sede Excessiva",
            "paciente": "Renata, 38 anos",
            "primeira_fala": "Doutor(a), vim consultar porque tô sentindo um cansaço absurdo e uma sede que não passa por nada nesse mundo.",
            "prompt_sistema": (
                "Você é Renata, 38 anos, professora. "
                "Queixa: polidipsia, poliúria (acorda 4x à noite para urinar), cansaço e perda de 5 kg no último mês. "
                "Detalhes (só revele se perguntado): mãe e tia têm diabetes tipo 2; teve diabetes gestacional há 4 anos; visão turva recente; sem alergias. "
                "REGRAS: Responda naturalmente. Só mencione perda de peso, poliúria e histórico familiar se perguntada."
            ),
            "gabarito": "Diagnóstico: Diabetes Mellitus descompensado. Pistas essenciais: poliúria, polidipsia, perda ponderal, diabetes gestacional prévio e história familiar. Conduta: glicemia de jejum, HbA1c, glicemia capilar imediata e plano terapêutico.",
        },
    },
    "Nefrologia": {
        "icone": "💧",
        "cenario": "Pronto-Atendimento",
        "descricao": "Dor lombar aguda, alterações urinárias, edema e avaliação da função renal.",
        "fallback": {
            "titulo_caso": "Dor Lombar Aguda em Cólica",
            "paciente": "Tiago, 34 anos",
            "primeira_fala": "Ai, doutor(a), tô com uma dor insuportável nas costas do lado direito que não melhora em posição nenhuma!",
            "prompt_sistema": (
                "Você é Tiago, 34 anos, programador. "
                "Queixa: dor lombar direita em cólica, início súbito há 3 horas, intensidade 9/10, irradiando para virilha direita, com náuseas. "
                "Detalhes (só revele se perguntado): bebe pouca água; urina avermelhada hoje; nega febre; já teve cálculo renal há 3 anos; sem alergias. "
                "REGRAS: Responda inquieto pela dor. Só conte sobre urina avermelhada, baixa ingesta hídrica e ausência de febre se perguntado."
            ),
            "gabarito": "Diagnóstico: Nefrolitíase / Cólica Nefrética não complicada. Pistas essenciais: dor lombar irradiada para virilha, hematúria, baixa ingesta hídrica, litíase prévia e ausência de febre. Conduta: analgesia, antiemético, hidratação e TC sem contraste ou USG de vias urinárias.",
        },
    },
    "Oftalmologia": {
        "icone": "👁️",
        "cenario": "Urgência Oftalmológica",
        "descricao": "Investigação de olho vermelho, dor ocular, baixa visual e uso de lentes de contato.",
        "fallback": {
            "titulo_caso": "Olho Vermelho Doloroso e Fotofobia",
            "paciente": "Camila, 25 anos",
            "primeira_fala": "Doutor(a), meu olho direito amanheceu super vermelho, doendo muito e lacrimejando, não consigo nem olhar pra luz.",
            "prompt_sistema": (
                "Você é Camila, 25 anos, arquiteta. "
                "Queixa: dor ocular intensa no olho direito, hiperemia, fotofobia, lacrimejamento e visão turva desde hoje cedo. "
                "Detalhes (só revele se perguntado): usa lentes de contato gelatinosas e dormiu com elas ontem; nega trauma direto; sem alergias. "
                "REGRAS: Responda incomodada com a luz. Só revele que usa lentes de contato e dormiu com elas se perguntada."
            ),
            "gabarito": "Diagnóstico: Ceratite Infecciosa / Úlcera de Córnea associada a lentes de contato. Pistas essenciais: olho vermelho doloroso, fotofobia, baixa visual e dormir com lentes. Conduta: suspender lentes, não usar corticoide tópico, encaminhar urgente ao oftalmologista.",
        },
    },
    "Otorrinolaringologia": {
        "icone": "👂",
        "cenario": "Ambulatório",
        "descricao": "Avaliação de vertigem, zumbido, hipoacusia, sinusopatias e sintomas vestibulares.",
        "fallback": {
            "titulo_caso": "Tontura Rotatória ao Movimentar a Cabeça",
            "paciente": "Helena, 49 anos",
            "primeira_fala": "Doutor(a), parece que o quarto inteiro tá rodando quando eu viro a cabeça na cama, tô até com enjoo.",
            "prompt_sistema": (
                "Você é Helena, 49 anos, costureira. "
                "Queixa: episódios de 30 segundos de tontura rotatória intensa ao deitar ou virar a cabeça para a direita há 4 dias. "
                "Detalhes (só revele se perguntado): sem zumbido, sem perda auditiva, sem cefaleia ou déficit motor; melhora parada; sem alergias. "
                "REGRAS: Só detalhe a duração curta e ausência de sintomas auditivos/neurológicos se perguntada."
            ),
            "gabarito": "Diagnóstico: Vertigem Posicional Paroxística Benigna (VPPB). Pistas essenciais: vertigem posicional de curta duração (< 1 min) sem sintomas cocleares ou neurológicos. Conduta: manobra de Dix-Hallpike e manobra de reposicionamento de Epley.",
        },
    },
    "Dermatologia": {
        "icone": "🩹",
        "cenario": "Consultório",
        "descricao": "Anamnese de lesões cutâneas, critérios ABCDE, prurido e exposição ocupacional.",
        "fallback": {
            "titulo_caso": "Lesão Pigmentada Assimétrica no Dorso",
            "paciente": "Bruno, 31 anos",
            "primeira_fala": "Doutor(a), apareceu uma mancha escura nas minhas costas que minha esposa achou estranha e pediu pra eu vir olhar.",
            "prompt_sistema": (
                "Você é Bruno, 31 anos, instrutor de surfe. "
                "Queixa: lesão pigmentada no dorso há 4 meses, cresceu, bordas irregulares e duas cores (marrom escuro e preto). "
                "Detalhes (só revele se perguntado): pele muito clara, exposição solar diária sem protetor, queimaduras solares na adolescência, tia teve melanoma. "
                "REGRAS: Só conte sobre as características da mancha, exposição solar e histórico familiar se perguntado."
            ),
            "gabarito": "Diagnóstico: Suspeita de Melanoma Cutâneo (critérios ABCDE positivos). Pistas essenciais: assimetria, bordas irregulares, variação de cor, evolução, fototipo baixo e história familiar. Conduta: dermatoscopia e biópsia excisional.",
        },
    },
    "Cirurgia Geral": {
        "icone": "🔪",
        "cenario": "Pronto-Socorro Cirúrgico",
        "descricao": "Investigação de abdome agudo, cronologia da dor e sinais de irritação peritoneal.",
        "fallback": {
            "titulo_caso": "Dor Abdominal Migratória",
            "paciente": "Gabriel, 21 anos",
            "primeira_fala": "Doutor(a), tô com uma dor na barriga desde ontem à noite que começou perto do umbigo e agora foi pro lado direito embaixo.",
            "prompt_sistema": (
                "Você é Gabriel, 21 anos, estudante. "
                "Queixa: dor abdominal iniciada há 18 horas periumbilical, migrou para fossa ilíaca direita, piora ao andar/tossir. "
                "Detalhes (só revele se perguntado): anorexia total, 1 vômito e febre de 37,9°C; nega diarreia ou disúria; sem cirurgias prévias. "
                "REGRAS: Responda curvado de dor. Só revele anorexia e febre se perguntado."
            ),
            "gabarito": "Diagnóstico: Apendicite Aguda. Pistas essenciais: migração da dor para fossa ilíaca direita, anorexia, náusea/vômito e febrícula. Conduta: jejum, hidratação venosa, analgesia, hemograma/PCR, USG/TC se necessário e avaliação cirúrgica.",
        },
    },
    "Ginecologia": {
        "icone": "🌸",
        "cenario": "Consultório Ginecológico",
        "descricao": "Anamnese ginecológica, dor pélvica crônica, alterações menstruais e saúde reprodutiva.",
        "fallback": {
            "titulo_caso": "Dismenorreia Progressiva e Dor Pélvica",
            "paciente": "Larissa, 29 anos",
            "primeira_fala": "Doutor(a), eu vim porque minhas cólicas menstruais estão ficando cada vez piores e já não passam com remédio comum.",
            "prompt_sistema": (
                "Você é Larissa, 29 anos, designer. "
                "Queixa: dismenorreia progressiva há 2 anos, dor pélvica crônica e dispareunia de profundidade. "
                "Detalhes (só revele se perguntado): tentando engravidar há 1 ano e meio sem sucesso; dor ao evacuar na menstruação; sem alergias. "
                "REGRAS: Responda de forma reservada no início, revelando dispareunia e infertilidade apenas se perguntada com respeito."
            ),
            "gabarito": "Diagnóstico: Endometriose Pélvica. Pistas essenciais: dismenorreia progressiva, dispareunia de profundidade, disquezia cíclica e infertilidade. Conduta: exame ginecológico, USG transvaginal com preparo intestinal ou RM de pelve.",
        },
    },
    "Obstetrícia": {
        "icone": "🤰",
        "cenario": "Pronto-Atendimento Obstétrico",
        "descricao": "Gestação, sinais premonitórios de eclâmpsia, sangramentos e vitalidade fetal.",
        "fallback": {
            "titulo_caso": "Cefaleia e Alterações Visuais no 3º Trimestre",
            "paciente": "Beatriz, 32 anos (34 semanas)",
            "primeira_fala": "Doutor(a), tô grávida de 34 semanas e vim porque hoje acordei com uma dor de cabeça forte na nuca e minha vista tá meio embaralhada.",
            "prompt_sistema": (
                "Você é Beatriz, 32 anos, primigesta de 34 semanas. "
                "Queixa: cefaleia intensa há 4 horas, escotomas visuais e dor na boca do estômago (epigastralgia). "
                "Detalhes (só revele se perguntado): edema súbito em mãos e rosto há 2 dias; movimentação fetal presente; sem alergias. "
                "REGRAS: Responda preocupada com o bebê. Só conte sobre epigastralgia e edema facial se perguntada."
            ),
            "gabarito": "Diagnóstico: Pré-eclâmpsia com sinais de gravidade (iminência de eclâmpsia). Pistas essenciais: gestante > 20 semanas com cefaleia, escotomas e epigastralgia. Conduta: aferir PA, sulfato de magnésio, anti-hipertensivo se PA >= 160x110, rotina HELLP e vitalidade fetal.",
        },
    },
    "Ortopedia": {
        "icone": "🦴",
        "cenario": "Pronto-Socorro Ortopédico",
        "descricao": "Trauma musculoesquelético, mecanismo de lesão, regras clínicas e status neurovascular.",
        "fallback": {
            "titulo_caso": "Trauma Torcional Agudo de Tornozelo",
            "paciente": "Rafael, 26 anos",
            "primeira_fala": "Doutor(a), torci feio o tornozelo direito jogando futebol agora há pouco e não consigo nem encostar o pé no chão.",
            "prompt_sistema": (
                "Você é Rafael, 26 anos, engenheiro civil. "
                "Queixa: entorse em inversão do tornozelo direito há 1 hora no futebol, dor intensa e edema lateral imediato. "
                "Detalhes (só revele se perguntado): ouviu estalo; não consegue dar 4 passos; dor óssea no maléolo lateral; sensibilidade e perfusão preservadas; sem alergias. "
                "REGRAS: Só detalhe o estalo e a incapacidade de dar 4 passos (Regras de Ottawa) se perguntado."
            ),
            "gabarito": "Diagnóstico: Entorse Grave de Tornozelo / Suspeita de Fratura Maleolar (Ottawa positivo). Pistas essenciais: inversão, dor óssea maleolar e incapacidade de dar 4 passos. Conduta: radiografia de tornozelo, imobilização provisória, gelo, elevação e analgesia.",
        },
    },
    "Anestesiologia": {
        "icone": "💉",
        "cenario": "Avaliação Pré-Anestésica",
        "descricao": "Risco cirúrgico, via aérea, medicamentos críticos, alergias e antecedentes anestésicos.",
        "fallback": {
            "titulo_caso": "Avaliação Pré-Anestésica para Cirurgia Eletiva",
            "paciente": "Sérgio, 61 anos",
            "primeira_fala": "Bom dia, doutor(a). Vim fazer a avaliação pré-anestésica porque vou operar a vesícula por vídeo na semana que vem.",
            "prompt_sistema": (
                "Você é Sérgio, 61 anos, aposentado. "
                "Queixa: avaliação pré-anestésica para colecistectomia videolaparoscópica. "
                "Detalhes (só revele se perguntado): usa clopidogrel e AAS por stent cardíaco há 4 meses; irmão teve hipertermia maligna em anestesia; alergia a látex. "
                "REGRAS: Só revele stent/antiagregantes, alergia a látex e histórico familiar de hipertermia maligna se perguntado."
            ),
            "gabarito": "Diagnóstico: Alto Risco Anestésico (Stent recente em dupla antiagregação + Suscetibilidade à Hipertermia Maligna + Alergia ao Látex). Conduta: parecer cardiológico para antiagregantes, anestesia venosa total (TIVA) sem halogenados/succinilcolina e sala látex-free.",
        },
    },
    "Neurologia": {
        "icone": "⚡",
        "cenario": "Emergência Neurológica",
        "descricao": "Déficit neurológico focal agudo, cefaleias secundárias, janela terapêutica e comorbidades.",
        "fallback": {
            "titulo_caso": "Déficit Motor Súbito e Disartria",
            "paciente": "Antônio, 67 anos (filha: Paula)",
            "primeira_fala": "Doutor(a), corre aqui! Meu pai tava tomando café agora há pouco e do nada a boca dele entortou e ele não consegue mexer o braço direito!",
            "prompt_sistema": (
                "Você é Paula, filha de Antônio (67 anos). "
                "Queixa: início súbito há 40 minutos de desvio de rima labial, disartria e hemiparesia direita. "
                "Detalhes (só revele se perguntado): tem fibrilação atrial e parou a rivaroxabana há 1 semana; sem trauma craniano. "
                "REGRAS: Responda em urgência. Só revele o tempo exato (40 min) e suspensão do anticoagulante se perguntada."
            ),
            "gabarito": "Diagnóstico: AVC Isquêmico Agudo em janela terapêutica (< 4,5h). Pistas essenciais: déficit focal súbito, início há 40 min e FA sem anticoagulação. Conduta: protocolo AVC, glicemia capilar, TC de crânio sem contraste imediata e avaliar trombólise/trombectomia.",
        },
    },
    "Infectologia": {
        "icone": "🦠",
        "cenario": "Pronto-Atendimento",
        "descricao": "Síndromes febris agudas, arboviroses, sinais de alarme e história epidemiológica.",
        "fallback": {
            "titulo_caso": "Síndrome Febril Aguda com Dor Abdominal",
            "paciente": "Felipe, 29 anos",
            "primeira_fala": "Doutor(a), tô há quatro dias com uma febre altíssima, dor no corpo inteiro e uma dor atrás dos olhos que não me deixa nem trabalhar.",
            "prompt_sistema": (
                "Você é Felipe, 29 anos, vendedor. "
                "Queixa: febre de 39,5°C há 4 dias, mialgia, cefaleia retro-orbitária e exantema desde ontem. "
                "Detalhes (só revele se perguntado): hoje a febre baixou, mas surgiu dor abdominal forte e 2 vômitos persistentes; surto de dengue no bairro; sem alergias. "
                "REGRAS: Só conte sobre dor abdominal intensa e vômitos (sinais de alarme) se perguntado."
            ),
            "gabarito": "Diagnóstico: Dengue com Sinais de Alarme (Grupo C). Pistas essenciais: síndrome febril + dor retro-orbitária + epidemiologia + dor abdominal e vômitos na defervescência. Conduta: hidratação venosa imediata (Grupo C), hemograma completo, evitar AINEs/AAS e internação.",
        },
    },
    "Reumatologia": {
        "icone": "🦴",
        "cenario": "Ambulatório",
        "descricao": "Poliartrite simétrica, rigidez matinal inflamatória e manifestações autoimunes.",
        "fallback": {
            "titulo_caso": "Dor e Rigidez Matinal nas Mãos",
            "paciente": "Cláudia, 42 anos",
            "primeira_fala": "Doutor(a), faz uns quatro meses que eu acordo com as juntas das mãos e dos punhos todas duras e inchadas.",
            "prompt_sistema": (
                "Você é Cláudia, 42 anos, bibliotecária. "
                "Queixa: artrite simétrica de pequenas articulações das mãos e punhos há 4 meses. "
                "Detalhes (só revele se perguntado): rigidez matinal dura mais de 1 hora e melhora com movimento; fadiga; mãe tem artrite reumatoide; sem alergias. "
                "REGRAS: Só detalhe a duração da rigidez matinal (> 1h) se perguntada."
            ),
            "gabarito": "Diagnóstico: Artrite Reumatoide. Pistas essenciais: poliartrite crônica simétrica de pequenas articulações e rigidez matinal > 1 hora. Conduta: Fator Reumatoide, Anti-CCP, VHS/PCR, RX de mãos e iniciar DMARD (Metotrexato).",
        },
    },
    "Urologia": {
        "icone": "🩺",
        "cenario": "Consultório Urológico",
        "descricao": "Sintomas do trato urinário inferior, hematúria e saúde urológica.",
        "fallback": {
            "titulo_caso": "Noctúria e Jato Urinário Fraco",
            "paciente": "José Augusto, 64 anos",
            "primeira_fala": "Doutor(a), minha esposa insistiu pra eu vir porque tô levantando umas cinco vezes toda noite pra ir no banheiro.",
            "prompt_sistema": (
                "Você é José Augusto, 64 anos, comerciante. "
                "Queixa: noctúria (5x/noite), jato urinário fraco, esforço miccional e esvaziamento incompleto há 1 ano. "
                "Detalhes (só revele se perguntado): nega disúria, febre, hematúria ou perda de peso; sem alergias. "
                "REGRAS: Só detalhe o jato fraco e ausência de hematúria se perguntado."
            ),
            "gabarito": "Diagnóstico: Hiperplasia Prostática Benigna (HPB). Pistas essenciais: LUTS obstrutivos e irritativos progressivos em homem > 50 anos sem sinais de alarme. Conduta: toque retal, PSA, EAS, creatinina, USG de vias urinárias/próstata e alfa-bloqueador.",
        },
    },
    "Hematologia": {
        "icone": "🩸",
        "cenario": "Ambulatório",
        "descricao": "Investigação de síndrome anêmica, sangramentos, linfonodomegalias e carências.",
        "fallback": {
            "titulo_caso": "Fadiga Progressiva e Palidez Cutânea",
            "paciente": "Patrícia, 35 anos",
            "primeira_fala": "Doutor(a), tô me sentindo muito fraca, com falta de ar quando subo escada e todo mundo diz que eu tô branca igual papel.",
            "prompt_sistema": (
                "Você é Patrícia, 35 anos, contadora. "
                "Queixa: fadiga, dispneia aos esforços, tontura e palidez há 3 meses. "
                "Detalhes (só revele se perguntado): menorragia intensa com coágulos todo mês; vontade de mastigar gelo (pagofagia) e unhas quebradiças; sem alergias. "
                "REGRAS: Só conte sobre a menstruação intensa e pagofagia se perguntada."
            ),
            "gabarito": "Diagnóstico: Anemia Ferropriva secundária a sangramento uterino anormal. Pistas essenciais: síndrome anêmica, menorragia e pagofagia. Conduta: hemograma, ferritina, ferro sérico, saturação de transferrina, reposição de sulfato ferroso e investigação ginecológica.",
        },
    },
    "Geriatria": {
        "icone": "👴",
        "cenario": "Ambulatório Geriátrico",
        "descricao": "Polifarmácia, quedas no idoso, avaliação funcional, cognitiva e iatrogenia.",
        "fallback": {
            "titulo_caso": "Queda Domiciliar e Sonolência no Idoso",
            "paciente": "Dona Nair, 79 anos (neto: Bruno)",
            "primeira_fala": "Oi doutor(a), trouxe minha avó porque ela levou um tombo no corredor de casa ontem à noite quando levantou pra ir ao banheiro.",
            "prompt_sistema": (
                "Você é Bruno, neto de Dona Nair (79 anos). "
                "Queixa: queda da própria altura ontem à madrugada, sonolência diurna e tontura ao levantar. "
                "Detalhes (só revele se perguntado): toma 8 remédios por dia, incluindo clonazepam iniciado há 2 semanas para insônia e 2 anti-hipertensivos; sem alergias. "
                "REGRAS: Só revele o uso recente de clonazepam e a polifarmácia se perguntado sobre medicações."
            ),
            "gabarito": "Diagnóstico: Queda no Idoso por Polifarmácia / Benzodiazepínico e provável Hipotensão Ortostática. Pistas essenciais: início recente de clonazepam e múltiplos anti-hipertensivos. Conduta: desprescrição gradual do benzodiazepínico, pesquisa de hipotensão postural, revisão medicamentosa e prevenção ambiental.",
        },
    },
    "Oncologia": {
        "icone": "🎗️",
        "cenario": "Ambulatório",
        "descricao": "Investigação de sintomas constitucionais, perda ponderal inexplicada e rastreamento.",
        "fallback": {
            "titulo_caso": "Tosse Crônica e Perda Ponderal",
            "paciente": "Marcos, 59 anos",
            "primeira_fala": "Doutor(a), vim consultar porque tô com uma tosse seca que não passa faz dois meses e perdi bastante peso sem fazer dieta.",
            "prompt_sistema": (
                "You are Marcos, 59 anos, pedreiro. "
                "Queixa: tosse persistente há 2 meses, perda de 8 kg, hiporexia e fadiga. "
                "Detalhes (só revele se perguntado): fumou 2 maços/dia por 38 anos; raias de sangue no escarro (hemoptise) na última semana; nega febre noturna; sem alergias. "
                "REGRAS: Só conte sobre a carga tabágica alta e hemoptise se perguntado."
            ),
            "gabarito": "Diagnóstico: Suspeita de Neoplasia Pulmonar. Pistas essenciais: tosse > 3 semanas em tabagista pesado, hemoptise e perda ponderal. Conduta: TC de tórax com contraste urgente e encaminhamento para broncoscopia/biópsia.",
        },
    },
    "Medicina de Emergência": {
        "icone": "🚑",
        "cenario": "Sala Vermelha",
        "descricao": "Instabilidade aguda, reações graves e conduta imediata salvadora.",
        "fallback": {
            "titulo_caso": "Reação Aguda Grave após Ingestão Alimentar",
            "paciente": "Eduardo, 24 anos",
            "primeira_fala": "Doutor(a)... tô com o corpo todo coçando, minha garganta tá fechando e tô ficando muito tonto depois que comi um camarão agora pouco!",
            "prompt_sistema": (
                "You are Eduardo, 24 anos. "
                "Queixa: há 10 min após comer camarão iniciou urticária generalizada, edema labial, rouquidão, sibilos e tontura forte. "
                "Detalhes (só revele se perguntado): já teve alergia leve a frutos do mar antes; sem outras doenças. "
                "REGRAS: Responda com frases curtas e rouquidão, mostrando urgência."
            ),
            "gabarito": "Diagnóstico: Anafilaxia / Choque Anafilático. Pistas essenciais: exposição a alérgeno + urticária/angioedema + comprometimento respiratório e hipotensão. Conduta IMEDIATA: Adrenalina IM 0,3-0,5 mg no vasto lateral da coxa imediatamente, O2 alto fluxo, acesso venoso e monitorização.",
        },
    },
    "Clínica Médica": {
        "icone": "🩺",
        "cenario": "Ambulatório Geral",
        "descricao": "Investigação de sintomas sistêmicos, fadiga crônica, alterações ponderais e diagnóstico amplo.",
        "fallback": {
            "titulo_caso": "Fadiga Crônica, Ganho de Peso e Intolerância ao Frio",
            "paciente": "Vanessa, 44 anos",
            "primeira_fala": "Doutor(a), tô me sentindo muito inchada, ganhei peso mesmo comendo pouco e tô com um sono e um frio fora do normal.",
            "prompt_sistema": (
                "You are Vanessa, 44 anos, secretária. "
                "Queixa: fadiga, sonolência, intolerância ao frio, ganho de 4 kg e constipação há 6 meses. "
                "Detalhes (só revele se perguntado): pele seca, queda de cabelo, irregularidade menstrual; irmã tem doença na tireoide; sem alergias. "
                "REGRAS: Só detalhe constipação, queda de cabelo e histórico familiar tireoidiano se perguntada."
            ),
            "gabarito": "Diagnóstico: Hipotireoidismo Primário. Pistas essenciais: hipometabolismo (astenia, intolerância ao frio, ganho ponderal, constipação) e história familiar. Conduta: solicitar TSH e T4 livre e iniciar Levotiroxina em jejum após confirmação.",
        },
    },
}


# 6. Funções de Comunicação com a IA (Gerador de Casos, Paciente e Preceptor)
def gerar_resposta_ia(contents, instrucao_sistema, temperatura=0.7, json_mode=False):
    ultimo_erro = None
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
        except Exception as e:
            ultimo_erro = e
            continue
    raise ultimo_erro


def criar_caso_por_nivel(especialidade, nivel):
    info_esp = ESPECIALIDADES[especialidade]
    info_nivel = NIVEIS_DIFICULDADE[nivel]

    prompt_gerador = f"""Crie um caso clínico original e realista em português para treinamento de anamnese médica.

ESPECIALIDADE: {especialidade} (Cenário: {info_esp['cenario']})
NÍVEL DE DIFICULDADE: {nivel}
DIRETRIZ DO NÍVEL: {info_nivel['instrucao_ia']}

Varie o perfil do paciente (nome brasileiro comum, idade, profissão, quadro clínico compatível com a especialidade e nível solicitado).
Retorne EXCLUSIVAMENTE um objeto JSON válido com estas exatas 5 chaves:
{{
  "titulo_caso": "Título curto do cenário clínico sem entregar o diagnóstico (ex: Dor Abdominal Aguda no Pronto-Socorro)",
  "paciente": "Nome e idade (e acompanhante se for pediatria/idoso dependente)",
  "primeira_fala": "Fala inicial natural e realista do paciente ao entrar no consultório, apresentando apenas a queixa principal sem dar o diagnóstico",
  "prompt_sistema": "Instruções completas em primeira pessoa para a IA atuar como esse paciente: idade, profissão, sintomas detalhados, antecedentes pessoais/familiares, medicações, alergias, hábitos, estado emocional e a regra estrita de NUNCA revelar o diagnóstico nem entregar pistas ocultas sem o estudante perguntar.",
  "gabarito": "Diagnóstico oficial completo, pistas essenciais que o estudante deveria descobrir na anamnese e conduta inicial esperada."
}}
"""
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text="Gere o caso clínico em JSON conforme as instruções.")],
        )
    ]

    try:
        resposta_bruta = gerar_resposta_ia(
            contents,
            "You are a medical professor expert in OSCE clinical simulation. Respond only with valid JSON.",
            temperatura=0.85,
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

    return info_esp["fallback"]


def avaliar_consulta(especialidade, nivel, dados_caso, mensagens, hipotese, conduta):
    transcricao = []
    for m in mensagens:
        papel = "Estudante" if m["role"] == "user" else f"Paciente ({dados_caso['paciente']})"
        transcricao.append(f"{papel}: {m['content']}")
    texto_conversa = "\n".join(transcricao)

    prompt_preceptor = f"""Você é um Preceptor Médico experiente avaliando a consulta de um estudante de saúde.

ESPECIALIDADE: {especialidade}
NÍVEL DE DIFICULDADE ESCOLHIDO: {nivel}

CASO CLÍNICO E GABARITO OFICIAL:
{dados_caso['gabarito']}

TRANSCRIÇÃO DA CONSULTA REALIZADA PELO ESTUDANTE:
{texto_conversa}

RESPOSTA FINAL ENVIADA PELO ESTUDANTE:
- Hipótese Diagnóstica: {hipotese}
- Conduta Inicial: {conduta if conduta.strip() else "Não informada"}

Avalie o desempenho do estudante considerando o nível de dificuldade ({nivel}) de forma construtiva, técnica e objetiva em português, usando exatamente esta estrutura em Markdown:

### 🎯 Veredito do Diagnóstico
Diga claramente se o estudante **ACERTOU**, **ACERTOU PARCIALMENTE** ou **ERROU**, e apresente o **Gabarito Oficial** do caso.

### ⭐ Nota da Anamnese ({nivel}): X.X / 10
Atribua uma nota justa de 0 a 10 considerando as perguntas feitas durante a entrevista, a investigação das pistas ocultas, a precisão do diagnóstico e a conduta proposta.

### ✅ Pontos Bem Investigados
Liste em tópicos o que o estudante perguntou bem durante a conversa.

### 🔍 O que Faltou Perguntar
Liste em tópicos as perguntas importantes do gabarito que o estudante deixou de investigar (como alergias, antecedentes, medicações, hábitos ou sinais de alarme).

### 💊 Feedback sobre a Conduta Inicial
Comente se a conduta sugerida pelo estudante está adequada ou o que deveria ser priorizado na prática clínica.
"""
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text="Por favor, avalie minha consulta clínica e meu diagnóstico final.")],
        )
    ]
    return gerar_resposta_ia(contents, prompt_preceptor, temperatura=0.3)


# 7. Janela Modal para Envio do Diagnóstico Final
@st.dialog("🎓 Encerrar Consulta e Enviar Diagnóstico")
def abrir_modal_diagnostico(esp_atual, nivel_atual, dados_caso):
    st.caption(f"Paciente: **{dados_caso['paciente']}** • {esp_atual} ({nivel_atual})")
    with st.form("form_diagnostico_modal"):
        hipotese = st.text_input(
            "1. Qual é a sua Hipótese Diagnóstica principal?",
            placeholder="Ex: Infarto Agudo do Miocárdio, Crise de Pânico, Apendicite Aguda...",
        )
        conduta = st.text_area(
            "2. Qual é a sua Conduta Inicial (exames, medicações ou encaminhamento)?",
            placeholder="Ex: Solicitar ECG em 10 min, monitorização, analgesia, exames laboratoriais...",
            height=90,
        )
        enviar_diag = st.form_submit_button(
            "✅ Confirmar e Ver Nota do Preceptor",
            type="primary",
            use_container_width=True,
        )

    if enviar_diag:
        if not hipotese.strip():
            st.warning("⚠️ Digite sua hipótese diagnóstica antes de enviar para o Preceptor.")
        else:
            with st.spinner("🩺 O Preceptor Virtual está avaliando toda a sua entrevista e seu diagnóstico..."):
                try:
                    resultado = avaliar_consulta(
                        esp_atual,
                        nivel_atual,
                        dados_caso,
                        st.session_state.messages,
                        hipotese,
                        conduta,
                    )
                    st.session_state.parecer_preceptor = resultado
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao gerar avaliação do Preceptor: {e}")


# 8. Gerenciamento de Estado da Navegação
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


def iniciar_consulta_com_nivel(especialidade, nivel):
    caso = criar_caso_por_nivel(especialidade, nivel)
    st.session_state.nivel_ativo = nivel
    st.session_state.caso_atual = caso
    st.session_state.parecer_preceptor = None
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": caso["primeira_fala"],
        }
    ]


# ==============================================================================
# MENU LATERAL COM NAVEGAÇÃO DE PÁGINAS (Incluindo Sugestões)
# ==============================================================================
with st.sidebar:
    if os.path.exists("logotipo.jpg"):
        st.image("logotipo.jpg", use_container_width=True)
    else:
        st.markdown("## 🧠 AnamnesIA")
    st.caption("Guia Rápido de Anamnese")
    
    st.markdown("---")
    pagina_selecionada = st.radio(
        "Navegação",
        ["🩺 Simulador Clínico", "💡 Enviar Sugestão / Feedback"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown(
        """
        **Roteiro sugerido:**
        1. **Queixa Principal e HDA:** Início, duração, intensidade, irradiação.
        2. **Antecedentes Pessoais:** Doenças crônicas, cirurgias.
        3. **Medicações e Alergias:** Uso contínuo e alergias.
        4. **Hábitos e Família:** Tabagismo, etilismo, histórico familiar.
        """
    )


# ==============================================================================
# TELA DE SUGESTÕES / FEEDBACK
# ==============================================================================
if pagina_selecionada == "💡 Enviar Sugestão / Feedback":
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-badges">
                <span class="hero-badge">💡 CANAL DE MELHORIA CONTÍNUA</span>
                <span class="hero-badge">✨ SUA OPINIÃO IMPORTA</span>
            </div>
            <div class="hero-title">
                Envie sua Sugestão ou <span class="ia-strong">Feedback</span>
            </div>
            <div class="hero-subtitle">
                Ajude a melhorar o AnamnesIA sugerindo novas especialidades, casos clínicos ou melhorias na plataforma.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("form_sugestoes"):
        nome_usuario = st.text_input("Seu Nome ou Perfil (Opcional)", placeholder="Ex: Estudante de Medicina / Dr(a). Nome...")
        tipo_feedback = st.selectbox(
            "Tipo de Sugestão",
            ["Nova Especialidade Médica", "Novo Caso Clínico / Ideia de Sintoma", "Correção Técnica ou Erro", "Melhoria na Interface / Aplicativo", "Outro"]
        )
        mensagem_feedback = st.text_area(
            "Descreva sua sugestão detalhadamente:",
            placeholder="Conte-nos o que você gostaria de ver na plataforma ou como podemos melhorá-la...",
            height=140
        )
        enviar_sugestao = st.form_submit_button("📤 Enviar Sugestão", type="primary", use_container_width=True)

    if enviar_sugestao:
        if not mensagem_feedback.strip():
            st.warning("⚠️ Por favor, escreva a sua sugestão antes de enviar.")
        else:
            # Aqui você pode salvar em arquivo local, banco ou apenas exibir o sucesso para o usuário
            st.success("🎉 **Sugestão enviada com sucesso!** Muito obrigado por contribuir para a evolução do AnamnesIA.")
            st.balloons()


# ==============================================================================
# TELA 1: SELEÇÃO DE ESPECIALIDADES (SIMULADOR)
# ==============================================================================
elif st.session_state.especialidade_ativa is None:
    # Exibe o logotipo junto com o título e a frase na cor branca no Banner Principal
    logo_html = ""
    if os.path.exists("logotipo.jpg"):
        import base64
        with open("logotipo.jpg", "rb") as f:
            data = f.read()
            encoded = base64.b64encode(data).decode()
            logo_html = f'<img src="data:image/jpeg;base64,{encoded}" style="height: 52px; vertical-align: middle; margin-right: 12px; border-radius: 6px;">'

    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-badges">
                <span class="hero-badge">✨ SIMULADOR DE PACIENTE VIRTUAL</span>
                <span class="hero-badge">🩺 {len(ESPECIALIDADES)} ESPECIALIDADES</span>
                <span class="hero-badge">🎚️ 3 NÍVEIS DE DIFICULDADE</span>
            </div>
            <div class="hero-title">
                {logo_html} Anamnes<span class="ia-strong">IA</span>
            </div>
            <div class="hero-subtitle">
                Plataforma inteligente de simulação clínica para treinamento de anamnese e raciocínio médico.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_titulo, col_busca = st.columns([2, 1])
    with col_titulo:
        st.subheader("1️⃣ Escolha a especialidade médica:")
    with col_busca:
        busca = st.text_input(
            "Buscar especialidade",
            placeholder="🔍 Buscar especialidade ou cenário...",
            label_visibility="collapsed",
        )

    especialidades_filtradas = {
        nome: dados
        for nome, dados in ESPECIALIDADES.items()
        if busca.lower() in nome.lower()
        or busca.lower() in dados["cenario"].lower()
        or busca.lower() in dados["descricao"].lower()
    }

    if not especialidades_filtradas:
        st.info("Nenhuma especialidade encontrada com esse termo. Limpe a busca para ver todas as 24 opções.")
    else:
        lista_itens = list(especialidades_filtradas.items())
        for i in range(0, len(lista_itens), 3):
            cols = st.columns(3)
            for idx, (nome, dados) in enumerate(lista_itens[i : i + 3]):
                with cols[idx]:
                    st.markdown(
                        f"""
                        <div class="spec-card">
                            <div class="spec-title">{dados['icone']} {nome}</div>
                            <div class="spec-scenario">📍 Cenário: {dados['cenario']}</div>
                            <div class="spec-desc">{dados['descricao']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "Selecionar Especialidade ➔",
                        key=f"btn_{nome}",
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state.especialidade_ativa = nome
                        st.session_state.nivel_ativo = None
                        st.session_state.caso_atual = None
                        st.session_state.messages = []
                        st.session_state.parecer_preceptor = None
                        st.rerun()

# ==============================================================================
# TELA 2: SELEÇÃO DO NÍVEL DE DIFICULDADE (FÁCIL, MÉDIO OU DIFÍCIL)
# ==============================================================================
elif st.session_state.nivel_ativo is None:
    esp_atual = st.session_state.especialidade_ativa
    info_esp = ESPECIALIDADES[esp_atual]

    if st.button("⬅️ Voltar para Todas as Especialidades"):
        st.session_state.especialidade_ativa = None
        st.rerun()

    st.markdown(
        f"""
        <div class="hero-banner" style="margin-top: 0.5rem;">
            <div class="hero-badges">
                <span class="hero-badge">{info_esp['icone']} {esp_atual.upper()}</span>
                <span class="hero-badge">📍 {info_esp['cenario'].upper()}</span>
            </div>
            <div class="hero-title" style="font-size: 1.75rem;">
                2️⃣ Selecione o Nível da <span class="ia-strong">Anamnese</span>
            </div>
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
                    <div class="spec-title">{chave_nivel} — {info_nivel['titulo'].split('—')[-1].strip()}</div>
                    <div class="spec-scenario">🎯 {info_nivel['subtitulo']}</div>
                    <div class="spec-desc">{info_nivel['descricao']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                f"Iniciar Nível {chave_nivel.split()[-1]} ➔",
                key=f"nivel_{chave_nivel}",
                type="primary",
                use_container_width=True,
            ):
                with st.spinner(f"🩺 Preparando prontuário ({chave_nivel}) e chamando o paciente..."):
                    iniciar_consulta_com_nivel(esp_atual, chave_nivel)
                st.rerun()

# ==============================================================================
# TELA 3: CONSULTÓRIO VIRTUAL
# ==============================================================================
else:
    esp_atual = st.session_state.especialidade_ativa
    nivel_atual = st.session_state.nivel_ativo
    info_esp = ESPECIALIDADES[esp_atual]
    dados_caso = st.session_state.caso_atual

    # Barra superior com navegação e botão evidente de Diagnóstico Final
    col_b1, col_b2, col_b3, col_b4 = st.columns([1, 1, 1, 1.35])
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
            with st.spinner("🩺 Gerando um novo paciente neste nível..."):
                iniciar_consulta_com_nivel(esp_atual, nivel_atual)
            st.rerun()
    with col_b4:
        if st.button("🎓 Enviar Diagnóstico", type="primary", use_container_width=True):
            abrir_modal_diagnostico(esp_atual, nivel_atual, dados_caso)

    # Faixa superior da consulta ativa
    st.markdown(
        f"""
        <div class="hero-banner" style="padding: 1.3rem 1.8rem; margin-top: 0.5rem;">
            <div class="hero-badges">
                <span class="hero-badge">{info_esp['icone']} {esp_atual.upper()}</span>
                <span class="hero-badge">{nivel_atual.upper()}</span>
                <span class="hero-badge">📍 {info_esp['cenario'].upper()}</span>
                <span class="hero-badge">🧑 PACIENTE: {dados_caso['paciente'].upper()}</span>
            </div>
            <div class="hero-title" style="font-size: 1.6rem;">{dados_caso.get('titulo_caso', 'Consultório Virtual — AnamnesIA')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Parecer do Preceptor no topo após envio do diagnóstico
    if st.session_state.parecer_preceptor:
        with st.container(border=True):
            st.success("✅ **Consulta Finalizada! Confira abaixo a avaliação do Preceptor Virtual:**")
            st.markdown(st.session_state.parecer_preceptor)
            c_prox1, c_prox2 = st.columns(2)
            with c_prox1:
                if st.button("🎲 Sortear Outro Caso neste Nível", type="primary", use_container_width=True):
                    with st.spinner("🩺 Chamando próximo paciente..."):
                        iniciar_consulta_com_nivel(esp_atual, nivel_atual)
                    st.rerun()
            with c_prox2:
                if st.button("🩺 Escolher Outra Especialidade", use_container_width=True):
                    st.session_state.especialidade_ativa = None
                    st.session_state.nivel_ativo = None
                    st.session_state.caso_atual = None
                    st.session_state.messages = []
                    st.session_state.parecer_preceptor = None
                    st.rerun()

    # Histórico limpo da conversa
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Caixa de digitação do chat
    if prompt := st.chat_input("Digite sua pergunta de anamnese para o paciente..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        contents = []
        for m in st.session_state.messages[1:]:
            api_role = "user" if m["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=api_role,
                    parts=[types.Part.from_text(text=m["content"])],
                )
            )

        instrucao_completa = (
            f"{dados_caso['prompt_sistema']}\n\n"
            f"Nível de dificuldade da simulação: {nivel_atual}.\n"
            f"Contexto: Você iniciou a consulta dizendo: \"{dados_caso['primeira_fala']}\""
        )

        with st.chat_message("assistant"):
            with st.spinner("O paciente está respondendo..."):
                try:
                    resposta_ia = gerar_resposta_ia(contents, instrucao_completa, temperatura=0.7)
                    st.markdown(resposta_ia)
                    st.session_state.messages.append({"role": "assistant", "content": resposta_ia})
                except Exception as e:
                    st.error(f"Ocorreu um erro ao falar com a IA: {e}")
