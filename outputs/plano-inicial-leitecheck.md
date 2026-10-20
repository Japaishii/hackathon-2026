# LeiteCheck — análise inicial e plano de execução

## 1. O que é um sistema especialista

Um sistema especialista representa conhecimento de um domínio em uma base explícita e aplica esse conhecimento a fatos fornecidos para chegar a conclusões. No LeiteCheck, as respostas da anamnese são fatos; a base versionada contém condições e conclusões revisadas; e o motor de inferência aplica as regras de forma reproduzível. A aplicação deve mostrar quais fatos e regras sustentaram cada resultado.

Um motor de inferência por encadeamento para frente parte dos fatos conhecidos, procura regras cujas condições estejam satisfeitas, dispara essas regras e registra conclusões derivadas. Dados ausentes não equivalem a respostas negativas: devem continuar desconhecidos, podendo levar a resultado inconclusivo ou pedido de informação. A precedência de segurança e a resolução de conflitos precisam ser definidas e documentadas.

A LLM pode apoiar a equipe na análise, planejamento, programação e revisão. Ela não pode tomar as decisões de triagem em execução. As decisões devem vir da base explícita e do motor determinístico.

## 2. Leitura dos documentos do evento

Foram lidos integralmente `Hackathon2026.pdf` (3 páginas) e `Apresentação Hackathon2026.pdf` (16 páginas). Os requisitos oficiais identificados são:

- Escolher um dos temas; o Tema 1 é anamnese de bovinos leiteiros em lactação, com coleta estruturada de sinais e histórico e triagem explicável.
- Criar uma aplicação para usuário final que resolva um problema da pecuária leiteira com base explícita de conhecimento e motor de inferência.
- Usar agente de codificação com IA no desenvolvimento e ferramentas/códigos open source disponíveis na web.
- Não usar a LLM como o sistema especialista; o motor deve ser determinístico e auditável.
- Demonstrar a solução funcionando e entregar documentação obrigatória do processo, arquitetura tecnológica e regras de produção, além de apresentação organizada do processo.
- A solução completa deve rodar em localhost.
- O evento descreve o resultado como prova de conceito e recomenda casos de teste conhecidos.
- Cronograma informado: início 20/10/2026 às 9h; encerramento até 22/10/2026 às 20h; apresentação 23/10/2026 às 9h.
- Grupos: apresentação informa de 1 a 3 participantes inscritos e presentes. O material textual também diz máximo de três.

Os documentos oficiais não exigem Python, FastAPI, SQLite, JSON, pytest, encadeamento para frente, cadastro de rebanho, relatórios PDF, operação sem internet, equipe de três ou quatro módulos. Esses itens aparecem como decisões/propostas no texto mestre colado, não como regras do evento. A versão revisada do texto colado escolhe FastAPI em vez de Flask; este plano respeita essa escolha como decisão da equipe.

## 3. Estado do espaço de trabalho

A pasta do projeto não contém código ou especificação prévia; há somente as pastas de trabalho e de saídas. Assim, não existe implementação existente a preservar nem arquivos da aplicação a integrar nesta primeira etapa. Este documento constitui a análise e o plano inicial; a implementação começa incrementalmente depois desta etapa.

## 4. Escopo proposto

### Núcleo mínimo para a prova de conceito

1. Anamnese curta e estruturada para vacas leiteiras em lactação, com opções explícitas para sim/não/desconhecido/não medido quando aplicável.
2. Base JSON de perguntas e regras versionada, com identificadores estáveis, condições, conclusão, prioridade, explicação e fonte/revisão pendente.
3. Motor Python determinístico e independente do FastAPI, com validação, encadeamento para frente, tratamento de ausência, política de prioridade e trilha de regras acionadas.
4. API FastAPI com modelos Pydantic; interface local leve servida pela própria aplicação, sem CDN.
5. Resultado com prioridade, razões observáveis, regras acionadas, limitações e orientação segura sem declarar diagnóstico confirmado.
6. Casos sintéticos reproduzíveis para resultado sem alerta, alerta definido por protocolo e informação insuficiente.
7. README de instalação/execução local e documentação do processo, arquitetura e regras; roteiro de demonstração.

### Opcionais, somente após estabilizar o núcleo

Cadastro de vários animais, histórico SQLite, filtros e painel; acompanhamento de providências; relatório imprimível/PDF; comparações e indicadores agregados. São funcionalidades propostas no texto mestre, não critérios oficiais explícitos. SQLite pode entrar cedo se o tempo permitir, mas não deve atrasar motor, explicabilidade, demonstração e documentação.

## 5. Matriz de rastreabilidade inicial

| Requisito | Origem | Módulo responsável | Implementação prevista | Verificação |
|---|---|---|---|---|
| Tema 1: anamnese de vacas em lactação | Oficial | Interface / schemas | Perguntas de sinais e histórico com dados básicos relevantes | Cenários de preenchimento e revisão do formulário |
| Base explícita de conhecimento | Oficial | `regras/` | JSON versionado, separado da interface e do motor | Carregamento, validação de estrutura e revisão de IDs/fontes |
| Motor de inferência | Oficial | `app/especialista/` | Regras determinísticas Python, inicialmente forward chaining | Testes unitários com fatos e resultado esperado |
| Resultado explicável e auditável | Oficial (apresentação) | Explicador / API / interface | Mostrar fatos considerados, regra acionada e justificativa | Casos conhecidos conferem trilha e explicação |
| Não usar LLM para decidir | Oficial | Limite arquitetural | Nenhuma chamada a LLM no fluxo de triagem | Inspeção de dependências/código e execução offline |
| Aplicação para usuário final | Oficial | FastAPI + interface | Formulário e tela de resultado simples | Demonstração do fluxo completo no navegador local |
| Funcionar por completo em localhost | Oficial | Aplicação / empacotamento | Uvicorn local e recursos locais, sem CDN | Inicialização e fluxo sem rede externa |
| Ferramentas/código open source | Oficial | Dependências | Dependências open source documentadas | Revisão de `requirements.txt` e licenças/dependências |
| Demonstração funcionando | Oficial | Produto / docs | Casos preparados e roteiro com contingência | Ensaio do roteiro em instalação limpa/local |
| Documentação de processo, arquitetura e regras | Oficial | `docs/`, README | Especificação, decisões e regras usadas | Conferência de completude contra o produto implementado |
| Apresentação organizada do processo | Oficial | Material de apresentação | Narrativa IA → conhecimento → motor → demonstração → limites | Revisão e ensaio pela equipe |
| Perguntas com dados ausentes explícitos | Proposta do texto mestre | Schema / motor / interface | Representar desconhecido sem convertê-lo em “não” | Teste de ausência versus negativo |
| Histórico do rebanho | Opcional proposto | Persistência | SQLite para animais e avaliações | Testes de persistência e consulta, se incluído |
| Stack FastAPI | Decisão posterior do texto mestre | API | `app/main.py`, Pydantic, Uvicorn | Testes de rota e inicialização local |

## 6. Arquitetura e contratos

```text
Navegador local (HTML/CSS/JS)
          │ HTTP localhost
          ▼
FastAPI (rotas + schemas Pydantic)
          │ avaliação validada
          ▼
Serviço de aplicação ─────────── Persistência SQLite (opcional no MVP)
          │ fatos normalizados
          ▼
Validador → Memória de trabalho → Motor determinístico
                                      │
                           Base JSON versionada
                                      │
                                      ▼
                           Traço + explicações
```

- **Interface:** envia respostas e exibe resultado; não calcula a triagem.
- **API (`app/main.py`, rotas e schemas):** valida contrato, coordena serviço e entrega respostas HTTP. Não contém regras clínicas.
- **Serviço de aplicação:** cria uma avaliação, invoca validação/motor e persiste entrada e saída quando houver banco.
- **Base JSON:** contém versão, perguntas/fatos, regras, fontes e status de revisão.
- **Motor:** entrada pura de fatos normalizados + base carregada; saída serializável de prioridade, conclusões, regras acionadas, fatos derivados e desconhecidos. Sem Flask/FastAPI, rede ou LLM.
- **Memória de trabalho:** isolada por avaliação; nunca mistura fatos do caso com a base ou histórico.
- **Explicador:** transforma o traço estruturado em justificativas legíveis, sem inventar fatos.
- **SQLite (opcional no MVP):** registra animais, avaliações, respostas, resultado e acompanhamento; não altera retrospectivamente a regra ou versão usada.

### Contrato conceitual de triagem

Entrada: `animal` (opcional no núcleo), `answers` (mapa de identificador de pergunta para valor tipado) e, futuramente, `evaluation_id`.

Saída: `knowledge_base_version`, `priority`, `status` (por exemplo, avaliado ou insuficiente), `conclusions[]`, `fired_rules[]`, `evidence[]`, `unknowns[]`, `guidance[]` e aviso de que triagem não confirma diagnóstico.

Semântica: condição verdadeira/falsa/desconhecida; valor não fornecido permanece desconhecido. Operadores iniciais limitados e documentados (AND/OR e comparações tipadas que forem realmente necessárias). Conflitos: prioridade de segurança precede classes de menor urgência; regras simultâneas são preservadas no traço; ambiguidades não resolvidas retornam revisão/insuficiência, não um diagnóstico arbitrário. Detalhar essa política antes de codificar as regras.

## 7. Regras clínicas: pesquisa e validação pendentes

Nenhuma regra clínica deve ser inventada com base apenas no prompt ou em inferência do agente. Antes de promover uma regra à base de produção, registrar fonte veterinária rastreável, trecho/critério operacional, população/contexto de aplicação, data de acesso e revisor competente. Buscar validação de médico-veterinário ou técnico com conhecimento de bovinos leiteiros. A documentação precisa diferenciar regra revisada de hipótese didática.

Para o MVP, priorizar coleta de histórico e sinais observáveis e definir poucos critérios de encaminhamento/alerta somente quando houver fonte e revisão. Se ainda não houver validação ao construir a demonstração, usar regras claramente rotuladas como exemplos sintéticos/de demonstração, sem alegação de eficácia clínica e sem apresentá-las como protocolo veterinário. O sistema não deve recomendar tratamento nem afirmar doença confirmada.

## 8. Divisão de trabalho sugerida (até três pessoas)

- **Pessoa A — Domínio e conhecimento:** levantar perguntas, localizar fontes veterinárias, registrar proveniência e organizar revisão das regras.
- **Pessoa B — Motor e qualidade:** implementar normalização, semântica de desconhecidos, inferência, explicação e testes unitários.
- **Pessoa C — Aplicação e entrega:** FastAPI, interface local, persistência se couber, documentação e roteiro de apresentação.

Decisões de regra, critérios de urgência e versão final da base devem ser revisados em conjunto. Se a equipe tiver menos de três membros, reduzir primeiro os opcionais e dividir revisão entre todos.

## 9. Plano de execução priorizado

1. Confirmar Tema 1, limites de escopo e tecnologia FastAPI; selecionar agente de codificação e registrar uso no processo.
2. Definir modelo de pergunta/fato/resposta e levantar fontes clínicas com revisão apropriada.
3. Especificar semântica de regras, desconhecidos, precedência e formato do traço.
4. Implementar carregador/validador da base JSON e motor puro com casos conhecidos.
5. Implementar schemas e endpoints FastAPI para avaliação; integrar motor e explicador.
6. Construir interface mínima para anamnese, resultado e trilha explicável.
7. Persistir histórico em SQLite se o núcleo e o prazo estiverem seguros.
8. Verificar instalação e fluxo localhost sem rede, registrar resultados dos testes, documentar limitações.
9. Preparar dados de demonstração, contingência, apresentação e ensaio de todos os integrantes.

## 10. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Regra clínica sem fonte ou interpretação errada | Exigir fonte rastreável e revisão veterinária; manter status explícito de validação |
| Desconhecido tratado como negativo | Tipo de resposta triestado/estado explícito e testes dedicados |
| Regras simultâneas com resultados conflitantes | Política documentada, precedência de segurança e conflito visível no traço |
| Escopo amplo demais para o prazo | Congelar MVP antes de histórico/relatórios; opcionais entram só depois do fluxo central |
| Resultado parece diagnóstico ou tratamento | Linguagem de triagem, limites e encaminhamento seguro revisados |
| Aplicação depende de internet/CDN | Hospedar assets localmente e conferir execução sem conectividade |
| Demonstração instável ou sem dados | Casos sintéticos pré-carregados, roteiro curto e contingência documentada |
| Equipe não consegue explicar o que foi gerado pela IA | Registrar decisões, mudanças e revisão humana; ensaiar contratos, regras e testes |

## 11. Decisões registradas e pendências

- **Decisão do texto mestre:** Python, FastAPI, Uvicorn, Pydantic, JSON, SQLite e pytest; arquitetura em módulos.
- **Diretriz oficial:** agente de codificação apoia a construção, mas motor explícito toma as decisões.
- **Pendências da equipe:** confirmar participantes; identificar revisor veterinário/técnico; escolher fontes clínicas; decidir quais sinais entram no MVP; confirmar se SQLite e histórico cabem após o núcleo.
- **Próxima etapa de implementação:** modelar dados/perguntas/regras e criar o motor determinístico mínimo com testes, após assegurar base clínica suficientemente fundamentada.

## Referências locais analisadas

- `C:\Users\felip\Downloads\Hackathon2026.pdf` — regulamento e temas (3 páginas).
- `C:\Users\felip\Downloads\Apresentação Hackathon2026.pdf` — visão do projeto, critérios, fluxo e entrega (16 páginas).
- `C:\Users\felip\.codex\attachments\5191ce83-1504-42f1-816d-9a93f4886240\Texto colado.txt` — prompt mestre fornecido pela equipe; tratado como pedido e especificação proposta, não como regulamento oficial.
