# BoviHealth — checklist de prontidão (22/10/2026)

## Escopo
Prova de conceito de anamnese e triagem explicável. Não é diagnóstico, prescrição nem dispositivo validado clinicamente.

## Verificações reproduzíveis
1. Criar ambiente virtual, instalar `requirements.txt`.
2. Rodar `python preflight.py` e guardar a saída.
3. Rodar `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
4. Abrir `http://127.0.0.1:8000/` e `/docs`.
5. Testar cadastro de vaca, triagem, regra acionada, fontes, histórico, modal de acompanhamento e conclusão para nova triagem.
6. Reiniciar servidor e confirmar histórico persistido. Usar banco de demonstração isolado, sem dados pessoais reais.
7. Ensaiar casos em `knowledge/casos_demonstracao.json`: sintéticos, não equivalem a acurácia clínica.
8. Conferir entrega do código, documentação, slides, identificação dos integrantes e execução em localhost.

## Lacunas que não podem ser declaradas concluídas sem evidência
- Revisão por médico-veterinário de cada condição, prioridade e orientação.
- Conferência do texto integral das fontes; link cadastrado não é validação clínica.
- Teste visual no computador e navegador efetivamente usados na banca.
- Verificação dos materiais finais enviados dentro do prazo.

## Uso de IA (declarar o que a equipe de fato fez)
A equipe informou uso de Codex, Claude e ChatGPT. Registrar prompts representativos, decisões humanas, revisões, testes e correções. Não atribuir tarefas específicas a cada ferramenta sem evidência.

## Roteiro de 4 minutos (ajustar ao tempo concedido)
0:00 problema e escopo; 0:40 arquitetura: perguntas → fatos → regras versionadas → conclusão; 1:20 caso crítico e trilha explicável; 2:20 caso com informação desconhecida; 2:50 histórico e acompanhamento; 3:20 fontes, testes, limitações e colaboração com IA.

## Atenção
O termo "sem alerta nas regras" NÃO significa animal saudável. A triagem pode ser insuficiente mesmo com um alerta acionado.
