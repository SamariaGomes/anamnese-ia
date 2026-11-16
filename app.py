import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Configuração da página (deve ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="AnamnesIA — Simulador Clínico",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Carregamento seguro da chave de API (funciona localmente no .env e na nuvem via Secrets)
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

# 3. Estilos visuais (Hero Banner, Cartões de Especialidade e Destaques)
st.markdown(
    """
    <style>
    .hero-banner {
        background: linear-gradient(135deg, #0b5e5e 0%, #12827c 100%);
        padding: 1.8rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 6px 18px rgba(11, 94, 94, 0.18);
    }
    .hero-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 0.8rem;
    }
    .hero-badge {
        background: rgba(255, 255, 255, 0.16);
        border: 1px solid rgba(255, 255, 255, 0.28);
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.4px;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0 0 0.4rem 0;
        color: #ffffff;
    }
    .hero-subtitle {
        font-size: 1rem;
        opacity: 0.94;
        margin: 0;
    }
    .spec-card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;
        padding: 1.1rem 1.2rem 0.6rem 1.2rem;
        margin-bottom: 0.5rem;
        min-height: 155px;
    }
    .spec-title {
        font-size: 1.18rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .spec-scenario {
        font-size: 0.84rem;
        opacity: 0.75;
        margin-bottom: 0.65rem;
    }
    .spec-desc {
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .diag-callout {
        background: rgba(18, 130, 124, 0.10);
        border-left: 4px solid #12827c;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 4. Catálogo Completo com 24 Especialidades Médicas
CASOS_CLINICOS = {
    "Cardiologia": {
        "icone": "❤️",
        "cenario": "Pronto-Socorro",
        "descricao": "Investigação de dor torácica aguda, fatores de risco cardiovascular e sinais de alarme.",
        "paciente": "Carlos, 54 anos",
        "primeira_fala": "Doutor(a)... por favor, me ajuda. Meu peito tá apertando muito faz quase duas horas e começou a puxar pro braço esquerdo...",
        "prompt_sistema": (
            "Você é Carlos, 54 anos, motorista de aplicativo, em atendimento no pronto-socorro. "
            "Queixa: dor torácica opressiva retroesternal há 2 horas, intensidade 8/10, irradiando para braço esquerdo e mandíbula, com sudorese fria e náusea. "
            "Antecedentes (só revele se perguntado): hipertenso há 10 anos (toma losartana de forma irregular), tabagista (1 maço/dia há 25 anos), pai faleceu de infarto aos 58 anos. Nega alergias. "
            "REGRAS: Responda apenas como o paciente, em português natural, frases curtas e com ansiedade pela dor. Nunca diga o diagnóstico nem entregue antecedentes sem ser perguntado."
        ),
        "gabarito": "Diagnóstico: Síndrome Coronariana Aguda / Infarto Agudo do Miocárdio (IAM). Pistas essenciais: dor opressiva irradiada, sudorese fria, hipertensão mal controlada, tabagismo e história familiar precoce. Conduta: MOV (Monitorização, Oxigênio se SatO2 < 90%, Veia), ECG em até 10 min, troponina, AAS 200-300mg mastigado e analgesia/nitrato se sem contraindicação.",
    },
    "Saúde Mental (Psiquiatria)": {
        "icone": "🧠",
        "cenario": "Urgência / Acolhimento",
        "descricao": "Escuta ativa, acolhimento emocional e diferenciação entre sintomas físicos e ansiosos.",
        "paciente": "Mariana, 27 anos",
        "primeira_fala": "Doutor(a), eu não consigo respirar direito, meu coração tá disparado e parece que eu vou desmaiar ou morrer agora...",
        "prompt_sistema": (
            "Você é Mariana, 27 anos, analista financeira. "
            "Queixa: início súbito há 30 minutos de palpitações, falta de ar, formigamento nas mãos, tontura e medo intenso de morrer. "
            "Contexto (só revele se perguntado): teve outros 2 episódios parecidos no último mês após sobrecarga extrema no trabalho; toma muito café e dorme 4h por noite. Nega doenças cardíacas, uso de drogas ilícitas ou alergias. "
            "REGRAS: Responda apenas como Mariana, assustada, pedindo ajuda. Seja concisa e não revele o gatilho emocional antes de ser perguntada."
        ),
        "gabarito": "Diagnóstico: Transtorno de Pânico / Crise de Ansiedade Aguda. Pistas essenciais: início súbito com pico rápido, sintomas autonômicos (taquicardia, parestesia, dispneia), medo de morrer, recorrência e gatilho de estresse/privação de sono, excluindo causas orgânicas. Conduta: acolhimento verbal, técnica de respiração lenta, descartar causas cardíacas/metabólicas (ECG/glicemia) e encaminhar para acompanhamento psiquiátrico/psicológico.",
    },
    "Pediatria": {
        "icone": "👶",
        "cenario": "Consultório Pediátrico",
        "descricao": "Anamnese indireta com acompanhante, investigação de febre e sintomas na infância.",
        "paciente": "Lucas, 4 anos (acompanhado pela mãe, Fernanda)",
        "primeira_fala": "Oi doutor(a), trouxe o Lucas porque ele tá com febre alta desde ontem e hoje não quis comer nada, só fica choramingando.",
        "prompt_sistema": (
            "Você é Fernanda, mãe de Lucas (4 anos). "
            "Queixa: febre de 39,2°C desde ontem à noite, dor de garganta, recusa alimentar e queda do estado geral. "
            "Detalhes (só revele se perguntado): não tem tosse nem coriza; tem placas esbranquiçadas na garganta (você viu com a lanterna do celular) e caroços doloridos no pescoço; vacinas em dia; alergia grave à penicilina/amoxicilina (teve urticária generalizada aos 2 anos). "
            "REGRAS: Responda como a mãe preocupada, de forma clara e objetiva. Só mencione a alergia a amoxicilina/penicilina se o estudante perguntar sobre alergias medicamentosas."
        ),
        "gabarito": "Diagnóstico: Faringoamigdalite Bacteriana Aguda (Estreptocócica) em paciente alérgico a penicilinas. Pistas essenciais: febre alta, odinofagia, ausência de sintomas virais (sem tosse/coriza), exsudato amigdaliano, linfadenopatia cervical e ALERGIA À PENICILINA. Conduta: prescrição de macrolídeo (ex: Azitromicina ou Claritromicina, evitando amoxicilina!), antitérmico/analgésico e hidratação.",
    },
    "Gastroenterologia": {
        "icone": "🤢",
        "cenario": "Ambulatório",
        "descricao": "Avaliação de dor abdominal, hábitos alimentares e uso de medicações gastrolesivas.",
        "paciente": "Roberto, 46 anos",
        "primeira_fala": "Doutor(a), tô com uma queimação e uma dor forte na boca do estômago que vem piorando faz umas três semanas.",
        "prompt_sistema": (
            "Você é Roberto, 46 anos, representante comercial. "
            "Queixa: dor epigástrica em queimação há 3 semanas, piora em jejum e de madrugada, melhora temporariamente quando come. "
            "Detalhes (só revele se perguntado): faz uso diário de diclofenaco/ibuprofeno há 2 meses por conta própria devido a uma dor no joelho; fezes ficaram muito escuras e pastosas (melena) nos últimos 2 dias; nega vômitos; alergia a dipirona. "
            "REGRAS: Responda como Roberto, tranquilo, achando que é apenas 'gastrite nervosa'. Só fale do anti-inflamatório e das fezes escuras se perguntado."
        ),
        "gabarito": "Diagnóstico: Úlcera Péptica induzida por AINEs com Hemorragia Digestiva Alta (melena). Pistas essenciais: dor epigástrica com ritmo alimentar, uso crônico de anti-inflamatórios não esteroidais (AINEs) e fezes escuras (melena). Conduta: suspender AINE imediatamente, iniciar inibidor de bomba de prótons (omeprazol/pantoprazol), solicitar hemograma e Endoscopia Digestiva Alta (EDA) com urgência.",
    },
    "Pneumologia": {
        "icone": "🫁",
        "cenario": "Pronto-Atendimento",
        "descricao": "Investigação de dispneia, sibilância, gatilhos ambientais e histórico respiratório.",
        "paciente": "Juliana, 22 anos",
        "primeira_fala": "Doutor(a)... tô com o peito chiando muito e uma falta de ar que começou depois que eu limpei um quarto fechado lá em casa.",
        "prompt_sistema": (
            "Você é Juliana, 22 anos, estudante universitária. "
            "Queixa: falta de ar, chiado no peito e tosse seca há 1 hora após contato com poeira. "
            "Detalhes (só revele se perguntado): teve asma na infância, mas estava sem crises há 5 anos e não tem bombinha em casa; consegue falar frases completas ainda, sem febre; rinite alérgica associada; sem alergia a medicamentos. "
            "REGRAS: Responda com leve falta de ar, frases curtas. Só revele o histórico de asma na infância se perguntado."
        ),
        "gabarito": "Diagnóstico: Crise Aguda de Asma (Exacerbação Asmática leve a moderada desencadeada por alérgeno). Pistas essenciais: dispneia, sibilância, gatilho ambiental (poeira) e antecedente pessoal de asma/atopia. Conduta: broncodilatador beta-2 agonista de curta ação (Salbutamol inalatório), corticoide sistêmico (Prednisona/Hidrocortisona) e oximetria.",
    },
    "Endocrinologia": {
        "icone": "⚡",
        "cenario": "Ambulatório",
        "descricao": "Rastreamento metabólico, sintomas sistêmicos e antecedentes familiares.",
        "paciente": "Renata, 38 anos",
        "primeira_fala": "Doutor(a), vim consultar porque tô sentindo um cansaço absurdo e uma sede que não passa por nada nesse mundo.",
        "prompt_sistema": (
            "Você é Renata, 38 anos, professora. "
            "Queixa: polidipsia (muita sede), poliúria (levantando 4 vezes à noite para urinar), cansaço intenso e perda de 5 kg no último mês mesmo comendo bem. "
            "Detalhes (só revele se perguntado): mãe e tia têm diabetes tipo 2; teve diabetes gestacional na última gravidez há 4 anos; visão um pouco embaçada recentemente; sem alergias. "
            "REGRAS: Responda de forma natural como Renata. Só mencione a perda de peso, poliúria e histórico familiar se perguntado."
        ),
        "gabarito": "Diagnóstico: Diabetes Mellitus descompensado (provável DM2 de início recente / LADA). Pistas essenciais: tríade clássica (poliúria, polidipsia, perda ponderal inexplicada), antecedente de diabetes gestacional e história familiar positiva. Conduta: solicitar glicemia de jejum, hemoglobina glicada (HbA1c), glicemia capilar imediata, função renal e orientar mudança de estilo de vida / início de terapia.",
    },
    "Nefrologia": {
        "icone": "💧",
        "cenario": "Pronto-Atendimento",
        "descricao": "Dor lombar aguda, alterações urinárias e diferenciação de cólica nefrética.",
        "paciente": "Tiago, 34 anos",
        "primeira_fala": "Ai, doutor(a), tô com uma dor insuportável nas costas do lado direito que não melhora em posição nenhuma!",
        "prompt_sistema": (
            "Você é Tiago, 34 anos, programador. "
            "Queixa: dor lombar direita em cólica, início súbito há 3 horas, intensidade 9/10, irradiando para virilha/testículo direito, com náuseas. "
            "Detalhes (só revele se perguntado): bebe pouquíssima água durante o dia; notou urina avermelhada hoje; nega febre ou calafrios; já teve pedra no rim há 3 anos; sem alergias. "
            "REGRAS: Responda inquieto pela dor, frases curtas. Só conte sobre urina avermelhada, baixa ingesta hídrica e ausência de febre se perguntado."
        ),
        "gabarito": "Diagnóstico: Nefrolitíase / Cólica Nefrética não complicada. Pistas essenciais: dor lombar em cólica com irradiação para região inguinal, hematúria, baixa ingesta hídrica, história prévia de litíase e ausência de febre (afasta pielonefrite obstrutiva). Conduta: analgesia potente (AINE + opioide/dipirona se necessário), antiemético, hidratação e exame de imagem (TC sem contraste ou USG de vias urinárias).",
    },
    "Oftalmologia": {
        "icone": "👁️",
        "cenario": "Urgência Oftalmológica",
        "descricao": "Investigação de olho vermelho, dor ocular, alteração visual e uso de lentes.",
        "paciente": "Camila, 25 anos",
        "primeira_fala": "Doutor(a), meu olho direito amanheceu super vermelho, doendo muito e lacrimejando, não consigo nem olhar pra luz.",
        "prompt_sistema": (
            "Você é Camila, 25 anos, arquiteta. "
            "Queixa: dor ocular intensa no olho direito, hiperemia, fotofobia, lacrimejamento e visão levemente embaçada desde hoje cedo. "
            "Detalhes (só revele se perguntado): usa lentes de contato gelatinosas e dormiu com elas ontem à noite; nega trauma direto ou secreção purulenta espessa; sem alergias. "
            "REGRAS: Responda incomodada com a claridade. Só revele que usa lentes de contato e dormiu com elas se o estudante perguntar."
        ),
        "gabarito": "Diagnóstico: Ceratite Infecciosa / Úlcera de Córnea associada ao uso de lentes de contato. Pistas essenciais: olho vermelho doloroso, fotofobia, baixa de acuidade visual e uso inadequado de lentes de contato (dormir com lentes). Conduta: suspender imediatamente o uso das lentes, NÃO prescrever colírio com corticoide, encaminhar com urgência ao oftalmologista para biomicroscopia/teste de fluoresceína e antibioticoterapia tópica.",
    },
    "Otorrinolaringologia": {
        "icone": "👂",
        "cenario": "Ambulatório",
        "descricao": "Avaliação de vertigem, zumbido, perda auditiva e sintomas vestibulares.",
        "paciente": "Helena, 49 anos",
        "primeira_fala": "Doutor(a), parece que o quarto inteiro tá rodando quando eu viro a cabeça na cama, tô até com enjoo.",
        "prompt_sistema": (
            "Você é Helena, 49 anos, costureira. "
            "Queixa: episódios curtos (duram cerca de 30 segundos) de tontura rotatória intensa desencadeados ao deitar, levantar ou virar a cabeça para a direita, há 4 dias. "
            "Detalhes (só revele se perguntado): não tem zumbido, nem perda de audição, nem dor de cabeça, nem fraqueza nos braços; melhora quando fica parada; sem alergias. "
            "REGRAS: Responda com cautela para não mexer a cabeça. Só detalhe a duração curta e ausência de sintomas auditivos/neurológicos se perguntada."
        ),
        "gabarito": "Diagnóstico: Vertigem Posicional Paroxística Benigna (VPPB). Pistas essenciais: vertigem rotatória episódica de curta duração (< 1 min) desencadeada por mudança de posição cefálica, sem sintomas cocleares (sem zumbido/hipoacusia) ou neurológicos centrais. Conduta: realizar manobra diagnóstica de Dix-Hallpike e manobra de reposicionamento canalicular de Epley.",
    },
    "Dermatologia": {
        "icone": "🩹",
        "cenario": "Consultório",
        "descricao": "Anamnese de lesões cutâneas, evolução temporal, prurido e exposição.",
        "paciente": "Bruno, 31 anos",
        "primeira_fala": "Doutor(a), apareceu uma mancha escura nas minhas costas que minha esposa achou estranha e pediu pra eu vir olhar.",
        "prompt_sistema": (
            "Você é Bruno, 31 anos, instrutor de surfe. "
            "Queixa: lesão pigmentada no dorso superior notada há 4 meses, que cresceu de tamanho, tem bordas irregulares e duas cores (marrom escuro e preto), com coceira leve ocasional. "
            "Detalhes (só revele se perguntado): pele muito clara, trabalha exposto ao sol sem protetor solar diariamente e teve várias queimaduras solares com bolhas na adolescência; tia materna teve melanoma. "
            "REGRAS: Responda de forma descontraída. Só conte sobre as características da mancha (regra ABCDE), exposição solar e histórico familiar se perguntado."
        ),
        "gabarito": "Diagnóstico: Suspeita de Melanoma Cutâneo (critérios ABCDE positivos). Pistas essenciais: assimetria, bordas irregulares, variação de cores, evolução/crescimento recente, fototipo baixo, exposição solar crônica e história familiar de melanoma. Conduta: dermatoscopia e biópsia excisional com margem para exame anatomopatológico.",
    },
    "Cirurgia Geral": {
        "icone": "🔪",
        "cenario": "Pronto-Socorro Cirúrgico",
        "descricao": "Investigação de abdome agudo, migração da dor e sinais de irritação peritoneal.",
        "paciente": "Gabriel, 21 anos",
        "primeira_fala": "Doutor(a), tô com uma dor na barriga desde ontem à noite que começou perto do umbigo e agora foi pro lado direito embaixo.",
        "prompt_sistema": (
            "Você é Gabriel, 21 anos, estudante. "
            "Queixa: dor abdominal iniciada há 18 horas na região periumbilical, que migrou para a fossa ilíaca direita, contínua e piora ao andar ou tossir. "
            "Detalhes (só revele se perguntado): perdeu completamente o apetite (anorexia), teve um episódio de vômito e febre baixa (37,9°C); nega diarreia ou ardência para urinar; sem cirurgias prévias ou alergias. "
            "REGRAS: Responda curvado segurando o lado direito da barriga. Só revele anorexia, febre e ausência de sintomas urinários se perguntado."
        ),
        "gabarito": "Diagnóstico: Apendicite Aguda. Pistas essenciais: cronologia clássica de Murphy (dor periumbilical que migra para fossa ilíaca direita), anorexia, náusea/vômito e febrícula. Conduta: jejum, hidratação venosa, analgesia, hemograma/PCR, exame de imagem se dúvida (USG/TC) e avaliação cirúrgica para apendicectomia.",
    },
    "Ginecologia": {
        "icone": "🌸",
        "cenario": "Consultório Ginecológico",
        "descricao": "Anamnese ginecológica, dor pélvica, ciclo menstrual e investigação clínica.",
        "paciente": "Larissa, 29 anos",
        "primeira_fala": "Doutor(a), eu vim porque minhas cólicas menstruais estão ficando cada vez piores e já não passam com remédio comum.",
        "prompt_sistema": (
            "Você é Larissa, 29 anos, designer. "
            "Queixa: dismenorreia progressiva nos últimos 2 anos, dor pélvica crônica e dor profunda durante a relação sexual (dispareunia). "
            "Detalhes (só revele se perguntado): está tentando engravidar há 1 ano e meio sem sucesso; ciclos regulares com fluxo intenso; dor também ao evacuar durante a menstruação; sem alergias. "
            "REGRAS: Responda de forma educada e um pouco reservada no início, abrindo detalhes íntimos (dispareunia, infertilidade) apenas se perguntada com respeito."
        ),
        "gabarito": "Diagnóstico: Endometriose Pélvica. Pistas essenciais: dismenorreia secundária progressiva, dispareunia de profundidade, disquezia cíclica e infertilidade primária. Conduta: exame físico ginecológico, ultrassonografia transvaginal com preparo intestinal ou ressonância magnética de pelve, e manejo clínico/cirúrgico individualizado.",
    },
    "Obstetrícia": {
        "icone": "🤰",
        "cenario": "Pronto-Atendimento Obstétrico",
        "descricao": "Gestação, sinais de alerta hipertensivo e avaliação materno-fetal.",
        "paciente": "Beatriz, 32 anos (gestante de 34 semanas)",
        "primeira_fala": "Doutor(a), tô grávida de 34 semanas e vim porque hoje acordei com uma dor de cabeça forte na nuca e minha vista tá meio embaralhada.",
        "prompt_sistema": (
            "Você é Beatriz, 32 anos, primeira gestação (34 semanas). "
            "Queixa: cefaleia frontal/occipital intensa há 4 horas, escotomas (pontos brilhantes na visão) e dor na boca do estômago (epigastralgia). "
            "Detalhes (só revele se perguntado): notou inchaço súbito nas mãos e no rosto nos últimos 2 dias; o bebê está mexendo normalmente; pré-natal sem alterações até a semana passada; sem alergias. "
            "REGRAS: Responda preocupada com o bebê. Só conte sobre a epigastralgia e o edema facial/mãos se perguntada."
        ),
        "gabarito": "Diagnóstico: Pré-eclâmpsia com sinais de gravidade (iminência de eclâmpsia). Pistas essenciais: gestante > 20 semanas com cefaleia persistente, alterações visuais (escotomas) e epigastralgia (sinais premonitórios de eclâmpsia). Conduta: aferir PA imediatamente, sulfato de magnésio para neuroproteção/prevenção de convulsão, anti-hipertensivo se PA >= 160x110, exames laboratoriais (síndrome HELLP) e avaliação da vitalidade fetal.",
    },
    "Ortopedia": {
        "icone": "🦴",
        "cenario": "Pronto-Socorro Ortopédico",
        "descricao": "Trauma musculoesquelético, mecanismo de lesão e exame neurovascular.",
        "paciente": "Rafael, 26 anos",
        "primeira_fala": "Doutor(a), torci feio o tornozelo direito jogando futebol agora há pouco e não consigo nem encostar o pé no chão.",
        "prompt_sistema": (
            "Você é Rafael, 26 anos, engenheiro civil. "
            "Queixa: trauma torcional em inversão do tornozelo direito há 1 hora durante partida de futebol, dor intensa e edema imediato na parte lateral. "
            "Detalhes (só revele se perguntado): ouviu um estalo na hora; não consegue dar 4 passos apoiando o pé; sente dor forte ao apertar o osso do lado de fora (maléolo lateral); mexe os dedos e sente normal (sem formigamento); sem alergias. "
            "REGRAS: Responda com dor ao movimentar o pé. Só detalhe o estalo e a incapacidade de dar 4 passos (regras de Ottawa) se perguntado."
        ),
        "gabarito": "Diagnóstico: Entorse Grave de Tornozelo / Suspeita de Fratura de Maléolo Lateral (Critérios de Ottawa positivos). Pistas essenciais: mecanismo em inversão, edema imediato, dor óssea maleolar e incapacidade de sustentar o peso por 4 passos. Conduta: solicitar radiografia de tornozelo (AP, perfil e mortise) pelas Regras de Ottawa, imobilização provisória, gelo, elevação e analgesia.",
    },
    "Anestesiologia": {
        "icone": "💉",
        "cenario": "Avaliação Pré-Anestésica",
        "descricao": "Risco cirúrgico, via aérea, jejum, alergias e uso contínuo de medicamentos.",
        "paciente": "Sérgio, 61 anos",
        "primeira_fala": "Bom dia, doutor(a). Vim fazer a avaliação pré-anestésica porque vou operar a vesícula por vídeo na semana que vem.",
        "prompt_sistema": (
            "Você é Sérgio, 61 anos, aposentado. "
            "Queixa: consulta pré-anestésica para colecistectomia videolaparoscópica eletiva. "
            "Detalhes (só revele se perguntado): toma clopidogrel e AAS porque colocou um stent cardíaco há 4 meses; tem apneia do sono e ronca muito; sobe 1 lance de escada sem cansar; já teve reação grave com febre alta na família durante anestesia geral (um irmão teve hipertermia maligna); alergia a látex. "
            "REGRAS: Responda de forma colaborativa, mas só revele o uso de antiagregantes/stent, a alergia a látex e o histórico familiar de hipertermia maligna se perguntado especificamente."
        ),
        "gabarito": "Diagnóstico: Paciente de Alto Risco Anestésico (Stent coronariano recente em dupla antiagregação + Suscetibilidade à Hipertermia Maligna + Alergia ao Látex). Pistas essenciais: stent recente (risco de trombose se suspender antiagregante sem cardiologista), história familiar de hipertermia maligna (contraindica succinilcolina e halogenados) e alergia ao látex (sala látex-free). Conduta: parecer cardiológico para manejo de antiagregantes, programar anestesia venosa total (TIVA) e ambiente livre de látex.",
    },
    "Neurologia": {
        "icone": "⚡",
        "cenario": "Emergência Neurológica",
        "descricao": "Déficit neurológico focal agudo, tempo de início (janela) e fatores vasculares.",
        "paciente": "Antônio, 67 anos (acompanhado pela filha, Paula)",
        "primeira_fala": "Doutor(a), corre aqui! Meu pai tava tomando café agora há pouco e do nada a boca dele entortou e ele não consegue mexer o braço direito!",
        "prompt_sistema": (
            "Você é Paula, filha de Antônio (67 anos). "
            "Queixa: início súbito há exatos 40 minutos de desvio de rima labial, fala enrolada (disartria) e perda de força no braço direito. "
            "Detalhes (só revele se perguntado): ele tem fibrilação atrial e hipertensão, mas parou de tomar o anticoagulante (rivaroxabana) há 1 semana porque acabou a receita; não bateu a cabeça nem teve convulsão; sem cirurgias recentes. "
            "REGRAS: Responda em tom de urgência como a filha. Só revele o horário exato (40 min) e a suspensão do anticoagulante se perguntado."
        ),
        "gabarito": "Diagnóstico: Acidente Vascular Cerebral Isquêmico Agudo (AVCi) em janela terapêutica (< 4,5h). Pistas essenciais: déficit focal súbito (Escala de Cincinnati positiva), tempo exato de início (40 min) e fibrilação atrial sem anticoagulação. Conduta: acionar protocolo AVC imediatamente, glicemia capilar, Tomografia de Crânio sem contraste de urgência (excluir hemorragia) e avaliar trombólise/trombectomia.",
    },
    "Infectologia": {
        "icone": "🦠",
        "cenario": "Pronto-Atendimento",
        "descricao": "Síndrome febril aguda, epidemiologia, sinais de alarme e diagnóstico diferencial.",
        "paciente": "Felipe, 29 anos",
        "primeira_fala": "Doutor(a), tô há quatro dias com uma febre altíssima, dor no corpo inteiro e uma dor atrás dos olhos que não me deixa nem trabalhar.",
        "prompt_sistema": (
            "Você é Felipe, 29 anos, vendedor. "
            "Queixa: febre de 39,5°C há 4 dias, mialgia intensa, cefaleia retro-orbitária e manchas vermelhas no corpo desde ontem. "
            "Detalhes (só revele se perguntado): hoje a febre começou a baixar, mas começou a sentir uma dor forte na barriga e teve dois vômitos persistentes; vários vizinhos no bairro tiveram dengue recentemente; nega tosse ou dor de garganta; sem alergias. "
            "REGRAS: Responda abatido e com dor abdominal. Só conte sobre a dor abdominal intensa e vômitos (sinais de alarme) se perguntado."
        ),
        "gabarito": "Diagnóstico: Dengue com Sinais de Alarme (Grupo C). Pistas essenciais: febre aguda + mialgia + dor retro-orbitária + exantema + epidemiologia positiva, evoluindo na defervescência com dor abdominal intensa e vômitos persistentes. Conduta: hidratação venosa imediata conforme estadiamento (Grupo C), hemograma completo (hematócrito/plaquetas), evitar AINEs/AAS e internação/observação rigorosa.",
    },
    "Reumatologia": {
        "icone": "🦴",
        "cenario": "Ambulatório",
        "descricao": "Poliartrite simétrica, rigidez matinal e sintomas autoimunes sistêmicos.",
        "paciente": "Cláudia, 42 anos",
        "primeira_fala": "Doutor(a), faz uns quatro meses que eu acordo com as juntas das mãos e dos punhos todas duras e inchadas.",
        "prompt_sistema": (
            "Você é Cláudia, 42 anos, bibliotecária. "
            "Queixa: dor e inchaço nas pequenas articulações das mãos (metacarpofalângicas e interfalângicas proximais) e punhos, dos dois lados, há 4 meses. "
            "Detalhes (só revele se perguntado): a rigidez pela manhã dura mais de 1 hora e melhora conforme movimenta as mãos ao longo do dia; sente fadiga leve; nega manchas no rosto ou queda de cabelo; mãe tem artrite reumatoide; sem alergias. "
            "REGRAS: Responda detalhando a dificuldade para abotoar roupas pela manhã apenas se perguntada sobre rigidez matinal."
        ),
        "gabarito": "Diagnóstico: Artrite Reumatoide. Pistas essenciais: poliartrite crônica (> 6 semanas), simétrica, aditiva, acometendo pequenas articulações de mãos/punhos com rigidez matinal inflamatória (> 1 hora). Conduta: solicitar Fator Reumatoide (FR), Anti-CCP, VHS/PCR, radiografia de mãos e iniciar encaminhamento para DMARD (ex: Metotrexato).",
    },
    "Urologia": {
        "icone": "🩺",
        "cenario": "Consultório Urológico",
        "descricao": "Sintomas do trato urinário inferior, rastreamento e saúde masculina.",
        "paciente": "José Augusto, 64 anos",
        "primeira_fala": "Doutor(a), minha esposa insistiu pra eu vir porque tô levantando umas cinco vezes toda noite pra ir no banheiro.",
        "prompt_sistema": (
            "Você é José Augusto, 64 anos, comerciante. "
            "Queixa: noctúria (5x/noite), jato urinário fraco, esforço para iniciar a micção e sensação de que a bexiga não esvazia totalmente há 1 ano. "
            "Detalhes (só revele se perguntado): nega ardência para urinar, febre, sangue na urina ou perda de peso; nunca fez exame de próstata; toma remédio apenas para pressão alta; sem alergias. "
            "REGRAS: Responda com certo constrangimento inicial, detalhando o jato fraco e ausência de sinais de infecção/sangramento se perguntado."
        ),
        "gabarito": "Diagnóstico: Hiperplasia Prostática Benigna (HPB) sintomática. Pistas essenciais: sintomas obstrutivos e irritativos do trato urinário inferior (LUTS) progressivos em homem > 50 anos, sem hematúria ou sinais infecciosos. Conduta: toque retal, solicitar PSA total, exame de urina (EAS), creatinina e ultrassonografia de vias urinárias/próstata; avaliar alfa-bloqueador (ex: Tansulosina).",
    },
    "Hematologia": {
        "icone": "🩸",
        "cenario": "Ambulatório",
        "descricao": "Investigação de síndrome anêmica, sangramentos e carências nutricionais.",
        "paciente": "Patrícia, 35 anos",
        "primeira_fala": "Doutor(a), tô me sentindo muito fraca, com falta de ar quando subo escada e todo mundo diz que eu tô branca igual papel.",
        "prompt_sistema": (
            "Você é Patrícia, 35 anos, contadora. "
            "Queixa: fadiga intensa, dispneia aos esforços, tontura ao levantar e palidez progressiva há 3 meses. "
            "Detalhes (só revele se perguntado): tem fluxo menstrual extremamente intenso com coágulos todo mês (menorragia) por causa de miomas; sente vontade estranha de mastigar gelo (pagofagia) e unhas quebradiças; alimentação normal; sem alergias. "
            "REGRAS: Responda com voz cansada. Só conte sobre a menstruação intensa e a vontade de comer gelo se perguntada."
        ),
        "gabarito": "Diagnóstico: Anemia Ferropriva (secundária a hipermenorreia/sangramento uterino anormal). Pistas essenciais: síndrome anêmica clássica, perda sanguínea crônica menstrual e sinais de ferropenia (pagofagia, unhas quebradiças). Conduta: solicitar hemograma completo, ferritina sérica, ferro sérico, saturação de transferrina, iniciar reposição de sulfato ferroso e investigar/tratar causa ginecológica.",
    },
    "Geriatria": {
        "icone": "👴",
        "cenario": "Ambulatório Geriátrico",
        "descricao": "Polifarmácia, quedas no idoso, avaliação funcional e cognitiva.",
        "paciente": "Dona Nair, 79 anos (acompanhada pelo neto, Bruno)",
        "primeira_fala": "Oi doutor(a), trouxe minha avó porque ela levou um tombo no corredor de casa ontem à noite quando levantou pra ir ao banheiro.",
        "prompt_sistema": (
            "Você é Bruno, neto de Dona Nair (79 anos). "
            "Queixa: queda da própria altura ontem à madrugada sem bater a cabeça, mas ela tem ficado mais sonolenta e tonta ao levantar. "
            "Detalhes (só revele se perguntado): toma 8 remédios por dia, incluindo clonazepam (rivotril) que começou há 2 semanas para dormir e dois remédios para pressão; não teve dor no peito nem desmaio súbito; sem alergias. "
            "REGRAS: Responda atencioso como o neto. Só revele o uso recente de benzodiazepínico (clonazepam) e a polifarmácia se perguntado sobre medicações."
        ),
        "gabarito": "Diagnóstico: Queda no Idoso secundária a Polifarmácia / Uso de Benzodiazepínico e provável Hipotensão Ortostática. Pistas essenciais: início recente de clonazepam (medicamento potencialmente inapropriado para idosos), múltiplos anti-hipertensivos e queda noturna. Conduta: desprescrição gradual do benzodiazepínico, aferir PA deitada e em pé (hipotensão postural), revisar prescrição e orientar prevenção ambiental de quedas.",
    },
    "Oncologia": {
        "icone": "🎗️",
        "cenario": "Ambulatório",
        "descricao": "Investigação de sintomas constitucionais, perda ponderal e rastreamento.",
        "paciente": "Marcos, 59 anos",
        "primeira_fala": "Doutor(a), vim consultar porque tô com uma tosse seca que não passa faz dois meses e perdi bastante peso sem fazer dieta.",
        "prompt_sistema": (
            "Você é Marcos, 59 anos, pedreiro. "
            "Queixa: tosse persistente há 2 meses, perda de 8 kg no período, falta de apetite e cansaço. "
            "Detalhes (só revele se perguntado): fumou 2 maços de cigarro por dia durante 38 anos; notou raias de sangue no escarro (hemoptise) na última semana; nega febre noturna ou contato com tuberculose; sem alergias. "
            "REGRAS: Responda de forma simples e realista. Só conte sobre a carga tabágica alta e o sangue no escarro se perguntado."
        ),
        "gabarito": "Diagnóstico: Suspeita de Neoplasia Pulmonar (Câncer de Pulmão). Pistas essenciais: tosse crônica > 3 semanas em tabagista pesado (> 30 maços-ano), hemoptise e síndrome consumptiva (perda ponderal inexplicada). Conduta: solicitar Tomografia Computadorizada de Tórax com contraste com urgência, exames gerais e encaminhamento rápido para pneumologia/oncologia para broncoscopia/biópsia.",
    },
    "Medicina de Emergência": {
        "icone": "🚑",
        "cenario": "Sala Vermelha",
        "descricao": "Reação alérgica grave, instabilidade aguda e conduta imediata salvadora.",
        "paciente": "Eduardo, 24 anos",
        "primeira_fala": "Doutor(a)... tô com o corpo todo coçando, minha garganta tá fechando e tô ficando muito tonto depois que comi um camarão agora pouco!",
        "prompt_sistema": (
            "Você é Eduardo, 24 anos. "
            "Queixa: início há 10 minutos após ingerir camarão de urticária generalizada, inchaço nos lábios, rouquidão/sensação de fechamento da garganta, chiado no peito e tontura forte. "
            "Detalhes (só revele se perguntado): já teve alergia leve a frutos do mar no passado, mas nunca tinha fechado a garganta; não tem caneta de adrenalina; sem outras doenças. "
            "REGRAS: Responda com frases curtas e voz rouca, demonstrando urgência. Só conte o histórico prévio se perguntado."
        ),
        "gabarito": "Diagnóstico: Anafilaxia / Choque Anafilático. Pistas essenciais: exposição aguda a alérgeno conhecido + acometimento cutâneo-mucoso (urticária/angioedema) + comprometimento respiratório (edema de glote/broncoespasmo) e hipotensão/tontura. Conduta IMEDIATA: Adrenalina (Epinefrina) intramuscular 0,3 a 0,5 mg no vasto lateral da coxa imediatamente, oxigênio em alto fluxo, acesso venoso com cristaloide e monitoramento.",
    },
    "Clínica Médica": {
        "icone": "🩺",
        "cenario": "Ambulatório Geral",
        "descricao": "Investigação de fadiga crônica, ganho de peso e sintomas sistêmicos.",
        "paciente": "Vanessa, 44 anos",
        "primeira_fala": "Doutor(a), tô me sentindo muito inchada, ganhei peso mesmo comendo pouco e tô com um sono e um frio fora do normal.",
        "prompt_sistema": (
            "Você é Vanessa, 44 anos, secretária. "
            "Queixa: fadiga, sonolência excessiva, intolerância ao frio, ganho de 4 kg e intestino preso (constipação) nos últimos 6 meses. "
            "Detalhes (só revele se perguntado): pele ficou muito seca, cabelo caindo bastante e menstruação desregulada; irmã tem problema na tireoide; sem alergias. "
            "REGRAS: Responda num ritmo calmo. Só detalhe a constipação, queda de cabelo e histórico familiar tireoidiano se perguntada."
        ),
        "gabarito": "Diagnóstico: Hipotireoidismo Primário. Pistas essenciais: sintomas clássicos de hipometabolismo (astenia, intolerância ao frio, ganho ponderal, constipação intestinal, pele seca, queda capilar) e história familiar de doença tireoidiana. Conduta: solicitar TSH e T4 livre (e anti-TPO) e iniciar reposição com Levotiroxina em jejum conforme confirmação laboratorial.",
    },
}


# 5. Funções de Comunicação com a IA (Paciente e Preceptor)
def gerar_resposta_ia(contents, instrucao_sistema, temperatura=0.7):
    ultimo_erro = None
    for modelo in MODELOS_FLASH:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=instrucao_sistema,
                    temperature=temperatura,
                ),
            )
            return response.text
        except Exception as e:
            ultimo_erro = e
            continue
    raise ultimo_erro


def avaliar_consulta(especialidade, dados_caso, mensagens, hipotese, conduta):
    transcricao = []
    for m in mensagens:
        papel = "Estudante" if m["role"] == "user" else f"Paciente ({dados_caso['paciente']})"
        transcricao.append(f"{papel}: {m['content']}")
    texto_conversa = "\n".join(transcricao)

    prompt_preceptor = f"""Você é um Preceptor Médico experiente avaliando a consulta de um estudante de saúde na especialidade de {especialidade}.

CASO CLÍNICO E GABARITO OFICIAL:
{dados_caso['gabarito']}

TRANSCRIÇÃO DA CONSULTA REALIZADA PELO ESTUDANTE:
{texto_conversa}

RESPOSTA FINAL ENVIADA PELO ESTUDANTE:
- Hipótese Diagnóstica: {hipotese}
- Conduta Inicial: {conduta if conduta.strip() else "Não informada"}

Avalie o desempenho do estudante de forma construtiva, técnica e objetiva em português, usando exatamente esta estrutura em Markdown:

### 🎯 Veredito do Diagnóstico
Diga claramente se o estudante **ACERTOU**, **ACERTOU PARCIALMENTE** ou **ERROU**, e apresente o **Gabarito Oficial** do caso.

### ⭐ Nota da Anamnese: X.X / 10
Atribua uma nota justa de 0 a 10 considerando as perguntas feitas durante a entrevista, a precisão do diagnóstico e a conduta proposta.

### ✅ Pontos Bem Investigados
Liste em tópicos o que o estudante perguntou bem durante a conversa.

### 🔍 O que Faltou Perguntar
Liste em tópicos as perguntas importantes do gabarito que o estudante deixou de investigar (como alergias, antecedentes, hábitos ou sinais de alarme).

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


# 6. Gerenciamento de Estado da Navegação
if "especialidade_ativa" not in st.session_state:
    st.session_state.especialidade_ativa = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "parecer_preceptor" not in st.session_state:
    st.session_state.parecer_preceptor = None


def iniciar_consulta(especialidade):
    st.session_state.especialidade_ativa = especialidade
    st.session_state.parecer_preceptor = None
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": CASOS_CLINICOS[especialidade]["primeira_fala"],
        }
    ]


# ==============================================================================
# TELA 1: SELEÇÃO DE ESPECIALIDADES (LOBBY INICIAL)
# ==============================================================================
if st.session_state.especialidade_ativa is None:
    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-badges">
                <span class="hero-badge">✨ SIMULADOR DE PACIENTE VIRTUAL</span>
                <span class="hero-badge">🩺 {len(CASOS_CLINICOS)} ESPECIALIDADES DISPONÍVEIS</span>
            </div>
            <div class="hero-title">🩺 AnamnesIA</div>
            <p class="hero-subtitle">
                Selecione abaixo a especialidade médica que você deseja treinar hoje para iniciar o atendimento com um paciente virtual.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_titulo, col_busca = st.columns([2, 1])
    with col_titulo:
        st.subheader("Escolha a especialidade para a anamnese:")
    with col_busca:
        busca = st.text_input(
            "Buscar especialidade",
            placeholder="🔍 Buscar especialidade ou cenário...",
            label_visibility="collapsed",
        )

    especialidades_filtradas = {
        nome: dados
        for nome, dados in CASOS_CLINICOS.items()
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
                        "Iniciar Atendimento ➔",
                        key=f"btn_{nome}",
                        type="primary",
                        use_container_width=True,
                    ):
                        iniciar_consulta(nome)
                        st.rerun()

# ==============================================================================
# TELA 2: CONSULTÓRIO VIRTUAL (CHAT + DIAGNÓSTICO FINAL VISÍVEL NA TELA)
# ==============================================================================
else:
    esp_atual = st.session_state.especialidade_ativa
    dados_caso = CASOS_CLINICOS[esp_atual]

    # Barra lateral opcional com roteiro rápido de estudo
    with st.sidebar:
        st.markdown("## 🩺 AnamnesIA")
        st.caption("Guia Rápido de Anamnese")
        st.markdown(
            """
            **Roteiro sugerido:**
            1. **Queixa Principal e HDA:** Início, duração, intensidade, irradiação, fatores de melhora/piora.
            2. **Antecedentes Pessoais:** Doenças crônicas, cirurgias, internações.
            3. **Medicações e Alergias:** Uso contínuo e alergias a remédios.
            4. **Hábitos e Família:** Tabagismo, etilismo, histórico familiar.
            """
        )

    # Botões de navegação no topo da tela principal (visíveis no PC e no celular)
    col_voltar, col_reiniciar = st.columns(2)
    with col_voltar:
        if st.button("⬅️ Trocar Especialidade", use_container_width=True):
            st.session_state.especialidade_ativa = None
            st.session_state.messages = []
            st.session_state.parecer_preceptor = None
            st.rerun()
    with col_reiniciar:
        if st.button("🔄 Reiniciar Consulta", use_container_width=True):
            iniciar_consulta(esp_atual)
            st.rerun()

    # Faixa superior da consulta ativa
    st.markdown(
        f"""
        <div class="hero-banner" style="padding: 1.3rem 1.8rem; margin-top: 0.5rem;">
            <div class="hero-badges">
                <span class="hero-badge">{dados_caso['icone']} {esp_atual.upper()}</span>
                <span class="hero-badge">📍 {dados_caso['cenario'].upper()}</span>
                <span class="hero-badge">🧑 PACIENTE: {dados_caso['paciente'].upper()}</span>
            </div>
            <div class="hero-title" style="font-size: 1.65rem;">Consultório Virtual — AnamnesIA</div>
            <p class="hero-subtitle">
                Converse com o paciente para investigar os sintomas. Quando estiver pronto, envie seu diagnóstico final logo abaixo do chat.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Exibe o Parecer do Preceptor no topo quando o estudante finaliza a consulta
    if st.session_state.parecer_preceptor:
        with st.container(border=True):
            st.success("✅ **Consulta Finalizada! Confira abaixo a avaliação do Preceptor Virtual:**")
            st.markdown(st.session_state.parecer_preceptor)
            if st.button("🩺 Treinar Outra Especialidade", type="primary", use_container_width=True):
                st.session_state.especialidade_ativa = None
                st.session_state.messages = []
                st.session_state.parecer_preceptor = None
                st.rerun()

    # Histórico da conversa
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Área de Diagnóstico Final diretamente na tela principal (acima do chat_input)
    st.markdown(
        """
        <div class="diag-callout">
            🎓 <strong>Já coletou informações suficientes?</strong> Abra a caixa abaixo para enviar seu diagnóstico final e receber a nota do Preceptor.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("🎓 ENVIAR DIAGNÓSTICO FINAL E CONDUTA (CLIQUE AQUI)", expanded=False):
        with st.form("form_diagnostico_principal"):
            hipotese = st.text_input(
                "1. Qual é a sua Hipótese Diagnóstica principal?",
                placeholder="Ex: Infarto Agudo do Miocárdio, Crise de Pânico, Apendicite Aguda...",
            )
            conduta = st.text_area(
                "2. Qual é a sua Conduta Inicial (exames, medicações ou encaminhamento)?",
                placeholder="Ex: Solicitar ECG em 10 min, monitorização, analgesia, exames laboratoriais...",
                height=85,
            )
            enviar_diag = st.form_submit_button(
                "✅ Finalizar Consulta e Ver Nota do Preceptor",
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
                            dados_caso,
                            st.session_state.messages,
                            hipotese,
                            conduta,
                        )
                        st.session_state.parecer_preceptor = resultado
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao gerar avaliação do Preceptor: {e}")

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
