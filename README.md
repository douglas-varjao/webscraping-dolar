# Projeto de Web Scraping e Análise: Cotação Diária do Dólar

## Visão Geral do Projeto

Este projeto automatiza a coleta, processamento, análise e visualização das cotações diárias do dólar, utilizando a API do Banco Central do Brasil. Ele gera relatórios gráficos e uma planilha Excel com os dados históricos, e oferece a funcionalidade de envio automático desses relatórios por e-mail. O objetivo é fornecer insights rápidos sobre a variação do dólar e identificar dias sem cotação (feriados/fins de semana).

## Funcionalidades

* **Coleta de Dados:** Obtém cotações de compra e venda do dólar diretamente da API do Banco Central para um período especificado.
* **Tratamento de Dados:** Utiliza a biblioteca Pandas para limpar, formatar e organizar os dados, identificando também os dias sem cotação.
* **Geração de Relatórios Visuais:** Cria gráficos de linha que mostram a variação da cotação de compra e uma comparação entre compra e venda ao longo do tempo.
* **Exportação de Dados:** Salva as cotações completas e os dias sem cotação em um arquivo Excel (`.xlsx`) com abas separadas.
* **Exibição de Estatísticas:** Apresenta um resumo no terminal com as últimas cotações e estatísticas como média, máxima, mínima e volatilidade do dólar.
* **Automação de Envio:** Permite enviar o relatório completo (planilha Excel e gráficos) por e-mail para destinatários específicos.

## Tecnologias Utilizadas

* `Python 3.x`
* `requests`: Para fazer requisições HTTP à API do Banco Central.
* `pandas`: Para manipulação e análise de dados tabulares.
* `datetime`, `timedelta`, `pathlib`: Para gerenciamento de datas e caminhos de arquivo.
* `matplotlib.pyplot`: Para a criação dos gráficos de visualização de dados.
* `smtplib`, `email.mime`: Para a funcionalidade de envio de e-mails com anexos.
* `os`: Para lidar com variáveis de ambiente (essencial para segurança de credenciais).
* `Git` e `GitHub`: Para controle de versão e hospedagem do projeto.

### Pré-requisitos
* Python 3.x instalado.
