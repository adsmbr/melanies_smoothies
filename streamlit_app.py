# Importar pacotes Python
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas
import json

# Título e descrição do app
st.title("Customize Your Smoothie! 🥤")
st.write("Choose the fruits you want in your custom Smoothie!")

# Campo para o nome do cliente no pedido
name_on_order = st.text_input("Name on Smoothie:")
st.write('The name on your Smoothie will be:', name_on_order)

# Conexão com o Snowflake
try:
    conn = st.connection("snowflake")
    session = conn.session()
except Exception as e:
    st.error(f"Erro ao conectar ao Snowflake: {e}")
    st.stop()

# Busca as colunas FRUIT_NAME e SEARCH_ON da tabela de frutas
try:
    my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
    pd_df = my_dataframe.to_pandas()
    fruit_list = pd_df['FRUIT_NAME'].tolist()
except Exception as e:
    st.error(f"Erro ao carregar dados de frutas do Snowflake: {e}")
    st.stop()

# Componente de seleção de ingredientes
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    fruit_list,
    max_selections=5
)

# Executar lógica se houver frutas selecionadas
if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Buscar o nome correto na coluna search_on
        try:
            search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        except KeyError:
            st.error(f"Erro: Coluna 'SEARCH_ON' não encontrada no DataFrame.")
            st.stop()
        except IndexError:
            st.error(f"Erro: Fruta '{fruit_chosen}' não encontrada para 'SEARCH_ON'.")
            st.stop()

        st.subheader(fruit_chosen + ' Nutrition Information')

        # Corrigir formatação para a URL da API
        query_fruit = search_on.strip().lower().replace(" ", "")

        # Chamada da API Fruityvice
        try:
            fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{query_fruit}")
            if fruityvice_response.status_code == 404:
                st.warning(f"'{fruit_chosen}' não está disponível na API Fruityvice.")
                continue

            fruityvice_response.raise_for_status()
            st.dataframe(data=fruityvice_response.json(), use_container_width=True)
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao buscar dados nutricionais para {fruit_chosen}: {e}")
        except json.JSONDecodeError:
            st.error(f"Erro ao interpretar a resposta da API para {fruit_chosen}.")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado com {fruit_chosen}: {e}")

    # Inserir pedido na tabela ORDERS
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES ('{ingredients_string.strip()}', '{name_on_order}')
    """

    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        try:
            conn.query(my_insert_stmt)
            st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
        except Exception as e:
            st.error(f"Erro ao inserir pedido: {e}")
            st.write("Instrução SQL:", my_insert_stmt)
else:
    st.write("Selecione frutas para ver suas informações nutricionais!")
