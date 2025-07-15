# Importar pacotes Python 
import streamlit as st 
from snowflake.snowpark.functions import col 
import requests
import pandas

# Escrever diretamente no aplicativo 
st.title("Customize Your Smoothie! 🥤")
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
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Converte Snowpark -> Pandas para trabalhar no Streamlit
pd_df = my_dataframe.to_pandas()
fruit_list = pd_df['FRUIT_NAME'].tolist()

# Adicionar o multiselect com até 5 ingredientes
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    fruit_list,
    max_selections=5
)

# Se o usuário selecionou frutas, montamos a string e buscamos API
if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Busca o valor correto para a API na coluna SEARCH_ON
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]

        st.subheader(fruit_chosen + ' Nutrition Information')
        fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on)

        # Exibe o JSON formatado
        st.dataframe(data=fruityvice_response.json(), use_container_width=True)

    # Construir a instrução SQL INSERT
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders(ingredients, name_on_order)
        VALUES ('{ingredients_string}', '{name_on_order}')
    """

    # Botão para submeter o pedido
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        try:
            session.sql(my_insert_stmt).collect()  # ✅ Correto para executar SQL
            st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
        except Exception as e:
            st.error(f"Erro ao inserir pedido: {e}")
            st.write("Instrução SQL que causou o erro:", my_insert_stmt)
