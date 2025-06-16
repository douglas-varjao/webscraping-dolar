##BIBLIOTECAS
import requests
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

##"""Obtém cotações do dólar dos últimos N dias do Banco Central"""
def get_dolar_quotes(days=30):
    
    try:
        # 1. Definir período
        fim = datetime.today()
        inicio = fim - timedelta(days=days)
        
        # 2. Formatando datas (API requer formato mm-dd-yyyy)
        inicio_str = inicio.strftime("%m-%d-%Y")
        fim_str = fim.strftime("%m-%d-%Y")
        
        # 3. Construir URL da API
        url = (
            f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
            f"CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?"
            f"@dataInicial='{inicio_str}'&@dataFinalCotacao='{fim_str}'&"
            f"$format=json"
        )
        
        # 4. Fazer requisição
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # 5. Processar dados
        dados = response.json()
        
        # Verificar se existem dados
        if not dados.get('value'):
            print("A API retornou dados vazios. Verifique as datas.")
            return pd.DataFrame(), pd.DataFrame()
            
        df = pd.DataFrame(dados["value"])
        
        # 6. Verificar colunas necessárias
        required_cols = ["dataHoraCotacao", "cotacaoCompra", "cotacaoVenda"]
        if not all(col in df.columns for col in required_cols):
            print("Estrutura da API mudou. Colunas não encontradas.")
            return pd.DataFrame(), pd.DataFrame()
        
        # 7. Processar os dados
        df = df[required_cols].copy()
        df.rename(columns={
            "dataHoraCotacao": "Data",
            "cotacaoCompra": "Compra (R$)",
            "cotacaoVenda": "Venda (R$)"
        }, inplace=True)
        
        df["Data"] = pd.to_datetime(df["Data"]).dt.normalize()
        df.sort_values("Data", inplace=True)
        
        # 8. Identificar dias sem cotação
        all_dates = pd.DataFrame({
            "Data": pd.date_range(start=inicio, end=fim)
        })
        
        merged = pd.merge(all_dates, df, on="Data", how="left")
        missing_dates = merged[merged["Compra (R$)"].isna()].copy()
        
        # 9. Adicionar informações de dia da semana
        df["Dia_Semana"] = df["Data"].dt.day_name('pt_BR')
        missing_dates["Dia_Semana"] = missing_dates["Data"].dt.day_name('pt_BR')
        
        # 10. Classificar dias sem cotação
        missing_dates["Tipo"] = "Fim de Semana"
        missing_dates.loc[
            ~missing_dates["Dia_Semana"].isin(["sábado", "domingo"]), 
            "Tipo"
        ] = "Provável Feriado"
        
        return df, missing_dates[["Data", "Dia_Semana", "Tipo"]]
        
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}", file=sys.stderr)
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        print(f"Erro inesperado: {e}", file=sys.stderr)
        return pd.DataFrame(), pd.DataFrame()

##"""Gera relatório com gráficos e retorna caminhos dos arquivos"""
def generate_report(df_dolar, df_missing, output_dir):

    try:
        # 1. Gráfico de variação
        plt.figure(figsize=(12, 6))
        plt.plot(df_dolar['Data'], df_dolar['Compra (R$)'], marker='o', linestyle='-', color='blue')
        plt.title('Variação do Dólar (Compra) - Últimos 30 Dias', fontsize=14)
        plt.xlabel('Data', fontsize=12)
        plt.ylabel('Valor (R$)', fontsize=12)
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        graph_path = output_dir / 'variacao_dolar.png'
        plt.savefig(graph_path, dpi=300)
        plt.close()
        
        # 2. Gráfico de comparação
        plt.figure(figsize=(12, 6))
        plt.plot(df_dolar['Data'], df_dolar['Compra (R$)'], label='Compra', marker='o')
        plt.plot(df_dolar['Data'], df_dolar['Venda (R$)'], label='Venda', marker='x')
        plt.title('Comparação entre Cotações de Compra e Venda', fontsize=14)
        plt.xlabel('Data', fontsize=12)
        plt.ylabel('Valor (R$)', fontsize=12)
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        comp_venda_path = output_dir / 'compra_venda_dolar.png'
        plt.savefig(comp_venda_path, dpi=300)
        plt.close()
        
        return graph_path, comp_venda_path
        
    except Exception as e:
        print(f"Erro ao gerar gráficos: {e}", file=sys.stderr)
        return None, None

## """Envia email com os resultados"""
def send_email(receiver_email, subject, body, attachments=None):

    try:
        # Configurações - Edite com seus dados
        sender_email = "seu_email@gmail.com"
        password = "sua_senha"  # Recomendo usar variáveis de ambiente
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        
        # Corpo do email
        msg.attach(MIMEText(body, 'html'))
        
        # Anexar arquivos
        if attachments:
            for file_path in attachments:
                if file_path and file_path.exists():
                    part = MIMEBase('application', "octet-stream")
                    with open(file_path, 'rb') as file:
                        part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition','attachment; filename="{}"'.format(file_path.name))
                    msg.attach(part)
        
        # Enviar email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
            
        print("\nEmail enviado com sucesso!")
        
    except Exception as e:
        print(f"\nErro ao enviar email: {e}", file=sys.stderr)

##Bloco Principal
if __name__ == "__main__":
    try:
        print("Iniciando obtenção de cotações do dólar...")
        
        # 1. Obter dados
        df_dolar, df_missing = get_dolar_quotes(days=30)
        
        if not df_dolar.empty:
            print("Dados obtidos com sucesso!")
            
            # 2. Configurar diretório de saída
            output_dir = Path(r"D:\Aulas\Portifolio\WebScraping\Cotacao_do_Dolar")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 3. Gerar relatório
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_path = output_dir / f"cotacao_dolar_{timestamp}.xlsx"
            
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df_dolar.to_excel(writer, sheet_name='Cotações', index=False)
                df_missing.to_excel(writer, sheet_name='Dias_Sem_Cotacao', index=False)
            
            # 4. Gerar gráficos
            graph_path, comp_venda_path = generate_report(df_dolar, df_missing, output_dir)
            
            # 5. Exibir relatório
            print(f"\n{'='*50}")
            print(f"{'RELATÓRIO DE COTAÇÕES DO DÓLAR':^50}")
            print(f"{'='*50}")
            
            stats = {
                'Média Compra': df_dolar['Compra (R$)'].mean(),
                'Máxima Compra': df_dolar['Compra (R$)'].max(),
                'Mínima Compra': df_dolar['Compra (R$)'].min(),
                'Volatilidade': df_dolar['Compra (R$)'].std(),
                'Variação Total': df_dolar['Compra (R$)'].iloc[-1] - df_dolar['Compra (R$)'].iloc[0]
            }
            
            print(f"\nPeríodo: {df_dolar['Data'].min().date()} a {df_dolar['Data'].max().date()}")
            print(f"\nÚltima cotação:")
            print(f"• Data: {df_dolar['Data'].iloc[-1].date()}")
            print(f"• Compra: R${df_dolar['Compra (R$)'].iloc[-1]:.4f}")
            print(f"• Venda: R${df_dolar['Venda (R$)'].iloc[-1]:.4f}")
            
            print(f"\nEstatísticas:")
            for k, v in stats.items():
                print(f"• {k}: R${v:.4f}" if isinstance(v, float) else f"• {k}: {v}")
            
            # 6. Mostrar últimos registros
            if len(df_dolar) > 5:
                print("\nÚltimas 5 cotações:")
                print(df_dolar[['Data', 'Compra (R$)', 'Venda (R$)']].tail(5).to_string(index=False))
            
            print(f"\nArquivos salvos em: {output_dir.resolve()}")
            
            # 7. Opção de enviar por email
            enviar_email = input("\nDeseja enviar por email? (s/n): ").lower() == 's'
            
            if enviar_email:
                receiver = input("Digite o email do destinatário: ")
                subject = f"Cotação do Dólar - Atualizado em {datetime.now().strftime('%d/%m/%Y')}"
                
                body = f"""
                <h2>Relatório de Cotações do Dólar</h2>
                <p>Período: {df_dolar['Data'].min().date()} a {df_dolar['Data'].max().date()}</p>
                <p>Última cotação: R${df_dolar['Compra (R$)'].iloc[-1]:.4f} (compra)</p>
                <p>Variação: {stats['Variação Total']:.4f} no período</p>
                <p>Arquivos anexados:</p>
                <ul>
                    <li>Planilha completa com cotações</li>
                    <li>Gráficos de variação</li>
                </ul>
                """
                
                send_email(
                    receiver_email=receiver,
                    subject=subject,
                    body=body,
                    attachments=[excel_path, graph_path, comp_venda_path]
                )
        
        else:
            print("\nFalha ao obter dados. Verifique:")
            print("- Sua conexão com a internet")
            print("- Se a API do Banco Central está disponível")
            print("- O formato da resposta da API pode ter mudado")
            
    except Exception as e:
        print(f"\nErro inesperado: {str(e)}", file=sys.stderr)
        sys.exit(1)