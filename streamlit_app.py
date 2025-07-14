# Importar pacotes Python
import streamlit as st
from snowflake.snowpark.functions import col
import json # Importar json para lidar com Secrets
import requests # Adicionar importação da biblioteca requests

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
# Configuração de conexão para ambiente SnIS
# Forçando a leitura das credenciais das Secrets diretamente
try:
    secrets_dict = st.secrets["connections"]["snowflake"]
    session = st.connection("snowflake", type="sql", **secrets_dict).session()
except AttributeError:
    # Fallback para ambiente SiS se st.secrets não estiver disponível (para teste local)
    st.warning("Running in SiS environment or secrets not fully configured. Using get_active_session().")
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()


my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'))

# Comentar a linha que mostra o DataFrame na página
# st.dataframe(data=my_dataframe, use_container_width=True)

# Adicionar o multiselect
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe,
    max_selections=5 # Limita a seleção a 5 ingredientes
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

# Nova seção para exibir informações nutricionais do smoothiefroot
smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")
smoothiefroot_json = smoothiefroot_response.json() # NOVO: Converte a resposta para JSON
st.json(smoothiefroot_json) # NOVO: Exibe o JSON de forma formatada
