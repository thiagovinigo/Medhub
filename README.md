# Projeto: Agente de IA para Análise de Imagens Médicas 🩺

Este projeto utiliza modelos de Inteligência Artificial (Gemini) integrados a um agente autônomo (via biblioteca `agno`) para analisar imagens médicas. A aplicação inclui uma interface web interativa construída com `Streamlit` e uma etapa de pesquisa automatizada (via `Tavily`) para buscar referências e literatura recente.

## 🚀 Como reconstruir o projeto na sua máquina

Siga os passos abaixo para rodar o projeto localmente:

### 1. Preencha as chaves de API
Abra o arquivo `.env` na raiz do projeto e insira suas chaves (sem aspas):
```env
GOOGLE_API_KEY=sua_chave_do_google_aqui
TAVILY_API_KEY=sua_chave_do_tavily_aqui
```
*Se você não tiver as chaves, você pode gerá-las no [Google AI Studio](https://aistudio.google.com/) e no [Tavily](https://tavily.com/).*

### 2. Crie e ative um Ambiente Virtual (Recomendado)
Para evitar conflito de versões de bibliotecas na sua máquina, utilize um ambiente virtual:
* **No Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```

### 3. Instale as dependências
Com o terminal aberto na pasta do projeto e o ambiente ativado, rode:
```bash
pip install -r requirements.txt
```

### 4. Execute a aplicação

A aplicação agora é dividida em Frontend (React/Vite) e Backend (FastAPI). Você precisará de dois terminais:

**Terminal 1 (Backend):**
```bash
cd backend
python -m uvicorn main:app --reload
```
O backend estará rodando em `http://localhost:8000`.

**Terminal 2 (Frontend):**
```bash
cd frontend
npm install
npm run dev
```
O frontend abrirá automaticamente ou estará disponível em `http://localhost:5173`.


## 💡 Como atualizar e aprimorar o projeto (Próximos Passos)

Caso você queira expandir e melhorar a aplicação, aqui estão as principais áreas de atuação:

1. **Geração de PDF do Diagnóstico:**
   - Adicionar uma biblioteca como o `FPDF` ou `WeasyPrint` para gerar um relatório em PDF consolidado com o layout da análise do Agente, permitindo o download pelo usuário através do próprio Streamlit.

2. **Histórico de Pacientes/Imagens:**
   - Implementar um banco de dados leve (como `SQLite`) para salvar as imagens já analisadas e manter o histórico, permitindo que o médico consulte análises anteriores (criando uma nova aba na interface).

3. **Inclusão de Laudos Textuais:**
   - Permitir que, além da imagem, o usuário faça o upload de um PDF com o laudo do laboratório ou anotações clínicas, para que a IA correlacione a imagem com o histórico textual do paciente, aumentando muito a precisão.

4. **Multi-Agentes Especialistas (Orquestração):**
   - Criar múltiplos agentes na biblioteca `agno` (ex: Agente Oncologista, Agente Ortopedista, etc.) e um "Agente Roteador" que analisa inicialmente a imagem e passa para o especialista mais adequado emitir o parecer final.

5. **Aperfeiçoamento dos Prompts (Prompt Engineering):**
   - No `app.py`, as variáveis `prompt_analysis` e `prompt_search_template` podem ser ainda mais calibradas para exigir citações diretas no formato ABNT ou de periódicos específicos (como *PubMed*).
