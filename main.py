# Bibliotecas necessárias:
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, jsonify, request
import threading
import streamlit as st
import requests
import time
import matplotlib.dates as mdates  # Importar para formatação das datas:

# Carregamento de Dados:
class DataHandler:
    def __init__(self, file_path=None):
        self.file_path = file_path

    def load_data(self):
        if self.file_path is None:
            raise ValueError("O caminho para o arquivo Excel não está correto!")

        try:
            # Carregar o arquivo Excel declarado no caminho:
            data = pd.read_excel(self.file_path)

            # Garantir que a coluna "Data" seja do tipo datetime:
            data['Data'] = pd.to_datetime(data['Data'], format='%d/%m/%Y')

            print("Dados carregados com sucesso do arquivo Excel:")
            print(data.head())  # Imprime as primeiras linhas dos dados para debug:

            return data
        except Exception as e:
            raise ValueError(f"Erro ao carregar os dados do arquivo Excel: {e}")

    def get_data(self):
        """Retorna o DataFrame de dados mais atualizados (sempre recarrega do Excel)."""
        print("Recarregando os dados...")
        return self.load_data()  # Recarrega os dados sempre que necessário (caso a base seja modificada):

# Análises Estatísticas:
class Statistics:
    def __init__(self, data_handler):
        self.data_handler = data_handler

    def get_basic_statistics(self):
        """Calcula estatísticas básicas (média, mediana, desvio padrão) a partir dos dados mais recentes."""
        data = self.data_handler.get_data()  # Recarregar os dados mais recentes diretamente do arquivo Excel:

        print("Calculando estatísticas com os dados mais recentes:")
        print(data.head())  # Verificando os dados que estão sendo usados para calcular as estatísticas:

        # Filtrar apenas as colunas numéricas relevantes:
        relevant_columns = ['casosAcumulados', 'casosNovos', 'obitosAcumulados', 'obitosNovos']
        numeric_data = data[relevant_columns]

        # Calcular as estatísticas:
        stats = {
            'mean': numeric_data.mean().to_dict(),  # Média (mean): valor médio dos dados.
            'median': numeric_data.median().to_dict(),
            # Mediana (median): valor do meio (ou a média dos dois valores centrais) dos dados ordenados.
            'std': numeric_data.std().to_dict()
            # Desvio padrão (std): medida de quão dispersos os dados estão em relação à média.
        }
        return stats

# Visualização de Dados:
class Visualization:
    def __init__(self, data):
        self.data = data

    def plot_histogram(self, column, bins=30):
        """Gera um histograma para a coluna especificada."""
        if column in self.data.select_dtypes(include=['number']).columns:
            plt.figure(figsize=(8, 6))
            ax = sns.histplot(self.data[column], kde=True, bins=bins)
            plt.title(f'Histograma de {column}')
            plt.xlabel(column)
            plt.ylabel('Frequência')

            # Ajustar as datas na parte inferior (eixo X) para o formato brasileiro:
            plt.xticks(rotation=45)
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))  # Formatação da data:

            # Adicionar valores no topo de cada barra com separador de milhar:
            for p in ax.patches:
                ax.annotate(f'{p.get_height():,.0f}',
                            (p.get_x() + p.get_width() / 2., p.get_height()),
                            ha='center', va='center',
                            fontsize=10, color='black',
                            xytext=(0, 5), textcoords='offset points')

            st.pyplot(plt)
        else:
            st.warning(f'A coluna "{column}" não é numérica.')

    def plot_area(self, col1, col2):
        """Gera um gráfico de área entre duas colunas com cores distintas para cada dado."""
        if col1 in self.data.select_dtypes(include=['number']).columns and col2 in self.data.select_dtypes(
                include=['number']).columns:
            plt.figure(figsize=(10, 6))

            # Plotando a área para 'casosNovos' com cor azul:
            area1 = plt.fill_between(self.data['Data'], self.data[col1], color='blue', alpha=0.5, label='Casos Novos')

            # Plotando a área para 'obitosNovos' com cor vermelha:
            area2 = plt.fill_between(self.data['Data'], self.data[col2], color='red', alpha=0.5, label='Óbitos Novos')

            plt.title(f'Gráfico de Área entre {col1} e {col2}')
            plt.xlabel('Data')
            plt.ylabel('Quantidade')

            # Ajustar as datas na parte inferior (eixo X) para o formato brasileiro:
            plt.xticks(rotation=45)
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))  # Formatação da data

            plt.legend(title='Tipo de Dado')

            # Adicionar valores nas áreas com separador de milhar:
            for i, val in enumerate(self.data[col1]):
                plt.text(self.data['Data'].iloc[i], val, f'{val:,.0f}', ha='center', va='bottom', fontsize=8,
                         color='blue')
            for i, val in enumerate(self.data[col2]):
                plt.text(self.data['Data'].iloc[i], val, f'{val:,.0f}', ha='center', va='bottom', fontsize=8,
                         color='red')

            st.pyplot(plt)
        else:
            st.warning(f'Uma ou ambas as colunas "{col1}" e "{col2}" não são numéricas.')

    def plot_line_comparison(self):
        """Gera um gráfico de linhas para comparar a evolução dos valores do Brasil ao longo do tempo"""
        # Filtrar os dados:
        brazil_data = self.data[self.data['País'] == 'Brasil']

        # Plotando o gráfico de linhas comparando 'casosAcumulados' ao longo do tempo para o Brasil:
        plt.figure(figsize=(10, 6))

        # País - Brasil:
        line = sns.lineplot(x='Data', y='casosAcumulados', data=brazil_data, label='Brasil', color='blue', marker='o')

        # Adicionando títulos e labels aos gráficos:
        plt.title('Evolução de Casos Acumulados no Brasil', fontsize=14)
        plt.xlabel('Data', fontsize=12)
        plt.ylabel('Casos Acumulados', fontsize=12)

        # Ajustar as datas na parte inferior (eixo X) para o formato brasileiro:
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))  # Formatação da data

        plt.legend(title='País')

        # Adicionar valores nas linhas com separador de milhar:
        for x, y in zip(brazil_data['Data'], brazil_data['casosAcumulados']):
            plt.text(x, y, f'{y:,.0f}', ha='center', va='bottom', fontsize=8, color='blue')

        # Exibir o gráfico no Streamlit: Comando streamlit run main.py
        st.pyplot(plt)

    def plot_line_deaths(self):
        """Gera um gráfico de linha para a evolução de óbitos acumulados no Brasil."""
        # Filtrar os dados:
        brazil_data = self.data[self.data['País'] == 'Brasil']

        # Plotando o gráfico de linhas comparando 'obitosAcumulados' ao longo do tempo para o Brasil:
        plt.figure(figsize=(10, 6))

        # País - Brasil:
        line = sns.lineplot(x='Data', y='obitosAcumulados', data=brazil_data, label='Óbitos Acumulados', color='red',
                            marker='o')

        # Adicionando títulos e labels ao gráfico:
        plt.title('Evolução de Óbitos Acumulados no Brasil', fontsize=14)
        plt.xlabel('Data', fontsize=12)
        plt.ylabel('Óbitos Acumulados', fontsize=12)

        # Ajustar as datas na parte inferior (eixo X) para o formato brasileiro:
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))  # Formatação da data

        plt.legend(title='País')

        # Adicionar valores nas linhas com separador de milhar:
        for x, y in zip(brazil_data['Data'], brazil_data['obitosAcumulados']):
            plt.text(x, y, f'{y:,.0f}', ha='center', va='bottom', fontsize=8, color='red')

        # Exibir o gráfico no Streamlit
        st.pyplot(plt)


# API Flask:
app = Flask(__name__)

# Caminho para o arquivo Excel com os dados:
file_path = "COVID_19_2024.xlsx"

# Instanciando as classes:
data_handler = DataHandler(file_path=file_path)
statistics = Statistics(data_handler)


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """API Flask que retorna as estatísticas básicas: Média, Mediana e STD."""
    stats = statistics.get_basic_statistics()
    return jsonify(stats)


@app.route('/api/data', methods=['GET'])
def get_data():
    """Retorna os dados mais recentes."""
    data = data_handler.get_data()
    print(f"Dados mais recentes carregados: {data.head()}")  # Log para verificar se os dados estão sendo recarregados
    return jsonify(data.to_dict(orient='records'))


# Função para exibir barra de carregamento:
def loading_animation():
    progress = st.progress(0)
    for i in range(100):
        time.sleep(0.05)  # Simula o tempo de processamento
        progress.progress(i + 1)


# Função para exibir nossos nomes e as informações do projeto:
def show_author_names():
    st.markdown("Projeto desenvolvido por:")
    st.markdown("Rayane Sant'Anna e Naiá Duhau")
    st.markdown("Matrícula - Rayane: 2024.0502.8821")
    st.markdown("Email: [raymscs@hotmail.com](mailto:raymscs@hotmail.com)")
    st.markdown("Matrícula - Naiá: 2024.0500.0791")
    st.markdown("Email: [naiaduhau@gmail.com](mailto:naiaduhau@gmail.com)")
    st.markdown("Este projeto tem como objetivo analisar dados sobre a COVID-19 de Julho até início de Novembro de 2024.")

    st.markdown("---")  # Separação:

    # Informações da Avaliação:
    st.markdown("Informações Complementares da Avaliação Final:")
    st.markdown("Disciplina: Linguagem Python")
    st.markdown("Professor: Raphael Mauricio Sanches de Jesus")
    st.markdown("Email: [raphael.jesus@estacio.br](mailto:raphael.jesus@estacio.br)")
    st.markdown("Período: Pós-Graduação")
    st.markdown("Data de Entrega: 23/11/2024")


# Função para rodar o Streamlit:
def run_streamlit():
    # Interface Streamlit
    time.sleep(2)  # Delay para garantir que o Flask inicie primeiro:
    st.title("Análise de Dados com Streamlit:")

    # Exibir os nomes dos autores e informações adicionais:
    show_author_names()

    # Exibir barra de carregamento:
    loading_animation()

    # Carregar os dados:
    data = data_handler.get_data()

    # Formatar a coluna 'Data' no formato brasileiro para a tabela (mas não modificar o tipo datetime para plotagens):
    data['dataInformação'] = data['Data'].dt.strftime('%d/%m/%Y')  # Modificado o nome para 'dataInformação':

    # Remover a coluna original 'Data' e exibir apenas 'dataInformação' na tabela do Streamlit:
    data_to_display = data.drop(columns=['Data'])

    # Função para formatar os valores numéricos:
    def format_numeric(x):
        if isinstance(x, (int, float)):  # Verifica se o valor é numérico
            # Formatar com ponto para decimais e vírgula para milhar
            return f"{x:,.0f}".replace(',', '_').replace('.', ',').replace('_', '.')
        return x  # Se não for numérico, retorna o valor sem alteração

    # Aplicar a formatação apenas às colunas numéricas:
    data_to_display = data_to_display.applymap(format_numeric)

    # Exibir a tabela com barra de rolagem (apenas com a coluna 'Datas' visível):
    st.dataframe(data_to_display)  # Utilizando st.dataframe ao invés de st.write:

    # Exibir estatísticas básicas da API Flask:
    response = requests.get('http://127.0.0.1:5000/api/statistics')
    if response.status_code == 200:
        stats = response.json()
        st.subheader("Estatísticas Básicas")
        st.write(stats)

    # Visualizações:
    st.subheader("Gráfico de Área - Casos Novos x Óbitos Novos:")
    visualization = Visualization(data)
    visualization.plot_area('casosNovos', 'obitosNovos')

    # Exibir o gráfico de comparação de evolução dos casos acumulados:
    st.subheader("Evolução de Casos Acumulados no Brasil:")
    visualization.plot_line_comparison()

    # Exibir o gráfico de evolução de óbitos acumulados:
    st.subheader("Evolução de Óbitos Acumulados no Brasil:")
    visualization.plot_line_deaths()


def run_flask():
    app.run(debug=False, use_reloader=False)


if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    run_streamlit()
