"""Cadastro e manutenção dos usuários do dashboard."""
import datetime

import streamlit as st

from data_collection.storage import create_user, delete_user, load_metadata, update_user
from frontend.ui_components import inject_global_css

st.set_page_config(page_title="Usuários | Skoob Dashboard", page_icon="👥")
inject_global_css()


def format_updated_at(value: str | None) -> str:
    if not value:
        return "-"
    try:
        parsed = datetime.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime.timezone.utc)
        local_time = parsed.astimezone(datetime.timezone(datetime.timedelta(hours=-3)))
        return local_time.strftime("%d/%m/%Y %H:%M:%S")
    except ValueError:
        return value

with st.sidebar:
    st.header("👥 Gerenciamento de usuários")
    st.page_link(
        "load_data.py",
        label="Dashboard",
        icon="📚",
        use_container_width=True,
    )
    st.markdown("---")

st.title("👥 Usuários")
st.caption("Cadastre os usuários que poderão ser selecionados na dashboard.")

metadata = load_metadata()
users = metadata.get("users", {})

st.markdown("### Adicionar usuário")
with st.form("add_user_form", clear_on_submit=True):
    new_user_id = st.text_input("ID do usuário")
    new_user_name = st.text_input("Nome")
    add_user = st.form_submit_button("Adicionar usuário", use_container_width=True)

if add_user:
    try:
        create_user(new_user_id, new_user_name)
        st.success("Usuário adicionado.")
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))

st.divider()
st.markdown("### Usuários cadastrados")

if not users:
    st.info("Nenhum usuário cadastrado.")
else:
    rows = [
        {
            "Nome": user_data.get("name", user_id),
            "ID": user_id,
            "Status": user_data.get("status") or "-",
            "Atualizado em": format_updated_at(user_data.get("updated_at")),
        }
        for user_id, user_data in sorted(users.items())
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    user_ids = sorted(users)
    selected_user = st.selectbox(
        "Usuário para editar ou excluir",
        user_ids,
        format_func=lambda user_id: f"{users[user_id].get('name', user_id)} ({user_id})",
    )

    st.markdown("### Editar usuário")
    with st.form("edit_user_form"):
        edited_name = st.text_input(
            "Nome",
            value=users[selected_user].get("name", selected_user),
        )
        save_user = st.form_submit_button("Salvar alterações", use_container_width=True)

    if save_user:
        try:
            update_user(selected_user, edited_name)
            st.success("Usuário atualizado.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    st.markdown("### Excluir usuário")
    st.warning("A exclusão remove o cadastro e os dados salvos desse usuário.")
    if st.button("Excluir usuário", type="secondary"):
        delete_user(selected_user)
        st.success("Usuário excluído.")
        st.rerun()
