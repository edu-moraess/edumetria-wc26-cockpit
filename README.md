Edumetria WC26 Cockpit
Plataforma de Análise Econômica, Financeira e Geopolítica da Copa do Mundo FIFA 2026™

Eduardo Moraes
Cientista de Dados Quantitativos · Pesquisador em Economia · Estudante de Engenharia de Sistemas e Controle

---

Sumário Executivo

O Edumetria WC26 Cockpit é uma plataforma de análise quantitativa projetada para monitorar, analisar e projetar os potenciais impactos econômicos, financeiros, geopolíticos e setoriais associados à Copa do Mundo FIFA 2026™, sediada por Estados Unidos, Canadá e México.

A plataforma integra bases de dados públicas de bancos centrais, agências nacionais de estatística e mercados financeiros globais para construir indicadores proprietários, estruturas de monitoramento de riscos e cenários econômicos prospectivos.

O projeto combina:

· Engenharia de Dados
· Análise Quantitativa
· Economia Aplicada
· Modelagem de Riscos
· Projeções (Forecasting)
· Visualização de Dados

em um ambiente analítico totalmente reprodutível.

Horizonte de Análise: 2026–2035

---

Motivação da Pesquisa

Eventos esportivos de grande porte costumam estar associados a expectativas de:

· Crescimento econômico
· Expansão do turismo
· Desenvolvimento de infraestrutura
· Efeitos no mercado de trabalho
· Atração de investimento estrangeiro
· Legado econômico de longo prazo

No entanto, a evidência empírica frequentemente mostra resultados mistos.

O objetivo deste projeto é fornecer uma estrutura transparente e reprodutível para analisar esses potenciais impactos utilizando dados do mundo real, métodos quantitativos e premissas claramente documentadas.

---

Dashboard ao Vivo

Ambiente de Produção
https://edumetriaquant.streamlit.app

---

Estrutura Analítica

A plataforma está organizada em quatro pilares analíticos:

· Monitoramento Econômico – Acompanhamento das condições macroeconômicas nos países-sede.
· Monitoramento dos Mercados Financeiros – Acompanhamento do desempenho dos mercados, volatilidade e sentimento do investidor.
· Monitoramento Geopolítico e de Riscos – Avaliação das condições de incerteza global e de estresse macrofinanceiro.
· Projeções e Análise de Cenários – Construção de projeções probabilísticas e cenários prospectivos.

---

Módulos do Dashboard

Módulo Descrição Situação
Visão Geral Executiva Resumo executivo dos principais indicadores ✅
Macroeconomia PIB, IPC, taxas de juros, desemprego e curva de juros ✅
Análise de Turismo Fluxos turísticos e monitoramento setorial ✅
Monitor da Aviação Indicadores de energia e aviação ✅ Parcial
Análise de Hotelaria Indicadores de ocupação hoteleira e acomodações 🚧
Mercados Financeiros Índices, ETFs, volatilidade, drawdowns e correlações ✅
Monitor Geopolítico Indicadores de risco e incerteza globais ✅
Painel ESG Indicadores de sustentabilidade e meio ambiente 🚧
Centro de Previsões Simulações de Monte Carlo e análise de cenários ✅

---

Fontes de Dados

Dados Macroeconômicos

· Federal Reserve Economic Data (FRED)
· Statistics Canada (StatCan)
· Banco de México (Banxico)
· Instituto Nacional de Estadística y Geografía (INEGI)

Mercados Financeiros

· Yahoo Finance
· Dados do Mercado de Títulos do Tesouro (Treasury)

Mercados de Energia

· West Texas Intermediate (WTI)
· Brent Crude Oil

Integrações Futuras

· Fundo Monetário Internacional (FMI)
· Banco Mundial
· OCDE
· IATA
· OAG
· STR Global

---

Modelos Quantitativos

World Cup Risk Score (WCRS)
Estrutura proprietária desenvolvida para monitorar o estresse macrofinanceiro global por meio de:

· Indicadores de volatilidade
· Condições do mercado de energia
· Dinâmica dos mercados financeiros

World Cup Legacy Index (WCLI)
Estrutura composta experimental concebida para avaliar os potenciais efeitos de legado econômico de longo prazo associados ao torneio. A implementação atual concentra‑se principalmente em métricas de turismo, com expansão futura prevista para:

· PIB
· Emprego
· Investimento Estrangeiro Direto (IED)
· Infraestrutura
· Métricas ESG

Motor de Previsão de Monte Carlo
O Centro de Previsões implementa atualmente:

· Bootstrap Paramétrico
· Simulação de Monte Carlo
· Modelagem de Volatilidade Histórica

Configuração atual:

· 20.000 simulações
· Análise de percentis
· Distribuições de cenários
· Previsão probabilística

Monitor da Curva de Juros
Acompanhamento dos spreads dos títulos do Tesouro como indicador macroeconômico de alerta precoce.
Implementação atual:

· Spread 10A–2A
· Avaliação de Risco de Recessão

---

Metodologia do Centro de Previsões

A estrutura atual de previsão foi concebida como uma arquitetura MVP transparente.

Implementado

· Distribuições históricas de crescimento
· Simulações de bootstrap paramétrico
· Geração de intervalos de confiança
· Previsão por percentis

Limitações Atuais

· Assume normalidade dos incrementos
· Não modela mudanças de regime
· Não inclui eventos de cauda extrema
· Não incorpora choques exógenos da Copa do Mundo
· Não modela dependências entre países

Todas as limitações estão explicitamente documentadas para garantir transparência metodológica.

---

Arquitetura Técnica

```
edumetria-wc26-cockpit/
│
├── config.py
├── requirements.txt
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
│
├── database/
│   ├── schema.sql
│   └── connection.py
│
├── etl/
│   ├── extractors/
│   ├── transformers/
│   ├── loaders/
│   └── run_pipeline.py
│
├── models/
│   ├── econometric/
│   ├── ml/
│   └── montecarlo/
│
├── metadata/
│   └── data_dictionary.py
│
├── dashboards/
│   ├── app.py
│   ├── components.py
│   └── pages/
│
├── deployment/
│   ├── docker/
│   └── streamlit_cloud/
│
└── tests/
```

---

Pipeline de Dados

APIs Externas
  ↓
Extração
  ↓
Transformação
  ↓
Carga
  ↓
Data Warehouse
  ↓
Modelos Quantitativos
  ↓
Dashboard

---

Roteiro de Pesquisa

Econometria e Inferência Causal
Implementações futuras previstas:

· Diferenças-em-Diferenças (DiD)
· Controle Sintético
· Estudos de Evento
· Ridge VAR
· GARCH-X
· Projeções Locais
· Modelos de Insumo-Produto

Aprendizado de Máquina
Implementações futuras previstas:

· XGBoost
· LightGBM
· Prophet
· LSTM

Análise de Riscos
Implementações futuras previstas:

· Teoria de Valores Extremos (EVT)
· Testes de Estresse
· Modelos de Mudança de Regime
· Análise de Cenários
· Monitoramento de Risco Soberano

Avaliação de Impacto do Legado
Módulos de pesquisa futuros:

· Benchmarking Histórico de Copas do Mundo
· Análise Contrafactual
· Avaliação de Impacto em Infraestrutura
· Análise do Legado Turístico
· Análise de Impacto no Investimento Estrangeiro

---

Princípios Metodológicos

O projeto segue os seguintes princípios:

· Transparência
· Reprodutibilidade
· Auditabilidade
· Premissas Explícitas
· Limitações Documentadas

Os resultados não devem ser interpretados como consultoria de investimento, previsões oficiais ou recomendações de políticas.

---

Situação do Projeto

Estágio Atual: MVP Concluído

✅ Ingestão de Dados
✅ Pipeline de ETL
✅ Data Warehouse
✅ Dashboard Quantitativo
✅ Centro de Previsões
✅ Indicadores Proprietários
✅ Estrutura de Monitoramento de Riscos

Em Desenvolvimento

🚧 Modelos Econométricos
🚧 Estruturas de Inferência Causal
🚧 Análise Contrafactual
🚧 Estimação do Impacto do Legado
🚧 Análise Avançada de Riscos

---

Visão de Futuro

O objetivo de longo prazo é evoluir a plataforma para um ambiente analítico de nível de pesquisa voltado a:

· Avaliação de Impacto Econômico
· Análise de Riscos
· Econometria Aplicada
· Avaliação de Políticas
· Economia de Megaeventos

inspirado em estruturas analíticas comumente utilizadas por bancos centrais, organizações multilaterais e instituições de pesquisa econômica.

---

Autor

Eduardo Moraes
Cientista de Dados Quantitativos
Pesquisador em Economia
Estudante de Engenharia de Sistemas e Controle

Projeto de Pesquisa Independente

---

Aviso Legal

FIFA World Cup 2026™ é uma marca registrada da FIFA.
Este projeto é uma iniciativa acadêmica e analítica independente e não é afiliado, endossado ou patrocinado pela FIFA.

---

Licença

© 2026 Eduardo Moraes. Todos os direitos reservados.

Código de infraestrutura, pipelines de dados e dashboards
O código-fonte referente à infraestrutura de dados, pipelines de extração/transformação/carga (ETL), dashboards de visualização e utilitários de configuração é disponibilizado sob a Licença MIT, permitindo uso, modificação e distribuição desde que mantida a atribuição ao autor original.

Copyright (c) 2026 Eduardo Moraes

É concedida permissão, gratuitamente, a qualquer pessoa que obtenha uma cópia deste software e dos arquivos de documentação associados (o "Software"), para lidar com o Software sem restrições, incluindo, sem limitação, os direitos de usar, copiar, modificar, mesclar, publicar, distribuir, sublicenciar e/ou vender cópias do Software, e permitir que as pessoas a quem o Software é fornecido o façam, sujeito às seguintes condições:

O aviso de copyright acima e este aviso de permissão devem ser incluídos em todas as cópias ou partes substanciais do Software.

O SOFTWARE É FORNECIDO "NO ESTADO EM QUE SE ENCONTRA", SEM GARANTIA DE QUALQUER TIPO, EXPRESSA OU IMPLÍCITA, INCLUINDO, MAS NÃO SE LIMITANDO A, GARANTIAS DE COMERCIABILIDADE, ADEQUAÇÃO A UM DETERMINADO FIM E NÃO VIOLAÇÃO. EM NENHUM CASO OS AUTORES OU DETENTORES DOS DIREITOS AUTORAIS SERÃO RESPONSÁVEIS POR QUALQUER REIVINDICAÇÃO, DANO OU OUTRA RESPONSABILIDADE, SEJA EM UMA AÇÃO DE CONTRATO, ATO ILÍCITO OU DE OUTRA FORMA, DECORRENTE DE, FORA DE OU EM CONEXÃO COM O SOFTWARE OU O USO OU OUTRAS NEGOCIAÇÕES NO SOFTWARE.

Modelos proprietários
Os modelos analíticos proprietários — incluindo, mas não se limitando a, o World Cup Risk Score (WCRS), o World Cup Legacy Index (WCLI) e o motor de previsão de Monte Carlo — são protegidos por direitos autorais. Sua reprodução, adaptação, engenharia reversa ou utilização em qualquer forma requer autorização prévia e expressa por escrito do autor. O acesso público ao dashboard analítico não confere qualquer direito sobre esses modelos.