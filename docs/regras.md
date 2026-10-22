# Catálogo de regras de produção — LeiteCheck

**Versão da base:** 1.2.0  
**Escopo:** apoio inicial à anamnese e triagem de bovinos leiteiros. Não é ferramenta diagnóstica nem substitui avaliação veterinária.

## Como ler as regras
- **Fato positivo:** resposta explicitamente afirmativa.
- **Desconhecido:** ausência de resposta ou `null`; nunca é interpretado como `false`.
- **Prioridade `immediate`:** orientação de contato veterinário imediato.
- **Prioridade `veterinary_assessment`:** solicitar avaliação/orientação veterinária.
- A prioridade final é a de maior precedência entre as regras disparadas: `immediate` > `veterinary_assessment` > `none`.
- Cada regra é determinística e registra seu identificador, justificativa e fontes na trilha de inferência.

## Regras implementadas

| ID | Condição | Conclusão / prioridade | Fonte e justificativa |
|---|---|---|---|
| `R-RESP-001` | `respiratory_distress = true` | Contato veterinário imediato (`immediate`) | `merck_bloat`. Dificuldade respiratória evidente é tratada como sinal crítico. A fonte é referência internacional; validar com veterinário e buscar referência Embrapa específica antes de ampliar o uso. |
| `R-RECUMBENT-001` | `unable_to_rise = true` | Contato veterinário imediato (`immediate`) | `merck_recumbency`. Incapacidade de levantar exige avaliação rápida e pode gerar danos secundários. |
| `R-BLOAT-001` | `sudden_left_abdominal_distension = true` | Contato veterinário imediato (`immediate`) | `merck_bloat`. Distensão súbita pode ser compatível com timpanismo, mas a regra não confirma causa. Material técnico da Embrapa sobre timpanismo é uma referência complementar a revisar. |
| `R-UDDER-001` | `abnormal_milk = true` **ou** `udder_inflammation = true` | Avaliação veterinária (`veterinary_assessment`) | `embrapa_mastitis_2012` e `merck_mastitis`. A publicação da Embrapa descreve sinais observáveis no úbere e no leite. |
| `R-UDDER-SYSTEMIC-001` | Sinal mamário positivo **e** (`fever_state = fever_present` **ou** `reduced_appetite = true`) | Contato veterinário imediato (`immediate`) | `embrapa_mastitis_2012` e `merck_mastitis`. Associação de alteração mamária e sinal sistêmico eleva a preocupação, mas não fecha diagnóstico. Confirmar limiar de urgência com médico-veterinário. |
| `R-METABOLIC-SYSTEMIC-001` | `reduced_appetite = true` **e** `milk_drop = true` | Avaliação veterinária (`veterinary_assessment`) | `merck_mastitis` está registrada como contexto geral de sinal sistêmico, mas não é evidência específica para esta associação; a regra é exploratória e requer fonte própria. Não identifica causa metabólica. |

## Fontes cadastradas
- **Embrapa Gado de Leite.** Mendonça, L. C.; Guimarães, A. S.; Brito, M. A. V. P. e. *Diagnóstico de casos clínicos de mastite*. Comunicado Técnico 67, 2012. https://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/930366
- **Embrapa Gado de Leite.** Oliveira, V. M. de; Aroeira, L. J. M.; Silva, M. R. *Como prevenir a febre do leite em vacas leiteiras*. Comunicado Técnico 49, 2006. https://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/595888
- Merck Veterinary Manual. *Bloat in Ruminants*. https://www.merckvetmanual.com/digestive-system/diseases-of-the-ruminant-forestomach/bloat-in-ruminants
- Merck Veterinary Manual. *Bovine Secondary Recumbency*. https://www.merckvetmanual.com/musculoskeletal-system/bovine-secondary-recumbency/bovine-secondary-recumbency
- Merck Veterinary Manual. *Mastitis in Cattle*. https://www.merckvetmanual.com/reproductive-system/mastitis-in-large-animals/mastitis-in-cattle

## Lacunas conhecidas
1. As publicações da Embrapa precisam ser lidas integralmente e cada regra revisada por profissional veterinário.
2. A publicação sobre febre do leite ainda não sustenta uma regra nesta versão; não foi criada regra clínica apenas pelo título da fonte.
3. A regra `R-METABOLIC-SYSTEMIC-001` precisa de referência mais específica ou deve ser retirada em uma versão futura.
4. Não há fator de certeza calibrado nem validação clínica. Não exibir percentuais de confiança sem método e dados de validação.
5. Os casos atuais são cenários de teste sintéticos, não prontuários reais nem evidência de desempenho clínico.
