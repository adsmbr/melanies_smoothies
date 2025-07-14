# Importar pacotes Python
import streamlit as st
# REMOVIDO: from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col
import requests

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

# Adicionar a lista de opções de frutas, focando apenas na coluna FRUIT_NAME
# NOVO: Configuração de conexão para ambiente SnIS
cnx = st.connection("snowflake") # Adicionada linha de conexão
session = cnx.session() # Alterada linha de sessão

my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'))

# Comentar a linha que mostra o DataFrame na página
# st.dataframe(data=my_dataframe, use_container_width=True)

# Adicionar o multiselect
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe,
    max_selections=5 # NOVO: Limita a seleção a 5 ingredientes
)

# Adicionar lógica para limpar colchetes vazios
if ingredients_list:
    ingredients_string = ''
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
    
    # Construir uma instrução SQL INSERT
    my_insert_stmt = f"""insert into smoothies.public.orders(ingredients, name_on_order)
    values ('{ingredients_string}', '{name_on_order}')"""
    
    # Remover linhas de depuração (st.write(my_insert_stmt) e st.stop())
    # st.write(my_insert_stmt)
    # st.stop()

    time_to_insert = st.button('Submit Order')
    
    if time_to_insert:
        try:
            session.sql(my_insert_stmt).collect()
            st.success(f'Your Smoothie is ordered, {name_on_order}! 🎉')
        except Exception as e:
            st.error(f"Erro ao inserir pedido: {e}")
            st.write("Instrução SQL que causou o erro:", my_insert_stmt)
