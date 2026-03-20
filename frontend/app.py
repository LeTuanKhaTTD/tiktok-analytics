import requests
import streamlit as st
import pandas as pd

st.set_page_config(page_title="TVU Analytics Platform", page_icon="📈", layout="wide")

API_BASE_URL = st.secrets.get("API_BASE_URL", "http://127.0.0.1:8000")


def _headers() -> dict:
    token = st.session_state.get("access_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _request(method: str, path: str, **kwargs):
    url = f"{API_BASE_URL}{path}"
    return requests.request(method, url, timeout=30, **kwargs)


def _auth_view():
    st.title("TVU TikTok Analytics Platform")
    tab_login, tab_register = st.tabs(["Đăng nhập", "Đăng ký"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Mật khẩu", type="password", key="login_password")
        if st.button("Đăng nhập", use_container_width=True):
            resp = _request("POST", "/api/auth/login", json={"email": email, "password": password})
            if resp.ok:
                data = resp.json()
                st.session_state["access_token"] = data["access_token"]
                st.session_state["user_name"] = data["full_name"]
                st.success("Đăng nhập thành công")
                st.rerun()
            else:
                st.error(resp.text)

    with tab_register:
        full_name = st.text_input("Họ tên", key="reg_name")
        email = st.text_input("Email ", key="reg_email")
        password = st.text_input("Mật khẩu ", type="password", key="reg_password")
        if st.button("Đăng ký", use_container_width=True):
            resp = _request(
                "POST",
                "/api/auth/register",
                json={"email": email, "full_name": full_name, "password": password},
            )
            if resp.ok:
                data = resp.json()
                st.session_state["access_token"] = data["access_token"]
                st.session_state["user_name"] = data["full_name"]
                st.success("Đăng ký thành công")
                st.rerun()
            else:
                st.error(resp.text)


def _dashboard_view():
    st.header("Dashboard phân tích")
    text = st.text_area("Nhập nội dung cần phân tích sentiment", height=120)
    if st.button("Phân tích bằng PhoBERT API", type="primary"):
        if not text.strip():
            st.warning("Vui lòng nhập nội dung")
        else:
            resp = _request("POST", "/api/analysis/text", json={"text": text}, headers=_headers())
            if resp.ok:
                data = resp.json()
                c1, c2, c3 = st.columns(3)
                c1.metric("Sentiment", data["sentiment"])
                c2.metric("Confidence", f"{data['confidence']:.2%}")
                c3.metric("Model", data["model"])
            else:
                st.error(resp.text)

    st.subheader("Kết quả gần đây")
    history = _request("GET", "/api/analysis/history", headers=_headers())
    if history.ok:
        items = history.json().get("items", [])
        if items:
            st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có dữ liệu phân tích")
    else:
        st.error(history.text)


def _report_history_view():
    st.header("Lịch sử báo cáo")
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Tạo báo cáo từ dữ liệu gần nhất", use_container_width=True):
            resp = _request("POST", "/api/reports/create-latest", headers=_headers())
            if resp.ok:
                st.success("Đã tạo báo cáo")
                st.rerun()
            else:
                st.error(resp.text)

    res = _request("GET", "/api/reports/history", headers=_headers())
    if not res.ok:
        st.error(res.text)
        return

    items = res.json().get("items", [])
    if not items:
        st.info("Chưa có lịch sử báo cáo")
        return

    df = pd.DataFrame(items)
    st.dataframe(df, use_container_width=True, hide_index=True)


if "access_token" not in st.session_state:
    _auth_view()
else:
    with st.sidebar:
        st.write(f"Xin chào, **{st.session_state.get('user_name', 'User')}**")
        page = st.radio("Điều hướng", ["Dashboard phân tích", "Lịch sử báo cáo"])
        if st.button("Đăng xuất", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    if page == "Dashboard phân tích":
        _dashboard_view()
    else:
        _report_history_view()
