# ALERTA-19: Aplicação de Consulta e Gerenciamento de Dados da COVID-19 no Brasil

## Introdução

Este projeto consiste no desenvolvimento de uma aplicação CRUD para acesso e visualização de dados da pandemia de COVID-19 no Brasil, desenvolvido como parte da disciplina "DEV RÁPIDO EM PYTHON" (Desenvolvimento Rápido em Python) da UniFavip Wyden, ministrada pelo Professor Sebastião. A disciplina enfatiza metodologias de desenvolvimento ágil e rápido, com foco em projetos práticos que envolvem bancos de dados e interfaces gráficas.

O problema que a aplicação se propõe a resolver é a dificuldade de consultar e gerenciar informações atualizadas e históricas sobre a COVID-19 no Brasil de forma acessível e interativa. Ela visa superar a complexidade de lidar diretamente com grandes datasets brutos, tornando os dados epidemiológicos mais compreensíveis e exploráveis para estudantes, pesquisadores e o público em geral.

A importância do Desenvolvimento Rápido de Aplicações (RAD) neste contexto é demonstrada pela capacidade de construir uma solução funcional e robusta em prazos limitados. A metodologia RAD, com sua ênfase em prototipagem ágil, iteração contínua e entrega de valor incremental, permitiu a rápida construção de uma aplicação complexa a partir de um dataset real, validando os princípios da disciplina.

## Justificativa

A motivação para a escolha deste projeto reside na relevância contínua dos dados de saúde pública, especialmente aqueles relacionados à pandemia de COVID-19. A necessidade de ferramentas que democratizem o acesso e a análise dessas informações para fins acadêmicos e de pesquisa é premente. A complexidade e o volume do dataset brasil.io exigem uma solução eficiente para consulta e gerenciamento, o que confere ao projeto um caráter de desafio prático e de grande relevância.

Existe uma demanda real por interfaces interativas que permitam a exploração de grandes datasets epidemiológicos de forma intuitiva, tanto em ambientes acadêmicos quanto para tomadores de decisão. A pandemia gerou um volume massivo de dados que continuam sendo objeto de estudo e análise, e uma aplicação que facilite essa interação possui valor intrínseco e aplicabilidade prática.

A aplicação servirá como uma ferramenta de consulta valiosa para estudantes de Ciência da Computação, pesquisadores em saúde pública e qualquer interessado em epidemiologia. Ela permitirá a extração rápida de informações específicas, como casos por município em uma data específica ou óbitos por estado, e o acompanhamento da evolução da pandemia, apoiando análises e relatórios.

## Objetivos

### Objetivo Geral

Desenvolver uma aplicação CRUD em Python para consulta e gerenciamento eficiente de dados da COVID-19 no Brasil, utilizando metodologias de desenvolvimento rápido e atrelada a uma base de dados persistente.

### Objetivos Específicos

-   Implementar a funcionalidade de Leitura (Read) que permita a consulta e filtragem de dados da COVID-19 por múltiplos critérios, como data, estado e município, exibindo métricas chave (casos confirmados, óbitos, novos casos)
-   Desenvolver uma interface gráfica (GUI) intuitiva e responsiva que facilite a interação do usuário com a aplicação e a visualização dos dados
-   Integrar a aplicação com um sistema de banco de dados (SQLite) para o armazenamento persistente e recuperação otimizada do dataset da COVID-19
-   Aplicar e demonstrar os princípios e técnicas de Desenvolvimento Rápido em Python ao longo do ciclo de vida do projeto
-   Implementar as funcionalidades de Criação (Create), Atualização (Update) e Exclusão (Delete) de registros na base de dados local, contextualizando-as para o gerenciamento do dataset importado

## Base de Dados

A base de dados central para este projeto é o dataset `caso_full.csv.gz`, acessível publicamente através da plataforma brasil.io, com a URL: https://data.brasil.io/dataset/covid19/caso_full.csv.gz

O brasil.io é um projeto não-governamental que realiza um trabalho voluntário de coleta e agregação de informações sobre o número de casos confirmados e óbitos causados por SARS-COV-2 em níveis estadual e municipal no Brasil. Os dados são compilados a partir de relatórios públicos das Secretarias de Saúde estaduais e municipais, com o objetivo de fornecer informações em tempo real.

Os dados são fornecidos em formato CSV compactado (.csv.gz). O arquivo `caso_full.csv.gz` possui um tamanho considerável de aproximadamente 88.15MB, indicando um volume substancial de informações que requerem tratamento eficiente.

### Pré-processamento dos Dados

Considerando o formato dos dados (CSV.GZ) e as características conhecidas do dataset, os pré-processamentos incluem:

-   Descompactação do arquivo
-   Carregamento eficiente dos dados para um banco de dados relacional (SQLite) para otimizar consultas
-   Tratamento de valores ausentes (NaN)
-   Conversão de tipos de dados (strings para datas e números inteiros)
-   Agregação ou filtragem inicial para criar visões de dados mais úteis para a aplicação

### Limitações dos Dados

É importante reconhecer as limitações do dataset brasil.io. A qualidade dos dados depende diretamente da precisão das informações reportadas pelas secretarias de saúde estaduais e municipais. Além disso, a tabulação de óbitos e casos é baseada na data de coleta dos dados, o que pode introduzir um atraso de uma a sete semanas em relação à data real dos sintomas ou testes. Apesar dessas limitações, o dataset é amplamente reconhecido como uma excelente fonte para monitorar o curso da pandemia em tempo real.

## Tecnologias Utilizadas

-   **Linguagem de Programação**: Python 3.x
-   **Framework Web**: Flask, utilizado para a estrutura da aplicação web, gerenciamento de rotas e integração com o backend
-   **Bibliotecas Gráficas**: Tkinter para interface desktop e Matplotlib para visualizações integradas ao Flask)
-   **Banco de Dados**: SQLite, para persistência local e gerenciamento da base de dados da COVID-19 importada do CSV.GZ
-   **Manipulação de Dados**: Pandas, para manipulação eficiente e pré-processamento do dataset CSV em memória antes da persistência no banco de dados
-   **Ferramentas de Desenvolvimento**:
    -   VSCode (ambiente de desenvolvimento integrado)
    -   Git (sistema de controle de versão distribuído)
    - Figma (Prototipagem coletiva)
    -   GitHub (plataforma de hospedagem de código-fonte e colaboração)

## Metodologia de Desenvolvimento

O projeto foi conduzido sob os princípios do Desenvolvimento Rápido de Aplicações (RAD), com um foco claro em ciclos de desenvolvimento curtos, prototipagem ágil e feedback contínuo. Uma metodologia iterativa e incremental foi adotada, permitindo a construção progressiva das funcionalidades CRUD e a adaptação a novos insights durante o processo.

### Principais Etapas de Desenvolvimento

1.  **Análise e Requisitos**: Compreensão das necessidades para uma aplicação CRUD de consulta de dados COVID-19
2.  **Aquisição e Pré-processamento de Dados**: Download do dataset brasil.io e preparação para importação no banco de dados
3.  **Design da Arquitetura**: Definição da estrutura da aplicação Flask e do modelo de dados para o SQLite
4.  **Desenvolvimento Iterativo**: Implementação incremental das funcionalidades CRUD, com foco inicial na funcionalidade 'Read' (consulta)
5.  **Desenvolvimento da Interface Gráfica**: Criação da GUI para interação intuitiva
6.  **Testes e Validações**: Verificação da integridade dos dados, da funcionalidade das consultas e da usabilidade da interface

Como um projeto individual, a organização do trabalho priorizou a gestão de tempo eficaz, a definição de um Produto Mínimo Viável (MVP) para garantir a entrega das funcionalidades essenciais, e a integração contínua dos componentes desenvolvidos.

## Resultados e Funcionalidades

A aplicação implementa as seguintes funcionalidades CRUD (Create, Read, Update, Delete) atreladas à base de dados da COVID-19:

### Read (Consulta de Dados)

Esta é a funcionalidade central da aplicação. Permite aos usuários consultar e visualizar dados da COVID-19 com base em diversos critérios. É possível filtrar informações por data, estado e município, exibindo métricas chave como o número acumulado de casos confirmados, óbitos, e a contagem diária de novos casos e óbitos.

**Exemplos de consultas**:

-   Total de casos e óbitos em São Paulo em uma data específica
-   Evolução de novos casos em Pernambuco ao longo do tempo
-   Comparativo de casos confirmados entre diferentes municípios de uma região

### Create (Criação de Registros)

Funcionalidade para adicionar novos registros à base de dados local. No contexto desta aplicação de consulta, isso se refere à capacidade de importar novas versões do dataset brasil.io ou adicionar metadados/anotações personalizadas sobre os dados existentes.

### Update (Atualização de Registros)

Permite a modificação de registros existentes na base de dados local. Útil para corrigir dados importados, atualizar informações com base em novas fontes, ou importar dados mais recentes do brasil.io para substituir versões antigas, garantindo que a base de dados esteja sempre atualizada.

### Delete (Exclusão de Registros)

Funcionalidade para remover registros específicos da base de dados local. Pode ser utilizada para limpar dados desatualizados, remover entradas incorretas ou gerenciar o espaço de armazenamento da base de dados.

### Impacto da Solução

A aplicação resolve o problema de acesso fragmentado e a dificuldade na manipulação de grandes volumes de dados de saúde pública. Ela oferece uma interface centralizada, intuitiva e interativa que democratiza o acesso à informação da COVID-19, capacitando estudantes e pesquisadores a realizar análises rápidas e eficazes sem a necessidade de conhecimento avançado em programação ou bancos de dados.

(INSERIR IMGs dps)

## Conclusão

O desenvolvimento desta aplicação proporcionou aprendizados técnicos significativos, incluindo a manipulação eficiente de grandes datasets em Python, a integração de frameworks web como Flask com bancos de dados (SQLite), o design de interfaces de usuário (UI/UX) e a importância da modularidade do código. Do ponto de vista metodológico, foi possível aplicar na prática os princípios de Desenvolvimento Rápido de Aplicações (RAD) e gerenciar um projeto de software completo do início ao fim.

### Aspectos Bem-Sucedidos

-   Robustez da integração com o banco de dados
-   Usabilidade e clareza da interface gráfica
-   Eficiência na consulta e filtragem de dados
-   Capacidade de entregar um MVP funcional dentro do prazo da disciplina

### Oportunidades de Melhoria

Para versões futuras da aplicação, identificam-se as seguintes áreas de aprimoramento:

-   Otimização de performance para datasets ainda maiores
-   Implementação de funcionalidades de visualização de dados mais avançadas (gráficos interativos)
-   Expansão das opções de filtragem e agregação de dados
-   Incorporação de mais fontes de dados epidemiológicos

## Repositório GitHub

https://github.com/eversonfilipe/ALERTA-19

O repositório contém:

-   Código-fonte completo da aplicação
-   Este arquivo README.md com instruções de uso detalhadas
-   Imagens ou GIFs demonstrando o sistema em funcionamento
-   Documentação adicional do projeto

----------

_Este projeto foi desenvolvido como parte da disciplina "DEV RÁPIDO EM PYTHON" da UniFavip Wyden, aplicando metodologias de Desenvolvimento Rápido de Aplicações para criar uma solução prática de consulta e gerenciamento de dados epidemiológicos._
