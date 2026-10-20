# Processo de desenvolvimento

## Referências e decisões

O trabalho começou pela leitura dos dois documentos oficiais do Hackathon UFJF 2026 e do prompt mestre fornecido pela equipe. Os documentos oficiais definem o Tema 1, a necessidade de base explícita e motor de inferência, apoio por agente de codificação, demonstração, documentação e execução local. FastAPI, SQLite, pytest, histórico e relatórios foram tratados como decisões do projeto.

O agente de codificação foi usado para estruturar a aplicação, implementar o motor e as camadas de API/interface/persistência, escrever cenários de teste e revisar a coerência entre regras e explicações. A triagem em execução é feita exclusivamente pelo código determinístico e pela base JSON; não há chamada a LLM.

## Iterações implementadas

1. Planejamento e matriz de rastreabilidade em `outputs/plano-inicial-leitecheck.md`.
2. Formato de fatos e regras em JSON e motor de encadeamento para frente, com desconhecidos preservados.
3. API FastAPI com validação Pydantic e persistência SQLite.
4. Interface sem dependências externas em tempo de execução; anamnese, resultado explicável, histórico, acompanhamento e impressão.
5. Documentação de arquitetura, critérios, execução e fontes veterinárias consultadas.

## Verificações executadas

- `python -m unittest discover -s tests -v`: 7 testes aprovados.
- `python -m compileall -q app tests`: compilação Python aprovada.
- `node --check static/app.js`: sintaxe JavaScript aprovada.
- Não foi possível executar `pytest` neste ambiente, pois o pacote não está instalado. Os testes são compatíveis com coleta pelo pytest após instalar `requirements.txt` e foram executados pela biblioteca padrão `unittest`.
- A verificação HTTP pelo navegador/loopback local não foi permitida pelo isolamento do ambiente. Os handlers e a persistência foram exercitados diretamente pelos testes; a inicialização interativa deve ser conferida em ambiente local permitido com o comando do README.

## Limitações da versão

As regras foram limitadas a sinais observáveis sustentados pelas referências cadastradas em `knowledge/rules.json`; não constituem protocolo clínico validado. A equipe deve solicitar revisão veterinária antes de uso operacional. Casos de demonstração são sintéticos e não evidenciam eficácia clínica.
