# AuditKM — Escopo funcional e proposta do produto

Registro da descrição do responsável pelo projeto em 10/10/2026.
Este documento registra o comportamento desejado; não afirma que todas as funcionalidades já estejam implementadas.

## Propósito

O AuditKM é um sistema de rastreamento, mapeamento e auditoria de rotas de veículos para empresas. Seu objetivo é registrar o uso do veículo durante uma viagem e oferecer ao Administrador evidências para avaliar o percurso, a quilometragem, o tempo e possíveis irregularidades.

## Fluxo da viagem

1. O motorista inicia uma viagem, identificando o veículo e o destino para o qual foi enviado.
2. Para iniciar, deve tirar uma foto do hodômetro e informar a quilometragem atual do veículo. A foto e a quilometragem inicial são obrigatórias.
3. O aplicativo registra o ponto geográfico de início e o horário da viagem e começa a mapear o trajeto.
4. O rastreamento continua durante todo o percurso, incluindo chegada ao destino, eventuais deslocamentos posteriores e retorno. Chegar ao destino não finaliza automaticamente a viagem.
5. A finalização provavelmente ocorrerá no ponto inicial, mas o retorno a esse ponto não foi definido como obrigação. A viagem termina quando o motorista aciona “Finalizar Viagem”.
6. Para finalizar, o motorista deve tirar uma nova foto do hodômetro e informar a quilometragem final. A foto e a quilometragem final são obrigatórias.
7. O sistema encerra a coleta referente à viagem, preserva o percurso completo e salva o registro concluído no banco de dados.
8. Após a finalização, gera o relatório de auditoria e o disponibiliza automaticamente na conta do Admin/Administrador, na página “Relatórios de Auditoria”. Não foi definido envio por e-mail ou outro canal externo.

## Mapa e acompanhamento

O mapa deve mostrar a região em que o dispositivo móvel se encontra, incluindo a cidade e o entorno necessário para visualizar o percurso. Deve permitir trajetos rurais e rodoviários, sem limitar o mapeamento ao perímetro urbano.

Durante a viagem, linhas representam o percurso registrado e um ícone de veículo representa a posição do motorista/dispositivo. No relatório concluído, o mapa conserva o trajeto realizado; a representação de movimento pertence ao acompanhamento da viagem, enquanto uma reprodução do percurso histórico poderá ser detalhada posteriormente.

A localização capturada pelo aplicativo é a do dispositivo móvel utilizado pelo motorista e associado à viagem e ao veículo.

## Conteúdo do relatório de auditoria

- Identificação da viagem, do motorista, do veículo e do destino.
- Foto do hodômetro no início e quilometragem inicial informada.
- Foto do hodômetro na finalização e quilometragem final informada.
- Ponto de início, ponto de encerramento e horários correspondentes.
- Mapa com linhas do trajeto completo efetuado pelo motorista.
- Tempo estimado até o destino e tempo efetivamente registrado, quando houver dados suficientes para determinar a chegada.
- Possíveis irregularidades identificadas na comparação do percurso com a referência adotada.

Para que o tempo estimado possa ser auditado, recomenda-se guardar a estimativa apresentada no início, além do horário real de chegada. A regra para detectar chegada — confirmação pelo motorista ou área geográfica do destino — ainda precisa ser definida.

## Destinos frequentes e possíveis irregularidades

O sistema deve reconhecer viagens recorrentes entre uma origem e um destino e permitir comparação entre os percursos.

Exemplo fornecido: uma viagem da Empresa A para a Fazenda A normalmente utiliza a BR-364. Caso outra viagem para o mesmo destino utilize uma rota diferente, o relatório pode sinalizar “Possível Irregularidade”.

Uma diferença de rota representa um indício a ser analisado, não uma confirmação automática de uso indevido. Trânsito intenso, obras e outros impedimentos podem explicar a alteração.

A definição de qual percurso será a referência — rota aprovada pelo Administrador, histórico recorrente ou rota calculada — ainda precisa ser detalhada. A primeira viagem não deve ser presumida como referência definitiva sem uma regra de aprovação.

Como a viagem pode incluir ida e retorno, recomenda-se comparar trechos equivalentes: ida com ida e retorno com retorno, mantendo ambos no relatório completo.

## Evolução futura: rotas alternativas

Futuramente, o AuditKM deverá mostrar possíveis rotas melhores para o mesmo destino, considerando situações como trânsito intenso e obras.

O responsável deseja avaliar integração com Waze, Google Maps ou outro serviço de mapas, rotas ou trânsito. Nenhum fornecedor foi escolhido neste registro. A viabilidade, os dados disponíveis, os custos e as condições de uso deverão ser avaliados na etapa de integração.

Abrir um aplicativo de navegação e incorporar dados de trânsito/rotas ao motor de auditoria são integrações diferentes; ambas poderão ser avaliadas conforme a necessidade.

## Critérios essenciais de aceite

- A viagem não inicia sem foto do hodômetro e quilometragem inicial.
- O ponto de início e o horário são registrados.
- A chegada ao destino não interrompe o rastreamento automaticamente.
- O trajeto continua sendo registrado até a finalização explícita, incluindo o retorno quando existir.
- A viagem não é finalizada sem foto do hodômetro e quilometragem final.
- O registro concluído preserva as duas fotos, as quilometragens, os horários e o percurso.
- O relatório é disponibilizado automaticamente ao Administrador, sem necessidade de o motorista enviá-lo manualmente.
- Alterações em percursos recorrentes podem ser sinalizadas como “Possível Irregularidade”.

## Pontos ainda a detalhar

- Confirmação da chegada ao destino e possibilidade de múltiplas paradas.
- Escolha e aprovação da rota de referência para viagens recorrentes.
- Limites de tolerância para desvios e regras de justificativa/revisão.
- Tratamento de falta de internet, GPS indisponível e pontos pendentes na finalização.
- Administrador ou conjunto de administradores que receberá cada relatório.
- Forma de aviso na conta administrativa quando houver um novo relatório.

## Relação com a análise técnica anterior

Esta descrição reforça como requisitos obrigatórios: foto inicial e final, rastreamento contínuo até o encerramento explícito e geração/disponibilização automática do relatório administrativo. O código anteriormente analisado deve ser comparado com esses critérios; a presença de campos de foto ou de um endpoint de auditoria não comprova que o fluxo completo esteja atendido.
