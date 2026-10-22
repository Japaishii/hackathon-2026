# Arquitetura e regras do LeiteCheck

## Fluxo

```text
Interface local HTML/CSS/JS → FastAPI/Pydantic → validação de respostas
                                                   ↓
                           motor puro ← regras JSON versionadas
                                ↓
                 explicação + trilha → SQLite → histórico/relatório
```

O browser apenas coleta e apresenta. A API valida tipos e coordena. `infer()` recebe fatos e uma base carregada, sem rede, estado global mutável ou chamadas a modelos generativos. A memória de trabalho é local a cada inferência; apenas o snapshot de respostas e resultado é persistido.

## Contrato e semântica

Fatos booleanos aceitam `true`, `false` ou `null`; `null`/ausência significa desconhecido. Perguntas `enum` aceitam apenas as opções declaradas; para temperatura, `not_measured` é diferente de desconhecido e de temperatura normal. Regras suportam conjuntos `all`, `any`, `any_systemic` e comparações `equals`; cada grupo de alternativas precisa ter ao menos uma condição satisfeita. Uma regra dispara uma vez por execução. Fatos derivados monotônicos são suportados pelo motor; a base atual não depende deles. Cada regra que dispara adiciona conclusão, fonte e justificativa ao traço.

A precedência é fixa em `immediate`, `veterinary_assessment`, `none`. O motor preserva todas as conclusões concorrentes e retorna a prioridade de maior precedência. A base atual não contém conclusões mutuamente excludentes. Sem fatos suficientes, o status é `insufficient`, mesmo se alguma regra positiva já indicar alerta; o alerta continua apresentado.

## Regras incluídas

| ID | Condição | Resultado | Fundamentação |
|---|---|---|---|
| R-RESP-001 | dificuldade respiratória evidente | contato veterinário imediato | Sinais respiratórios em distensão ruminal grave podem evoluir rapidamente (Merck, bloat) |
| R-RECUMBENT-001 | caída e incapaz de levantar | contato veterinário imediato | Causas variadas e risco de dano secundário (Merck, recumbency) |
| R-BLOAT-001 | distensão súbita do flanco esquerdo | contato veterinário imediato | Alerta antes do possível aparecimento de dificuldade respiratória; não confirma timpanismo |
| R-UDDER-001 | leite alterado ou inflamação do úbere | avaliação/orientação veterinária | Sinais observáveis associados a mastite clínica, não confirmação |
| R-UDDER-SYSTEMIC-001 | leite alterado ou inflamação do úbere, junto a febre ou apetite reduzido | contato veterinário imediato | Sinais sistêmicos podem acompanhar mastite grave; avaliação clínica necessária |
| R-METABOLIC-SYSTEMIC-001 | apetite reduzido e queda repentina de produção | avaliação/orientação veterinária | Associação requer investigação e não identifica uma causa específica |

As referências completas e data de consulta estão em `knowledge/rules.json`. Os critérios devem ser revisados por médico-veterinário antes de uso além da demonstração.

## Persistência

SQLite armazena identificador e metadados básicos do animal, avaliações imutáveis (respostas, resultado e versão da base via resultado) e anotações de acompanhamento fornecidas pelo usuário. Não armazena credenciais. O relatório imprimível é renderizado no browser para PDF, sem serviço externo.
