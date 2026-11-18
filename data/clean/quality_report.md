# Relatório de qualidade dos dados

## Resumo
- Linhas brutas: 310,745
- Linhas finais (grão freguesia): 310,745
- Linhas agregadas por concelho: 38,225
- Período: 2020-11 a 2026-07
- Distritos: 18
- Concelhos (sem 'OUTROS'): 278
- Removidas por data/consumo inválidos: 0
- Linhas 'OUTROS' (marcadas, excluídas do agregado por concelho): 1,730
- Valores negativos: 395 (ação: set_nan)
- Duplicados exatos removidos: 0
- Chaves repetidas (data, freguesia, tensão): 0

## Decisões do LLM sobre as colunas
| Coluna bruta | Ação | Nome final | Justificação |
|---|---|---|---|
| data | rename | data | Manter coluna de referência temporal. |
| distrito | rename | distrito | Identificação geográfica de distrito. |
| coddistrito | rename | cod_distrito | Normalização do nome da coluna. |
| concelho | rename | concelho | Identificação geográfica de concelho. |
| coddistritoconcelho | rename | cod_concelho | Normalização do nome da coluna. |
| freguesia | rename | freguesia | Identificação geográfica de freguesia. |
| coddistritoconcelhofreguesia | rename | cod_freguesia | Normalização do nome da coluna. |
| nivel_de_tensao | rename | nivel_tensao | Normalização do nome da coluna. |
| energia_ativa_kwh | rename | consumo_kwh | Normalização do nome da coluna. |
| ano | drop | - | Redundante, derivável da coluna data. |
| mes | drop | - | Redundante, derivável da coluna data. |
| mes_int | drop | - | Redundante, derivável da coluna data. |

## Observações de qualidade (LLM)
- Presença de valores negativos no consumo, possivelmente associados a acertos de faturação ou injeção na rede, que devem ser tratados como nulos.
- A coluna freguesia apresenta valores nulos, sugerindo falta de granularidade em certos registos.
- Os prefixos 'OUTROS' indicam a existência de consumos agregados que não permitem a desagregação ao nível do concelho.
- A estrutura de códigos de distrito e concelho apresenta inconsistências de preenchimento (ex: '10--'), exigindo limpeza de caracteres especiais.
- O dataset cobre um período temporal extenso, sendo necessário garantir a consistência do formato da data.
- A elevada cardinalidade na coluna de consumo sugere dados de faturação reais e não estimativas arredondadas.
