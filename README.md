# LeiteCheck

Prova de conceito local para coleta guiada de sinais e histórico de bovinos leiteiros em lactação, com triagem determinística e explicável. A LLM não participa das decisões durante a execução.

## Executar

Requer Python 3.10 ou superior. Instale as dependências uma vez, com internet, ou use um ambiente previamente preparado:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000`. A documentação da API fica em `/docs`. O formulário, estilos, scripts, regras e banco rodam localmente; não há CDN, serviço remoto ou chamada a LLM no fluxo. As fontes veterinárias são links apresentados como referência, não dependências de execução.

O banco SQLite é criado em `data/leitecheck.sqlite3`. Para escolher outro caminho, defina `LEITECHECK_DB` antes de iniciar.

## Testes

```powershell
python -m pytest
```

Os casos automatizados cobrem disparo e explicação de regras, respostas desconhecidas, validação da base, endpoints e persistência do histórico. Também é possível executar com `python -m unittest discover -s tests`.

## Como funciona

- `knowledge/questions.json`: perguntas tipadas e condições para resultado completo.
- `knowledge/rules.json`: versão, prioridades, regras, explicações e referências.
- `app/specialist/engine.py`: valida a base e executa encadeamento para frente. Um fato desconhecido não é convertido em falso.
- `app/main.py`: API FastAPI e interface; não contém lógica clínica.
- `app/database.py`: animais, avaliações, respostas, snapshot do resultado e acompanhamento informado pela pessoa usuária.
- `templates/` e `static/`: interface sem frameworks ou bibliotecas remotas.

As prioridades usam precedência fixa `immediate > veterinary_assessment > none`. Se várias regras forem acionadas, todas aparecem na trilha e a prioridade mais alta prevalece. A ausência de alerta significa apenas que as regras desta base limitada não encontraram um sinal codificado; não indica que o animal esteja saudável.

## Limites e uso responsável

As regras são uma triagem inicial de demonstração, não um protocolo clínico validado para todas as propriedades ou regiões. Não confirmam doenças e não recomendam medicamentos. O sistema deve ser revisto por médico-veterinário antes de uso operacional. Em dificuldade respiratória evidente, animal incapaz de se levantar ou preocupação urgente, contate diretamente um médico-veterinário.

Os critérios clínicos foram limitados a sinais observáveis descritos nas fontes abaixo. A aplicação registra a versão da base usada em cada avaliação e preserva o resultado histórico. Regras futuras devem registrar fonte, justificativa e revisão competente antes de serem habilitadas.

## Entrega e demonstração

1. Cadastre um animal ou continue sem cadastro.
2. Preencha os sinais; use “Não sei / não observado” se necessário.
3. Gere a triagem e confira a prioridade, a justificativa e os IDs de regras.
4. Abra a avaliação no histórico, registre acompanhamento e use “Imprimir / salvar como PDF”.

Casos de demonstração: (a) todas as respostas prioritárias negativas, (b) dificuldade respiratória e distensão súbita, (c) respostas prioritárias desconhecidas, (d) leite alterado com febre. Dados são sintéticos e não evidência de eficácia clínica.

## Fontes veterinárias consultadas

- Merck Veterinary Manual, [Bloat in Ruminants](https://www.merckvetmanual.com/digestive-system/diseases-of-the-ruminant-forestomach/bloat-in-ruminants).
- Merck Veterinary Manual, [Bovine Secondary Recumbency](https://www.merckvetmanual.com/musculoskeletal-system/bovine-secondary-recumbency/bovine-secondary-recumbency).
- Merck Veterinary Manual, [Mastitis in Cattle](https://www.merckvetmanual.com/reproductive-system/mastitis-in-large-animals/mastitis-in-cattle).

## Requisitos do hackathon

O evento exige agente de codificação com IA no desenvolvimento, ferramenta/código open source, uma aplicação especialista com base explícita e motor de inferência, demonstração funcional, documentação do processo/arquitetura/regras, apresentação e execução integral em localhost. A escolha de FastAPI, SQLite, pytest e esta divisão de módulos é decisão do projeto, não requisito imposto pelo regulamento.
# hackathon-2026
