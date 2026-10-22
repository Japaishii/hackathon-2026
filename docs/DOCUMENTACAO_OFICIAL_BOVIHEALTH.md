# BoviHealth — Documentação Técnica Oficial

**Sistema especialista de apoio à triagem em bovinocultura leiteira**  
**Hackathon 2026 | Versão de documentação: outubro de 2026**

> **Aviso de segurança:** O BoviHealth é um protótipo de apoio à coleta de sinais e à priorização de atendimento. Não realiza diagnóstico definitivo, não prescreve medicamentos e não substitui a avaliação presencial de um médico-veterinário. Não há, nesta documentação, comprovação de validação clínica formal.

## 1. Resumo executivo

O **BoviHealth** é uma aplicação web para registrar sinais observados em bovinos leiteiros, executar uma avaliação por **regras determinísticas** e apresentar uma orientação inicial de prioridade com **trilha de inferência explicável**. O objetivo é auxiliar o responsável pelo animal a reconhecer situações que merecem atenção veterinária, organizar informações e registrar a evolução de cada triagem.

O sistema foi concebido como um **MVP de hackathon**. A saída é uma classificação de prioridade, e não a identificação confirmada de uma doença.

### 1.1. Problema

Em propriedades leiteiras, a identificação tardia de sinais relevantes pode atrasar o contato com o médico-veterinário. Também é comum que o responsável não consiga aferir todos os parâmetros necessários para descrever um caso. Um sistema de apoio deve, portanto, distinguir **sinal ausente** de **informação desconhecida**, evitando apresentar uma conclusão excessivamente segura.

### 1.2. Proposta de valor

- Questionário guiado para registrar sinais prioritários e contexto.
- Regras transparentes, com prioridades definidas na base de conhecimento.
- Exibição de fatos, regras acionadas, conclusão, orientações e fontes cadastradas.
- Registro de animais, histórico de triagens e acompanhamento posterior.
- Interface web responsiva, sem dependência de um modelo generativo para decidir a prioridade.

## 2. Escopo e público-alvo

**Público-alvo:** produtores, manejadores e estudantes que necessitam organizar informações para uma conversa com o médico-veterinário.  
**Escopo:** apoio à anamnese inicial e identificação de prioridades previstas na base de regras.  
**Fora do escopo:** diagnóstico diferencial completo, prescrição, indicação de dose, substituição de exame físico, monitoramento contínuo e atendimento de emergência autônomo.

## 3. Processo de desenvolvimento

1. **Definição do problema:** identificação de situações potencialmente urgentes na rotina da bovinocultura leiteira.
2. **Organização do conhecimento:** elaboração de perguntas e regras em arquivos JSON, com referências bibliográficas registradas.
3. **Implementação:** backend Python/FastAPI, persistência SQLite e interface HTML/CSS/JavaScript.
4. **Explicabilidade:** apresentação da sequência *fatos → regras → resultado*.
5. **Tratamento de incerteza:** respostas desconhecidas não são automaticamente convertidas em respostas negativas.
6. **Evolução do MVP:** histórico paginado, abertura de registros, exclusão com confirmação, acompanhamento editável e notificações de interface.
7. **Testes:** cenários automatizados e ensaios manuais; sua execução e seus resultados devem ser registrados antes da entrega final.

### 3.1. Uso de ferramentas de IA no desenvolvimento

**ChatGPT, Claude e Codex** foram utilizados como ferramentas de apoio ao desenvolvimento, revisão e organização do projeto. Essa participação deve ser descrita com transparência. **O mecanismo de classificação em execução é baseado em regras determinísticas**, não em geração livre de respostas por um modelo de linguagem. As sugestões das ferramentas devem ser revisadas pela equipe; o uso dessas ferramentas não equivale a validação veterinária.

## 4. Arquitetura

```text
Usuário / navegador
       |
       v
Interface web (templates/index.html; static/app.js; CSS)
       |
       | HTTP / JSON
       v
FastAPI (app/main.py) ------------------> SQLite (app/database.py)
       |
       v
Motor de inferência (app/specialist/engine.py)
       |
       +--> knowledge/questions.json
       +--> knowledge/rules.json
       |
       v
Prioridade + conclusões + orientações + regras acionadas
       |
       v
Resultado explicável, histórico e acompanhamento
```

### 4.1. Tecnologias

| Camada | Tecnologia | Responsabilidade |
|---|---|---|
| Backend | Python + FastAPI | API, validação e integração |
| Esquemas | Pydantic | Estrutura de entradas e saídas |
| Inferência | Python + regras JSON | Avaliação determinística |
| Persistência | SQLite | Animais, triagens e acompanhamentos |
| Frontend | HTML, CSS e JavaScript | Formulários, histórico e resultados |
| Testes | Pytest / HTTPX | Testes de lógica e API |

### 4.2. Organização principal

```text
app/
  main.py
  schemas.py
  database.py
  specialist/engine.py
knowledge/
  questions.json
  rules.json
static/
  app.js
  dashboard-final.css
  ...outros estilos do projeto
templates/
  index.html
tests/
  test_engine.py
  test_api.py
  ...outros testes do repositório
docs/
requirements.txt
```

A árvore representa os componentes principais; nomes de arquivos auxiliares devem ser conferidos na versão final do repositório.

## 5. Base de conhecimento e motor de inferência

O questionário e as regras ficam separados do código da interface. O motor recebe um conjunto de respostas, verifica condições lógicas e devolve uma avaliação. Para uma mesma versão das regras e as mesmas respostas, espera-se a mesma classificação.

### 5.1. Estados de entrada

| Valor | Interpretação |
|---|---|
| `true` | Sinal observado |
| `false` | Sinal investigado e não observado |
| `null` | Não informado / não foi possível verificar |
| `not_measured` | Parâmetro específico não aferido, quando previsto no questionário |

**Regra de segurança:** ausência de informação não é evidência de ausência do sinal.

### 5.2. Condições e prioridades

As regras podem utilizar conjuntos como `all`, `any`, `any_systemic` e comparações de valores. A base de conhecimento registra a hierarquia:

```text
immediate > veterinary_assessment > none
```

A prioridade mais alta acionada prevalece na apresentação do resultado. Quando os dados essenciais são insuficientes, o resultado pode indicar o status `insufficient`. A lógica exata depende da versão de `knowledge/rules.json` e do motor implantado.

### 5.3. Exemplos de sinais contemplados

- Dificuldade respiratória (`respiratory_distress`).
- Incapacidade de levantar (`unable_to_rise`).
- Distensão abdominal esquerda súbita (`sudden_left_abdominal_distension`).
- Alterações no leite (`abnormal_milk`).
- Inflamação do úbere (`udder_inflammation`).
- Febre, apetite, queda na produção de leite e tempo de início dos sinais.

Esses sinais **não comprovam, isoladamente, doenças específicas**. O nome e a condição exata de cada regra devem ser consultados no arquivo `knowledge/rules.json` da versão entregue.

### 5.4. Explicabilidade

A tela de resultado apresenta três etapas:

1. **Fatos:** respostas relevantes fornecidas pelo usuário.
2. **Regras:** condições acionadas, justificativas e fontes associadas.
3. **Resultado:** prioridade e orientações de encaminhamento.

Esse registro facilita auditoria técnica, apresentação à banca e revisão futura por especialistas.

## 6. Funcionalidades do MVP

### 6.1. Cadastro de animais

Permite registrar um identificador e dados de contexto produtivo disponíveis no formulário. O animal pode ser associado a triagens posteriores.

### 6.2. Triagem guiada

O usuário responde às perguntas, incluindo a opção de não saber ou não ter aferido um sinal. O sistema envia as respostas à API e apresenta a classificação com justificativas.

### 6.3. Histórico

O histórico lista avaliações anteriores, permite abrir um registro e navegar entre páginas. A exclusão individual exige confirmação; ao excluir uma triagem, seu acompanhamento associado também é removido, sem excluir automaticamente o animal.

### 6.4. Acompanhamento

Cada triagem pode receber uma anotação de acompanhamento. O conteúdo pode ser consultado e editado no resultado, e registros com acompanhamento são identificados no histórico. **Acompanhamento não equivale a prontuário clínico validado.**

### 6.5. Relatórios e mensagens

A interface oferece opção de impressão ou salvamento em PDF pelo navegador. Notificações visuais informam operações concluídas e erros de comunicação; a apresentação amigável de um erro não corrige, por si só, uma eventual falha de servidor.

## 7. API — principais operações

| Método | Rota | Finalidade |
|---|---|---|
| `GET` | `/api/questions` | Obter questionário |
| `GET` | `/api/rules` | Obter regras e fontes cadastradas |
| `GET` | `/api/animals` | Listar animais |
| `POST` | `/api/animals` | Cadastrar animal |
| `POST` | `/api/assessments` | Criar triagem |
| `GET` | `/api/assessments/{id}` | Consultar triagem |
| `GET` | `/api/assessments/page?page=1&page_size=5` | Consultar histórico paginado na versão atual da interface |
| `PATCH` | `/api/assessments/{id}/follow-up` | Salvar ou editar acompanhamento |
| `DELETE` | `/api/assessments/{id}` | Excluir triagem |
| `GET` | `/api/assessments/{id}/report` | Consultar relatório, conforme implementação |

A documentação interativa da API fica em `/docs` quando o servidor está em execução. **Não utilizar `/api/evaluate` como rota principal**, pois a criação de triagens na implementação trabalhada usa `/api/assessments`.

## 8. Instalação e execução

### 8.1. Pré-requisitos

- Python compatível com `requirements.txt` (ambiente usado no desenvolvimento: Python 3.12).
- `pip` e terminal.

### 8.2. Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Se a ativação do ambiente virtual estiver bloqueada pela política local do PowerShell, é possível executar o Python do ambiente diretamente, sem alterar a política do computador:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Aplicação: `http://127.0.0.1:8000`  
Documentação da API: `http://127.0.0.1:8000/docs`

### 8.3. Testes automatizados

```powershell
python -m pytest -q
```

Registrar no relatório final a data, o comando, a quantidade de testes e o resultado real da execução. Não declarar aprovação de testes sem a saída correspondente.

## 9. Plano de demonstração para o hackathon

### 9.1. Cenário A — Sinais de emergência

**Objetivo:** demonstrar prioridade de atendimento e rastreabilidade.

1. Criar ou selecionar um animal de demonstração.
2. Informar dificuldade respiratória = **sim** e incapacidade de levantar = **sim**.
3. Informar os demais sinais conforme um roteiro de teste previamente definido.
4. Gerar a triagem e verificar se as regras de emergência pertinentes foram acionadas.
5. Mostrar fatos, justificativas, fontes e orientação de contato veterinário.
6. Salvar um acompanhamento fictício e reabrir o registro pelo histórico.

**Critério de aceitação:** a saída corresponde à prioridade esperada pela base de regras e mostra o motivo. Se houver divergência, investigar antes da apresentação.

### 9.2. Cenário B — Dados incompletos

**Objetivo:** demonstrar tratamento de incerteza.

1. Marcar como **não sei** os sinais prioritários que não puderam ser verificados.
2. Preencher apenas as informações realmente disponíveis.
3. Gerar a triagem.
4. Verificar se o sistema preserva as incógnitas e não as interpreta como respostas negativas.
5. Conferir se o resultado comunica insuficiência de dados quando aplicável.

**Critério de aceitação:** o resultado não transmite segurança injustificada diante de sinais essenciais desconhecidos.

### 9.3. Evidências recomendadas

Capturar telas do questionário, da trilha de inferência, da indicação de dados incompletos, do histórico paginado e do acompanhamento salvo. Usar **dados fictícios** na demonstração.

## 10. Segurança, limitações e validação clínica

### 10.1. Limitações atuais

- Dependência da precisão e completude das respostas fornecidas.
- Cobertura limitada aos sinais e regras cadastrados.
- Ausência de exame físico e de confirmação laboratorial.
- Possibilidade de regras incompletas, inconsistentes ou desatualizadas.
- Persistência local em SQLite; requisitos de autenticação, autorização, privacidade, backup e implantação precisam de avaliação própria antes de uso real.
- Falta de evidência documentada de desempenho clínico em população real.

### 10.2. Validação técnica versus validação clínica

**Testes técnicos** verificam se o software executa corretamente o comportamento programado. **Validação clínica** verifica se o comportamento é adequado e seguro para situações reais. Uma suíte de testes aprovada **não comprova** sensibilidade, especificidade, segurança clínica nem eficácia em propriedades leiteiras.

### 10.3. Plano proposto de validação clínica

1. Revisão da base de regras por médicos-veterinários com experiência em bovinocultura leiteira.
2. Definição de cenários padronizados e critérios de referência independentes.
3. Avaliação retrospectiva ou estudo supervisionado, com autorização e governança adequadas.
4. Medição de sensibilidade, especificidade, taxa de falsos negativos e concordância com especialistas, por categoria de prioridade.
5. Revisão de regras problemáticas, versionamento e nova avaliação antes de qualquer implantação real.

**Status:** proposta de validação futura; não declarar etapas como realizadas sem evidências.

## 11. Referências e rastreabilidade

O documento original identifica como bases bibliográficas a **Embrapa Gado de Leite** e o **Merck Veterinary Manual**, incluindo conteúdos sobre timpanismo, decúbito e mastite. As referências completas, URLs, títulos e associação entre fontes e regras devem ser conferidas no `knowledge/rules.json` e revisadas pela equipe antes da entrega.

A presença de uma referência em uma regra não significa que a regra foi validada clinicamente por essa instituição.

## 12. Perguntas frequentes da banca

**O BoviHealth diagnostica doenças?**  
Não. Ele classifica prioridades com base em regras e nas informações fornecidas, apoiando a triagem inicial.

**Por que utilizar regras em vez de IA generativa na inferência?**  
Para tornar a classificação reproduzível e rastreável: a equipe consegue identificar quais condições foram satisfeitas e quais regras contribuíram para a saída.

**O sistema foi validado clinicamente?**  
Não há validação clínica formal comprovada nesta documentação. A validação técnica do código e a validação clínica são etapas distintas.

**O que acontece quando faltam informações?**  
O sistema preserva respostas desconhecidas e pode indicar dados insuficientes, em vez de supor que o sinal não existe.

**Como foram usados ChatGPT, Claude e Codex?**  
Como apoio ao desenvolvimento e à documentação. A decisão de prioridade em tempo de execução é produzida pelo motor de regras.

## 13. Evolução futura

- Revisão veterinária especializada e estudo de validação clínica.
- Governança da base de conhecimento: autoria, revisão, versão e justificativa de alterações.
- Autenticação e controle de acesso para ambientes com múltiplos usuários.
- Estratégia de backup, proteção de dados e auditoria de alterações.
- Estudos de usabilidade com produtores e manejadores.
- Avaliação de operação em locais com conexão instável.

## 14. Conclusão

O BoviHealth demonstra a aplicação de um **sistema especialista baseado em regras** para apoiar a organização de informações e a priorização inicial de atendimento em bovinocultura leiteira. Seus principais diferenciais como MVP são a **explicabilidade da inferência**, o **tratamento explícito de dados desconhecidos** e a **continuidade do registro por meio de histórico e acompanhamento**.

O projeto está orientado à **demonstração técnica e à avaliação no hackathon**. Qualquer uso clínico real exige revisão especializada, validação apropriada e medidas adicionais de segurança e governança.
