import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import streamlit as st

# Configuração da página do Streamlit
st.set_page_config(
    page_title="AnamnesIA — Simulador Clínico",
    page_icon="🩺",
    layout="wide",
)

# Carrega e limpa a chave de API do arquivo .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")

if not api_key:
    st.error("⚠️ Chave de API do Gemini não encontrada! Configure o arquivo .env com a sua chave.")
    st.stop()

# Configura o cliente da API do Google GenAI
client = genai.Client(api_key=api_key)

# Prioriza o modelo mais rápido e estável da conta, mantendo fallback automático
MODELOS_FLASH = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
]

# Banco Completo de Especialidades, Casos Clínicos e Gabaritos (24 especialidades)
casos_especialidades = {
    "Cardiologia": {
        "icone": "❤️",
        "ambiente": "Pronto-Socorro",
        "descricao": "Investigação de dor torácica aguda, fatores de risco cardiovascular e sinais de alarme.",
        "primeira_fala": "Doutor(a)... por favor, me ajuda. Meu peito tá apertando muito e começou a puxar para o braço esquerdo...",
        "prompt_sistema": "Você é Carlos, 52 anos, motorista de aplicativo, em atendimento simulado. Você sente dor opressiva retroesternal há 2 horas, irradiando para o braço esquerdo, com sudorese fria e leve dispneia. Tem hipertensão e fuma 1 maço/dia. REGRAS: Responda apenas como o paciente Carlos, de forma curta, natural e ansiosa. Não dê diagnósticos. Só revele hipertensão e tabagismo se o estudante perguntar.",
        "gabarito": "Diagnóstico: Síndrome Coronariana Aguda / Infarto Agudo do Miocárdio (IAM). Pontos-chave da anamnese: caracterizar dor opressiva com irradiação para MSE e sudorese, investigar hipertensão e tabagismo. Conduta inicial: ECG de 12 derivações em até 10 minutos, dosagem de troponina, monitorização cardíaca, oxigênio se SpO2 < 90% e AAS.",
    },
    "Saúde Mental (Psiquiatria)": {
        "icone": "🧠",
        "ambiente": "Urgência / Acolhimento",
        "descricao": "Escuta ativa, acolhimento emocional e diferenciação entre sintomas físicos e ansiosos.",
        "primeira_fala": "Doutor(a), eu não consigo respirar direito, meu coração tá disparado e parece que eu vou morrer!",
        "prompt_sistema": "Você é Mariana, 28 anos, analista financeira, em atendimento simulado. Está com taquicardia, falta de ar, parestesia nas mãos e medo de morrer após uma semana exaustiva no trabalho. Não usa drogas nem tem cardiopatia. REGRAS: Responda apenas como Mariana, assustada e com frases curtas. Não dê diagnósticos. Só mencione a sobrecarga no trabalho se o estudante perguntar sobre gatilhos ou rotina.",
        "gabarito": "Diagnóstico: Ataque de Pânico / Crise de Ansiedade Aguda. Pontos-chave da anamnese: acolher a paciente, investigar gatilhos psicossociais (estresse no trabalho), uso de estimulantes/drogas e excluir causas orgânicas/cardíacas. Conduta inicial: acolhimento verbal, técnica de respiração guiada, sinais vitais e ECG para descartar arritmia se necessário.",
    },
    "Pediatria": {
        "icone": "🧸",
        "ambiente": "Consultório Pediátrico",
        "descricao": "Anamnese indireta com acompanhante, investigação de febre e sintomas na infância.",
        "primeira_fala": "Olá doutor(a), trouxe o meu filho Lucas porque ele não dormiu nada essa noite, tá com febre alta e chorando muito...",
        "prompt_sistema": "Você é Juliana, 31 anos, mãe do Lucas (4 anos), em consulta pediátrica simulada. Lucas tem febre de 38,8°C há 2 dias, irritabilidade, leva a mão à orelha direita e teve resfriado na semana passada. Vacinação em dia, sem alergias. REGRAS: Responda apenas como a mãe Juliana, preocupada e natural. Não dê diagnósticos. Só revele que ele puxa a orelha direita ou o resfriado prévio se o estudante perguntar.",
        "gabarito": "Diagnóstico: Otite Média Aguda (OMA) à direita. Pontos-chave da anamnese: duração/temperatura da febre, sinal localizatório (levar mão à orelha direita), infecção de vias aéreas superiores (resfriado) prévia, estado vacinal e alergias medicamentosas. Conduta inicial: otoscopia bilateral, antitérmico/analgesia (dipirona ou paracetamol) e avaliar antibioticoterapia (amoxicilina).",
    },
    "Gastroenterologia": {
        "icone": "🩺",
        "ambiente": "Ambulatório",
        "descricao": "Avaliação de dor abdominal, hábitos alimentares e uso de medicações gastrolesivas.",
        "primeira_fala": "Bom dia, doutor(a). Vim consultar porque estou com uma queimação forte na boca do estômago que não melhora...",
        "prompt_sistema": "Você é Roberto, 41 anos, representante comercial, em consulta simulada. Tem dor epigástrica em queimação há 3 semanas, que piora em jejum e alivia ao comer. Toma ibuprofeno quase diariamente por dor lombar. Nega melena ou vômitos com sangue. REGRAS: Responda apenas como Roberto, de forma natural. Não dê diagnósticos. Só mencione o uso frequente de ibuprofeno se o estudante perguntar sobre medicamentos.",
        "gabarito": "Diagnóstico: Doença Ulcerosa Péptica (Úlcera Duodenal/Gástrica) ou Gastrite erosiva induzida por AINE. Pontos-chave da anamnese: relação da dor com alimentação (piora em jejum/alivia ao comer), uso crônico de anti-inflamatório (ibuprofeno) e pesquisa de sinais de alarme (melena, hematêmese, perda de peso). Conduta inicial: suspender ibuprofeno, iniciar inibidor de bomba de prótons (omeprazol) e solicitar Endoscopia Digestiva Alta.",
    },
    "Pneumologia": {
        "icone": "🫁",
        "ambiente": "Pronto-Atendimento",
        "descricao": "Investigação de dispneia, sibilância, gatilhos ambientais e histórico respiratório.",
        "primeira_fala": "Doutor(a)... *cof, cof*... meu peito tá chiando muito desde ontem à noite e tá difícil puxar o ar...",
        "prompt_sistema": "Você é Fernanda, 34 anos, professora, em atendimento simulado. Tem tosse seca, chiado no peito e dispneia desde que limpou um depósito empoeirado ontem. Teve asma na infância e sua mãe também é asmática. Sem febre. REGRAS: Responda apenas como Fernanda, com frases curtas pelo cansaço. Não dê diagnósticos. Só revele o contato com poeira e o histórico familiar se o estudante investigar.",
        "gabarito": "Diagnóstico: Crise Aguda de Asma (exacerbação desencadeada por alérgeno). Pontos-chave da anamnese: identificar exposição a gatilho ambiental (poeira), histórico pessoal de asma/bronquite na infância, histórico familiar de atopia e ausência de febre. Conduta inicial: oximetria de pulso, broncodilatador inalatório de curta ação (salbutamol) e corticoide sistêmico.",
    },
    "Endocrinologia": {
        "icone": "⚡",
        "ambiente": "Ambulatório",
        "descricao": "Rastreamento metabólico, sintomas sistêmicos e antecedentes familiares.",
        "primeira_fala": "Olá doutor(a). Marquei consulta porque ando sentindo um cansaço absurdo e uma sede que não passa por nada...",
        "prompt_sistema": "Você é Sônia, 47 anos, costureira, em consulta simulada. Há 2 meses apresenta polidipsia intensa, poliúria noturna, fadiga e perda de 4 kg sem dieta. Seu pai tem diabetes tipo 2. REGRAS: Responda apenas como Sônia, de forma acolhedora e natural. Não dê diagnósticos. Só revele poliúria, perda de peso ou o histórico paterno se o estudante perguntar.",
        "gabarito": "Diagnóstico: Diabetes Mellitus tipo 2 (descompensado). Pontos-chave da anamnese: identificar a tríade clássica (polidipsia, poliúria e perda ponderal inexplicada) e antecedente familiar de diabetes. Conduta inicial: solicitar glicemia de jejum, hemoglobina glicada (HbA1c), perfil lipídico, função renal e orientar mudanças no estilo de vida.",
    },
    "Nefrologia": {
        "icone": "💧",
        "ambiente": "Enfermaria / Ambulatório",
        "descricao": "Avaliação de função renal, alterações urinárias, edema e uso de nefrotóxicos.",
        "primeira_fala": "Doutor(a), notei que minhas pernas e meus olhos amanheceram muito inchados nos últimos dias, e quase não estou urinando...",
        "prompt_sistema": "Você é Antônio, 63 anos, aposentado, em atendimento simulado. Apresenta edema periorbitário e de membros inferiores há 4 dias, redução do volume urinário (oligúria) e urina espumosa. É hipertenso, diabético e fez exame com contraste iodado há 5 dias. REGRAS: Responda apenas como Antônio, de forma natural. Não dê diagnósticos. Só mencione o exame com contraste ou o diabetes se o estudante perguntar.",
        "gabarito": "Diagnóstico: Lesão Renal Aguda (LRA) nefrotóxica induzida por contraste iodado (sobreposta a fator de risco diabético/hipertensivo). Pontos-chave da anamnese: quantificar oligúria, caracterizar edema e espuma na urina, investigar exposição recente a nefrotóxicos (contraste) e comorbidades (DM/HAS). Conduta inicial: solicitar creatinina, ureia, eletrólitos, gasometria, EAS e ajustar medicações nefrotóxicas.",
    },
    "Oftalmologia": {
        "icone": "👁️",
        "ambiente": "Urgência Oftalmológica",
        "descricao": "Diferenciação de olho vermelho agudo, dor ocular, fotofobia e hábitos de risco.",
        "primeira_fala": "Ai, doutor(a), a luz tá doendo demais no meu olho direito! Ele tá muito vermelho, lacrimejando e a visão ficou embaçada...",
        "prompt_sistema": "Você é Camila, 29 anos, designer, em atendimento simulado. Tem dor ocular intensa no olho direito, fotofobia, hiperemia e borramento visual desde hoje cedo. Usa lentes de contato gelatinosas e dormiu com elas ontem após entrar na piscina. REGRAS: Responda apenas como Camila, incomodada com a claridade. Não dê diagnósticos. Só conte sobre as lentes de contato e a piscina se o estudante perguntar.",
        "gabarito": "Diagnóstico: Ceratite Infecciosa / Úlcera de Córnea associada ao uso inadequado de lentes de contato (risco de Pseudomonas ou Acanthamoeba). Pontos-chave da anamnese: diferenciar olho vermelho grave (dor intensa, fotofobia, baixa visual) e descobrir o uso noturno de lentes de contato após piscina. Conduta inicial: suspender lentes imediatamente, encaminhamento de urgência ao oftalmologista para lâmpada de fenda e não prescrever colírio de corticoide.",
    },
    "Otorrinolaringologia": {
        "icone": "👂",
        "ambiente": "Consultório ORL",
        "descricao": "Caracterização de tontura vs vertigem, fatores desencadeantes e sintomas auditivos.",
        "primeira_fala": "Doutor(a), parece que o quarto inteiro gira quando eu viro a cabeça na cama, chega a me dar enjoo...",
        "prompt_sistema": "Você é Henrique, 38 anos, engenheiro, em atendimento simulado. Sente episódios breves (menos de 1 minuto) de vertigem rotatória intensa ao deitar ou virar na cama há 3 dias, com náuseas, mas sem zumbido, sem perda auditiva e sem cefaleia. REGRAS: Responda apenas como Henrique, objetivo e natural. Não dê diagnósticos. Só detalhe a duração das crises ou ausência de zumbido se o estudante perguntar.",
        "gabarito": "Diagnóstico: Vertigem Posicional Paroxística Benigna (VPPB). Pontos-chave da anamnese: confirmar caráter rotatório, duração curta (< 1 minuto), gatilho posicional (virar na cama) e ausência de sintomas cocleares (zumbido/hipoacusia) ou neurológicos. Conduta inicial: realizar manobra diagnóstica de Dix-Hallpike e manobra terapêutica de reposicionamento de Epley.",
    },
    "Dermatologia": {
        "icone": "🧴",
        "ambiente": "Ambulatório / Pronto-Atendimento",
        "descricao": "Investigação de lesões cutâneas, prurido, cronologia e exposição medicamentosa.",
        "primeira_fala": "Doutor(a), meu corpo inteiro ficou cheio de manchas vermelhas que coçam muito desde ontem, e também tive um pouco de febre...",
        "prompt_sistema": "Você é Beatriz, 25 anos, estudante de arquitetura, em atendimento simulado. Apresenta exantema maculopapular pruriginoso difuso no tronco e braços há 24h e febre de 38°C. Começou a tomar carbamazepina há 2 semanas para neuralgia. Nega falta de ar ou inchaço nos lábios. REGRAS: Responda apenas como Beatriz, preocupada. Não dê diagnósticos. Só revele o início da carbamazepina se o estudante perguntar sobre medicamentos recentes.",
        "gabarito": "Diagnóstico: Farmacodermia / Reação Exantemática Medicamentosa induzida por carbamazepina (atenção para síndrome DRESS). Pontos-chave da anamnese: investigar início de novos fármacos nas últimas semanas (carbamazepina) e excluir sinais de gravidade (edema facial, acometimento de mucosas, dispneia). Conduta inicial: suspender imediatamente a carbamazepina, solicitar hemograma, função hepática e renal e prescrever sintomáticos.",
    },
    "Cirurgia Geral": {
        "icone": "🔪",
        "ambiente": "Pronto-Socorro Cirúrgico",
        "descricao": "Avaliação de abdome agudo, migração da dor e sinais de irritação peritoneal.",
        "primeira_fala": "Doutor(a), tô com uma dor na barriga desde ontem à noite que não passa e agora parece que firmou aqui embaixo do lado direito...",
        "prompt_sistema": "Você é Rafael, 24 anos, técnico de informática, em atendimento simulado. Começou com dor difusa ao redor do umbigo há 18 horas, perda de apetite e náuseas; nas últimas 6 horas a dor migrou para a fossa ilíaca direita e piora ao andar ou tossir. Febre de 37,9°C. REGRAS: Responda apenas como Rafael, com expressão de dor. Não dê diagnósticos. Só revele a migração da dor e a anorexia se o estudante fizer perguntas direcionadas.",
        "gabarito": "Diagnóstico: Apendicite Aguda (Abdome Agudo Inflamatório). Pontos-chave da anamnese: identificar a cronologia clássica (dor periumbilical inicial migrando para fossa ilíaca direita), anorexia, náuseas e febre baixa. Conduta inicial: exame físico abdominal (pesquisa de sinal de Blumberg), jejum, hidratação venosa, hemograma, PCR, ultrassonografia/TC de abdome e avaliação cirúrgica.",
    },
    "Ginecologia": {
        "icone": "🌸",
        "ambiente": "Consultório Ginecológico",
        "descricao": "Anamnese ginecológica, ciclo menstrual, dor pélvica crônica e impacto funcional.",
        "primeira_fala": "Bom dia, doutor(a). Vim porque minhas cólicas menstruais estão cada vez piores, a ponto de eu faltar no trabalho todo mês...",
        "prompt_sistema": "Você é Patrícia, 32 anos, advogada, em consulta ginecológica simulada. Tem dismenorreia progressiva nos últimos 2 anos, dor durante a relação sexual (dispareunia profunda) e dificuldade para engravidar há 1 ano e meio. Ciclos regulares de 28 dias. REGRAS: Responda apenas como Patrícia, natural e reservada. Não dê diagnósticos. Só mencione dispareunia ou tentativa de gravidez se o estudante perguntar com tato.",
        "gabarito": "Diagnóstico: Endometriose Pélvica. Pontos-chave da anamnese: investigar dismenorreia secundária progressiva, dispareunia de profundidade e infertilidade conjugal. Conduta inicial: exame físico ginecológico e solicitar ultrassonografia transvaginal com preparo intestinal ou ressonância magnética de pelve.",
    },
    "Obstetrícia": {
        "icone": "🤰",
        "ambiente": "Maternidade / Triagem Obstétrica",
        "descricao": "Avaliação pré-natal de urgência, idade gestacional e sinais de gravidade materna.",
        "primeira_fala": "Doutor(a), estou grávida de 8 meses e vim porque acordei com uma dor de cabeça muito forte na nuca e uns pontinhos brilhando na vista...",
        "prompt_sistema": "Você é Larissa, 27 anos, primigesta com 34 semanas de gestação, em triagem obstétrica simulada. Apresenta cefaleia occipital intensa há 4 horas, escotomas cintilantes e dor na boca do estômago (epigastralgia). Sua pressão subiu nas últimas consultas do pré-natal e o bebê está mexendo normalmente. REGRAS: Responda apenas como Larissa, preocupada com o bebê. Não dê diagnósticos. Só revele epigastralgia ou pressão alta no pré-natal se o estudante investigar.",
        "gabarito": "Diagnóstico: Pré-eclâmpsia com Sinais de Gravidade (Iminência de Eclâmpsia). Pontos-chave da anamnese: identificar idade gestacional (34 semanas), sinais premonitórios (cefaleia occipital, escotomas, epigastralgia), hipertensão no pré-natal e movimentação fetal. Conduta inicial: aferir pressão arterial imediatamente, internação hospitalar, sulfato de magnésio, exames laboratoriais (HELLP) e avaliação fetal.",
    },
    "Ortopedia": {
        "icone": "🦴",
        "ambiente": "Ambulatório / Pronto-Atendimento",
        "descricao": "Investigação osteomuscular, irradiação radicular e bandeiras vermelhas na coluna.",
        "primeira_fala": "Doutor(a), travei das costas depois de levantar uma caixa pesada e agora desce uma dor tipo choque pela minha perna direita...",
        "prompt_sistema": "Você é Marcos, 45 anos, estoquista, em atendimento simulado. Tem lombalgia intensa há 3 dias após esforço físico, irradiando pela face posterior da coxa e perna direita até o pé, com formigamento. Nega perda de força, febre ou alteração para urinar/evacuar. REGRAS: Responda apenas como Marcos, desconfortável para sentar. Não dê diagnósticos. Só detalhe a irradiação ou ausência de alterações urinárias se o estudante perguntar.",
        "gabarito": "Diagnóstico: Lombociatalgia Aguda / Radiculopatia Lombar (Hérnia de Disco) sem sinais de alarme. Pontos-chave da anamnese: caracterizar irradiação radicular abaixo do joelho com parestesia após sobrecarga e excluir bandeiras vermelhas (síndrome da cauda equina, déficit motor grave, febre). Conduta inicial: teste de Lasègue, analgesia/AINE, orientar retorno gradual às atividades sem repouso absoluto.",
    },
    "Anestesiologia": {
        "icone": "💉",
        "ambiente": "Avaliação Pré-Anestésica",
        "descricao": "Rastreamento de via aérea, jejum, alergias, comorbidades e medicações de risco.",
        "primeira_fala": "Olá doutor(a), vim passar na consulta pré-anestésica porque vou operar a vesícula na semana que vem...",
        "prompt_sistema": "Você é Cláudia, 56 anos, comerciante, em consulta pré-anestésica simulada para colecistectomia videolaparoscópica. Tem hipertensão, ronca muito à noite e acorda cansada (apneia do sono não tratada), toma AAS infantil diariamente e tem alergia grave a dipirona (edema de glote no passado). REGRAS: Responda apenas como Cláudia, colaborativa. Não dê diagnósticos. Só revele o ronco, o uso de AAS ou a alergia a dipirona conforme o estudante perguntar.",
        "gabarito": "Diagnóstico: Avaliação Pré-Anestésica ASA II com risco de Apneia Obstrutiva do Sono (SAOS), uso de antiagregante (AAS) e alergia grave (anafilaxia) à dipirona. Pontos-chave da anamnese: rastrear alergias graves, medicações em uso, comorbidades e sinais de SAOS (ronco/sonolência). Conduta inicial: registrar alergia à dipirona em destaque, orientar manejo do AAS e jejum pré-operatório e avaliar via aérea (Mallampati).",
    },
    "Neurologia": {
        "icone": "🧬",
        "ambiente": "Ambulatório de Neurologia",
        "descricao": "Caracterização de cefaleias, sintomas visuais transitórios e sinais focais.",
        "primeira_fala": "Doutor(a), tenho crises de dor de cabeça forte de um lado só que sempre começam com uns zigue-zagues brilhantes na visão...",
        "prompt_sistema": "Você é Renata, 36 anos, jornalista, em consulta neurológica simulada. Tem crises recorrentes há anos de cefaleia hemicraniana pulsátil, forte, com náusea, fotofobia e fonofobia, precedidas por escotomas visuais em zigue-zague que duram 20 minutos. Piora com estresse e privação de sono. REGRAS: Responda apenas como Renata, clara e natural. Não dê diagnósticos. Só detalhe duração da aura ou sintomas associados se o estudante perguntar.",
        "gabarito": "Diagnóstico: Migrânea (Enxaqueca) com Aura Visual. Pontos-chave da anamnese: caracterizar aura visual reversível (20 min), dor hemicraniana pulsátil, sintomas associados (náusea, fotofobia, fonofobia), cronicidade e gatilhos. Conduta inicial: tratamento abortivo da crise (AINE/triptano + antiemético), diário da cefaleia e evitar gatilhos.",
    },
    "Infectologia": {
        "icone": "🦟",
        "ambiente": "Pronto-Atendimento",
        "descricao": "Investigação de síndrome febril aguda, epidemiologia e sinais de alarme.",
        "primeira_fala": "Doutor(a), tô há 4 dias com febre alta, dor no corpo inteiro e hoje comecei a sentir uma dor forte na barriga e tontura ao levantar...",
        "prompt_sistema": "Você é Tiago, 30 anos, educador físico, em atendimento simulado. Teve febre de 39°C, mialgia, cefaleia retro-orbitária e manchas vermelhas; hoje a febre baixou, mas surgiu dor abdominal contínua, vômitos persistentes e lipotimia ao ficar em pé. Houve surto de dengue no bairro. REGRAS: Responda apenas como Tiago, abatido. Não dê diagnósticos. Só revele vômitos persistentes ou dor retro-orbitária se o estudante investigar.",
        "gabarito": "Diagnóstico: Dengue com Sinais de Alarme (Grupo C). Pontos-chave da anamnese: identificar fase crítica (melhora da febre no 4º dia), epidemiologia e sinais de alarme (dor abdominal contínua, vômitos persistentes e hipotensão postural/lipotimia). Conduta inicial: hidratação venosa imediata (protocolo Grupo C), hemograma completo urgente (hematócrito e plaquetas), teste diagnóstico (NS1/sorologia) e observação hospitalar.",
    },
    "Reumatologia": {
        "icone": "🤲",
        "ambiente": "Ambulatório",
        "descricao": "Diferenciação de dor articular inflamatória vs mecânica e sintomas sistêmicos.",
        "primeira_fala": "Bom dia, doutor(a). Minhas mãos e meus punhos amanhecem tão duros e inchados que eu levo mais de uma hora para conseguir mexer direito...",
        "prompt_sistema": "Você é Helena, 39 anos, artesã, em consulta reumatológica simulada. Apresenta dor e edema simétrico em articulações metacarpofalangeanas, interfalangeanas proximais e punhos há 3 meses, com rigidez matinal que dura cerca de 1 hora e meia e melhora com o movimento. REGRAS: Responda apenas como Helena, natural. Não dê diagnósticos. Só detalhe a duração da rigidez matinal e a simetria se o estudante perguntar.",
        "gabarito": "Diagnóstico: Artrite Reumatoide (Poliartrite Simétrica Inflamatória Crônica). Pontos-chave da anamnese: identificar padrão inflamatório (rigidez matinal > 1 hora que melhora ao movimento), simetria, acometimento de pequenas articulações das mãos/punhos e duração > 6 semanas. Conduta inicial: solicitar Fator Reumatoide, Anti-CCP, VHS, PCR, radiografia de mãos/punhos e encaminhar ao reumatologista.",
    },
    "Urologia": {
        "icone": "🫘",
        "ambiente": "Pronto-Socorro",
        "descricao": "Avaliação de dor lombar aguda em cólica, irradiação e sintomas urinários.",
        "primeira_fala": "Doutor(a), pelo amor de Deus, me dá um remédio! É uma dor insuportável nas costas do lado esquerdo que vai descendo pra virilha...",
        "prompt_sistema": "Você é Jorge, 49 anos, motorista de ônibus, em atendimento simulado. Sente dor em cólica de início súbito na região lombar esquerda há 3 horas, irradiando para fossa ilíaca e testículo esquerdo, com náuseas e urina avermelhada. Bebe pouca água. Sem febre. REGRAS: Responda apenas como Jorge, inquieto de dor. Não dê diagnósticos. Só mencione urina avermelhada ou baixa ingestão hídrica se o estudante perguntar.",
        "gabarito": "Diagnóstico: Nefrolitíase / Cólica Nefrética (Cálculo Ureteral à esquerda) não complicada. Pontos-chave da anamnese: dor lombar em cólica súbita com irradiação típica para virilha/testículo, hematúria, baixa ingestão hídrica e ausência de febre (excluindo pielonefrite obstrutiva). Conduta inicial: analgesia potente (AINE/opioide), antiemético, EAS, creatinina e TC de abdome/pelve sem contraste.",
    },
    "Hematologia": {
        "icone": "🩸",
        "ambiente": "Ambulatório",
        "descricao": "Investigação de síndrome anêmica, fadiga crônica e fontes de perda sanguínea.",
        "primeira_fala": "Olá doutor(a), vim consultar porque ando muito fraca, com falta de ar até para subir um lance de escada e todo mundo diz que tô pálida...",
        "prompt_sistema": "Você é Aline, 23 anos, estudante universitária, em consulta simulada. Tem astenia progressiva, dispneia aos esforços, tontura e vontade estranha de mastigar gelo há 4 meses. Seu fluxo menstrual é muito intenso e dura 8 dias com coágulos. REGRAS: Responda apenas como Aline, calma e natural. Não dê diagnósticos. Só revele a hipermenorreia ou vontade de mastigar gelo se o estudante perguntar.",
        "gabarito": "Diagnóstico: Anemia Ferropriva secundária a Sangramento Uterino Anormal (Hipermenorreia). Pontos-chave da anamnese: reconhecer síndrome anêmica (astenia, dispneia aos esforços), pica/pagofagia (vontade de comer gelo) e investigar perdas sanguíneas ginecológicas. Conduta inicial: solicitar hemograma, reticulócitos, ferritina, ferro sérico e saturação de transferrina, iniciar reposição de ferro oral e avaliar causa ginecológica.",
    },
    "Geriatria": {
        "icone": "🧓",
        "ambiente": "Ambulatório de Geriatria",
        "descricao": "Avaliação multidimensional do idoso, polifarmácia, quedas e funcionalidade.",
        "primeira_fala": "Bom dia, doutor(a). Minha filha insistiu para eu vir porque levei dois tombos em casa esse mês quando levantei rápido da cadeira...",
        "prompt_sistema": "Você é Sr. Osvaldo, 78 anos, aposentado, em consulta geriátrica simulada. Teve 2 quedas recentes ao levantar rapidamente (tontura postural), sem perda de consciência. Toma 7 medicamentos diferentes por dia (incluindo dois anti-hipertensivos e clonazepam para dormir). REGRAS: Responda apenas como Sr. Osvaldo, simpático e pausado. Não dê diagnósticos. Só detalhe a lista de remédios e o uso de clonazepam se o estudante perguntar.",
        "gabarito": "Diagnóstico: Instabilidade Postural / Quedas no Idoso por Hipotensão Ortostática e Polifarmácia (Iatrogenia medicamentosa). Pontos-chave da anamnese: caracterizar quedas ao ortostatismo, excluir síncope e revisar toda a lista de medicamentos (anti-hipertensivos + benzodiazepínico/clonazepam). Conduta inicial: aferir pressão arterial deitado e em pé, desprescrever clonazepam gradualmente e ajustar anti-hipertensivos.",
    },
    "Oncologia": {
        "icone": "🎗️",
        "ambiente": "Ambulatório",
        "descricao": "Investigação de sinais de alarme digestivos, perda ponderal e hábitos de vida.",
        "primeira_fala": "Bom dia, doutor(a). Vim porque de uns meses pra cá parece que a comida entala no meio do peito quando eu engulo carne ou pão...",
        "prompt_sistema": "Você é Sérgio, 61 anos, pedreiro, em consulta simulada. Tem disfagia progressiva (começou para sólidos e agora até para pastosos) há 3 meses e perdeu 9 kg no período. Fuma cigarro de palha há 40 anos e consome destilados nos fins de semana. REGRAS: Responda apenas como Sérgio, simples e direto. Não dê diagnósticos. Só revele a perda de peso, o tabagismo ou o etilismo se o estudante perguntar.",
        "gabarito": "Diagnóstico: Neoplasia Maligna de Esôfago (Suspeita de Câncer de Esôfago). Pontos-chave da anamnese: identificar disfagia mecânica progressiva (sólidos para pastosos), perda ponderal acentuada (9 kg) e os dois maiores fatores de risco (tabagismo e etilismo crônicos). Conduta inicial: solicitar Endoscopia Digestiva Alta (EDA) com biópsia com prioridade e exames de estadiamento.",
    },
    "Medicina de Emergência": {
        "icone": "🚑",
        "ambiente": "Sala de Emergência",
        "descricao": "Reconhecimento rápido de reação sistêmica aguda, via aérea e exposição.",
        "primeira_fala": "Doutor(a), comi um salgado ali na esquina há 15 minutos e comecei a empolar todo, minha boca tá inchando e tô sentindo um aperto na garganta...",
        "prompt_sistema": "Você é Vitor, 35 anos, designer gráfico, em atendimento de emergência simulado. Apresenta urticária generalizada, angioedema labial e sensação de bolo/aperto na garganta 15 minutos após comer salgado que provavelmente continha camarão (tem alergia conhecida a frutos do mar). Voz levemente rouca. REGRAS: Responda apenas como Vitor, ansioso e com frases curtas. Não dê diagnósticos. Só confirme a alergia prévia a camarão se o estudante perguntar.",
        "gabarito": "Diagnóstico: Anafilaxia Aguda (desencadeada por alergia alimentar a camarão). Pontos-chave da anamnese: reconhecer início agudo (< 15 min) com acometimento cutâneo-mucoso (urticária/angioedema) e comprometimento de via aérea (rouquidão/aperto na garganta) após exposição alergênica. Conduta inicial: administrar Adrenalina (Epinefrina) intramuscular imediatamente na face anterolateral da coxa, oxigênio suplementar, acesso venoso e monitorização.",
    },
    "Clínica Médica": {
        "icone": "🏥",
        "ambiente": "Consultório Geral",
        "descricao": "Investigação de queixas inespecíficas, metabolismo basal e sintomas sistêmicos.",
        "primeira_fala": "Olá doutor(a). Vim fazer um check-up porque ando com um desânimo fora do normal, engordei mesmo comendo pouco e sinto muito frio...",
        "prompt_sistema": "Você é Lúcia, 50 anos, bibliotecária, em consulta clínica simulada. Há 6 meses apresenta fadiga, ganho de 5 kg, intolerância ao frio, constipação intestinal, pele seca e queda de cabelo. Sua irmã tem problema na tireoide. REGRAS: Responda apenas como Lúcia, tranquila e detalhista quando perguntada. Não dê diagnósticos. Só mencione constipação ou o histórico da irmã se o estudante investigar.",
        "gabarito": "Diagnóstico: Hipotireoidismo Primário. Pontos-chave da anamnese: reunir sintomas clássicos de hipometabolismo (fadiga, ganho ponderal, intolerância ao frio, constipação, pele seca, queda capilar) e antecedente familiar de tireoidopatia. Conduta inicial: solicitar dosagem sérica de TSH e T4 livre (e anti-TPO se confirmado).",
    },
}

# Inicializa estados da sessão
if "especialidade_ativa" not in st.session_state:
    st.session_state.especialidade_ativa = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "avaliacao_final" not in st.session_state:
    st.session_state.avaliacao_final = None

# Estilos globais
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .anamnese-banner {
            background: linear-gradient(135deg, #0B3954 0%, #087E8B 55%, #0D9488 100%);
            padding: 1.75rem 2rem;
            border-radius: 16px;
            color: #FFFFFF;
            box-shadow: 0 8px 24px rgba(8, 126, 139, 0.22);
            margin-bottom: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.14);
        }
        .anamnese-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
        }
        .badge-pill {
            background: rgba(255, 255, 255, 0.16);
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            color: #FFFFFF;
            border: 1px solid rgba(255, 255, 255, 0.25);
        }
        .anamnese-title {
            font-size: 2.15rem;
            font-weight: 800;
            margin: 0;
            line-height: 1.15;
            letter-spacing: -0.02em;
            color: #FFFFFF;
        }
        .anamnese-subtitle {
            font-size: 1rem;
            margin: 0.5rem 0 0 0;
            color: rgba(255, 255, 255, 0.92);
            max-width: 720px;
            line-height: 1.45;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def chamar_gemini(contents, instrucao_sistema, temperatura=0.7):
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


# ==============================================================================
# TELA 1: SELEÇÃO INICIAL DE ESPECIALIDADE
# ==============================================================================
if st.session_state.especialidade_ativa is None:
    st.markdown(
        f"""
        <div class="anamnese-banner">
            <div class="anamnese-badges">
                <span class="badge-pill">✨ SIMULADOR DE PACIENTE VIRTUAL</span>
                <span class="badge-pill">🎓 {len(casos_especialidades)} ESPECIALIDADES DISPONÍVEIS</span>
            </div>
            <h1 class="anamnese-title">🩺 AnamnesIA</h1>
            <p class="anamnese-subtitle">
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
        termo_busca = st.text_input(
            "Filtrar especialidade",
            placeholder="🔍 Buscar especialidade ou cenário...",
            label_visibility="collapsed",
        ).strip().lower()

    lista_especialidades = [
        esp
        for esp, info in casos_especialidades.items()
        if not termo_busca
        or termo_busca in esp.lower()
        or termo_busca in info["ambiente"].lower()
        or termo_busca in info["descricao"].lower()
    ]

    if not lista_especialidades:
        st.info("Nenhuma especialidade encontrada com esse termo. Tente limpar a busca.")
    else:
        for i in range(0, len(lista_especialidades), 3):
            cols = st.columns(3)
            for j, esp in enumerate(lista_especialidades[i : i + 3]):
                info = casos_especialidades[esp]
                with cols[j]:
                    with st.container(border=True):
                        st.markdown(f"### {info['icone']} {esp}")
                        st.caption(f"📍 **Cenário:** {info['ambiente']}")
                        st.write(info["descricao"])
                        if st.button(
                            "Iniciar Atendimento ➔",
                            key=f"btn_{esp}",
                            type="primary",
                            use_container_width=True,
                        ):
                            st.session_state.especialidade_ativa = esp
                            st.session_state.messages = [{
                                "role": "assistant",
                                "content": info["primeira_fala"],
                            }]
                            st.session_state.avaliacao_final = None
                            st.rerun()

# ==============================================================================
# TELA 2: CONSULTÓRIO / CHAT DE ANAMNESE + AVALIAÇÃO DO PRECEPTOR
# ==============================================================================
else:
    esp_atual = st.session_state.especialidade_ativa
    dados_caso = casos_especialidades[esp_atual]

    # Barra lateral da consulta e formulário de encerramento
    with st.sidebar:
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #0B3954 0%, #0D9488 100%);
                padding: 1rem 1.1rem;
                border-radius: 12px;
                color: white;
                margin-bottom: 1rem;
            ">
                <div style="font-size: 1.25rem; font-weight: 700;">🩺 AnamnesIA</div>
                <div style="font-size: 0.82rem; opacity: 0.9;">Treinamento clínico seguro com IA</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(f"**Especialidade:** {dados_caso['icone']} {esp_atual}")
        st.markdown(f"**Cenário:** {dados_caso['ambiente']}")
        st.divider()

        # Formulário de Avaliação Final pelo Preceptor IA
        st.subheader("🎓 Encerrar e Avaliar")
        with st.form("form_avaliacao_final"):
            hipotese_aluno = st.text_input(
                "Qual a sua Hipótese Diagnóstica?",
                placeholder="Ex: Infarto Agudo do Miocárdio",
            )
            conduta_aluno = st.text_area(
                "Qual a sua Conduta / Exames iniciais?",
                placeholder="Ex: Solicitar ECG, troponina, monitorizar...",
                height=90,
            )
            btn_avaliar = st.form_submit_button(
                "✅ Conferir Diagnóstico",
                type="primary",
                use_container_width=True,
            )

        if btn_avaliar:
            if not hipotese_aluno.strip():
                st.warning("Digite sua hipótese diagnóstica antes de encerrar.")
            else:
                with st.spinner("O Preceptor está corrigindo sua consulta..."):
                    transcricao = "\n".join(
                        f"{'Estudante' if m['role'] == 'user' else 'Paciente'}: {m['content']}"
                        for m in st.session_state.messages
                    )
                    prompt_preceptor = (
                        f"ESPECIALIDADE: {esp_atual}\n"
                        f"GABARITO OFICIAL DO CASO: {dados_caso['gabarito']}\n\n"
                        f"TRANSCRIÇÃO DA CONSULTA REALIZADA PELO ESTUDANTE:\n{transcricao}\n\n"
                        f"HIPÓTESE DIAGNÓSTICA DO ESTUDANTE: {hipotese_aluno}\n"
                        f"CONDUTA SUGERIDA PELO ESTUDANTE: {conduta_aluno or 'Não informada'}\n\n"
                        "Avalie o desempenho do estudante de forma clara, didática e encorajadora, seguindo exatamente estes tópicos:\n"
                        "1. **Veredito do Diagnóstico:** Diga claramente se acertou, acertou parcialmente ou errou, e revele o diagnóstico oficial.\n"
                        "2. **Nota da Anamnese (0 a 10):** Avalie a qualidade da investigação feita no chat.\n"
                        "3. **O que você investigou bem:** Perguntas certas feitas pelo estudante.\n"
                        "4. **O que faltou perguntar:** Pistas importantes do gabarito que o estudante não perguntou ao paciente.\n"
                        "5. **Feedback da Conduta:** Compare a conduta sugerida com o esperado."
                    )
                    instrucao_preceptor = (
                        "Você é um professor e preceptor médico experiente avaliando uma simulação clínica (OSCE). "
                        "Seja objetivo, construtivo e baseie sua correção estritamente no gabarito e na transcrição fornecidos."
                    )
                    try:
                        resultado = chamar_gemini(
                            prompt_preceptor,
                            instrucao_preceptor,
                            temperatura=0.3,
                        )
                        st.session_state.avaliacao_final = resultado
                    except Exception as e:
                        st.error(f"Erro ao gerar avaliação: {e}")

        st.divider()

        if st.button("🔄 Reiniciar Consulta", use_container_width=True):
            st.session_state.messages = [{
                "role": "assistant",
                "content": dados_caso["primeira_fala"],
            }]
            st.session_state.avaliacao_final = None
            st.rerun()

        if st.button("⬅️ Trocar Especialidade", use_container_width=True):
            st.session_state.especialidade_ativa = None
            st.session_state.messages = []
            st.session_state.avaliacao_final = None
            st.rerun()

    # Faixa superior dinâmica com a especialidade selecionada
    st.markdown(
        f"""
        <div class="anamnese-banner">
            <div class="anamnese-badges">
                <span class="badge-pill">{dados_caso['icone']} {esp_atual.upper()}</span>
                <span class="badge-pill">🏥 {dados_caso['ambiente']}</span>
            </div>
            <h1 class="anamnese-title">🩺 AnamnesIA</h1>
            <p class="anamnese-subtitle">
                Atendimento em andamento. Converse com o paciente e, ao terminar, preencha seu diagnóstico na barra lateral para receber a correção.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Exibe o boletim de avaliação do Preceptor caso o estudante já tenha encerrado
    if st.session_state.avaliacao_final:
        with st.container(border=True):
            st.subheader("📋 Parecer do Preceptor (Resultado da Consulta)")
            st.markdown(st.session_state.avaliacao_final)
            if st.button("Fechar Parecer e Continuar Conversando"):
                st.session_state.avaliacao_final = None
                st.rerun()

    # Exibe o histórico de mensagens na tela
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada do usuário (estudante de saúde)
    if prompt := st.chat_input("Digite sua pergunta de anamnese..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Monta o histórico a partir da primeira pergunta do aluno (role="user")
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
            f"Contexto: Você acabou de iniciar a consulta dizendo ao estudante: "
            f"\"{dados_caso['primeira_fala']}\""
        )

        with st.chat_message("assistant"):
            with st.spinner("O paciente está digitando..."):
                try:
                    resposta_ia = chamar_gemini(
                        contents, instrucao_completa, temperatura=0.7
                    )
                    st.markdown(resposta_ia)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": resposta_ia}
                    )
                except Exception as e:
                    st.error(f"Ocorreu um erro ao falar com a IA: {e}")