# Importar pacotes Python
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas # NOVO: Importar pandas

# Escrever diretamente no aplicativo
st.title("Customize Your Smoothie!🥤")
st.write(
    """
    Choose the fruits you want in your custom Smoothie!
    """
)

# Adicionar o text_input para o nome do pedido
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Conexão com Snowflake
try:
    conn = st.connection("snowflake")
    session = conn.session()
except Exception as e:
    st.error(f"Erro ao conectar ao Snowflake: {e}")
    st.stop()

# Agora buscamos também SEARCH_ON para a integração com a API
try:
    my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
    pd_df = my_dataframe.to_pandas() # Converte Snowpark -> Pandas para trabalhar no Streamlit
    fruit_list = pd_df['FRUIT_NAME'].tolist()
except Exception as e:
    st.error(f"Erro ao carregar dados de frutas do Snowflake: {e}")
    st.stop()


# Adicionar o multiselect com até 5 ingredientes
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    fruit_list, # Usar fruit_list do Pandas DataFrame
    max_selections=5
)

# Se o usuário selecionou frutas, montamos a string e buscamos API
if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Busca o valor correto para a API na coluna SEARCH_ON
        # Certifique-se de que pd_df é um DataFrame Pandas e que 'SEARCH_ON' existe
        try:
            search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        except KeyError:
            st.error(f"Erro: Coluna 'SEARCH_ON' não encontrada no DataFrame. Verifique a tabela FRUIT_OPTIONS.")
            st.stop()
        except IndexError:
            st.error(f"Erro: Fruta '{fruit_chosen}' não encontrada no DataFrame para buscar 'SEARCH_ON'.")
            st.stop()

        st.subheader(fruit_chosen + ' Nutrition Information')
        try:
            fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on)
            fruityvice_response.raise_for_status() # Lança um erro para status de erro HTTP (4xx ou 5xx)
            st.dataframe(data=fruityvice_response.json(), use_container_width=True)
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao buscar dados nutricionais para {fruit_chosen}: {e}. Verifique a integração de acesso externo.")
        except json.JSONDecodeError:
            st.error(f"Erro ao decodificar JSON para {fruit_chosen}. Resposta: {fruityvice_response.text}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao buscar dados para {fruit_chosen}: {e}")

    # Construir a instrução SQL INSERT
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES ('{ingredients_string}', '{name_on_order}')
    """

    # Botão para submeter o pedido
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        try:
            conn.query(my_insert_stmt) # ✅ Correto para executar SQL
            st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
        except Exception as e:
            st.error(f"Erro ao inserir pedido: {e}")
            st.write("Instrução SQL que causou o erro:", my_insert_stmt)
else:
    st.write("Selecione frutas para ver suas informações nutricionais!")
