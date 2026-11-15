# 🩺 AnamnesIA

Simulador interativo de anamnese e raciocínio clínico com pacientes virtuais gerados por inteligência artificial em **24 especialidades médicas** e avaliação automatizada por um Preceptor Virtual.

## ✨ Funcionalidades

- **Catálogo com 24 Especialidades Médicas:** Tela inicial com busca instantânea abrangendo Cardiologia, Saúde Mental, Pediatria, Ginecologia, Obstetrícia, Cirurgia Geral, Medicina de Emergência, Ortopedia, Oftalmologia, Nefrologia, Endocrinologia, Pneumologia, Gastroenterologia, entre outras.
- **Pacientes Virtuais Realistas (Anti-Spoiler):** Cada caso possui queixa inicial, personalidade e histórico próprio. O paciente só revela informações decisivas (como tabagismo, alergias graves, uso de medicações ou histórico familiar) se o estudante fizer as perguntas certas.
- **Avaliação do Preceptor (IA):** Ao encerrar a consulta, o estudante preenche sua hipótese diagnóstica e conduta inicial na barra lateral. Uma segunda instância da IA compara toda a transcrição da conversa com o gabarito clínico do caso e entrega:
  - Veredito do diagnóstico e revelação do gabarito oficial;
  - Nota de **0 a 10** para a condução da anamnese;
  - Pontos bem investigados e perguntas importantes que ficaram de fora;
  - Feedback técnico sobre a conduta sugerida.

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python
- **Interface Web:** Streamlit + HTML/CSS customizado
- **Inteligência Artificial:** Google GenAI SDK (`google-genai`) com modelos Gemini Flash e fallback automático
- **Gerenciamento de Ambiente:** `python-dotenv`

## 🚀 Como executar localmente

1. **Clone este repositório:**
   ```bash
   git clone [https://github.com/SamariaGomes/anamnese-ia.git](https://github.com/SamariaGomes/anamnese-ia.git)
   cd anamnese-ia
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure sua chave de API:**
   Crie um arquivo chamado `.env` na raiz do projeto e adicione sua chave gratuita do [Google AI Studio](https://aistudio.google.com/):
   ```env
   GEMINI_API_KEY="sua_chave_aqui"
   ```

5. **Inicie o aplicativo:**
   ```bash
   streamlit run app.py
   ```

## 📁 Estrutura do Projeto

```text
anamnese-ia/
├── app.py              # Código principal (interface, 24 casos clínicos e Preceptor IA)
├── requirements.txt    # Dependências do projeto
├── .gitignore          # Proteção contra envio de arquivos sensíveis (.env e venv)
└── README.md           # Documentação do projeto
```