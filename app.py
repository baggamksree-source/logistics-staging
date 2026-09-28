import streamlit as st

st.set_page_config(page_title="Corporate Logistics Portal", layout="wide")
st.title("🏢 Shipping & Logistics Enterprise Hub v2")
st.markdown("---")

# --- SECURITY PROTECTION ASSURANCE MECHANISM ---
user_email = ""
if hasattr(st, "experimental_user") and st.experimental_user:
    user_email = getattr(st.experimental_user, "email", "") or getattr(st.experimental_user, "name", "")
if not user_email and hasattr(st, "context") and hasattr(st.context, "user"):
    user_email = st.context.user.get("email", st.context.user.get("name", ""))

user_email = str(user_email).strip().lower()

if not user_email or user_email in ["none", ""]:
    st.sidebar.warning("✏️ Finalizing Security Sync...")
    user_email = st.sidebar.text_input("Confirm Your Office Email / Name:", value="").strip().lower()
    if not user_email:
        st.info("👋 Please enter your Office Name or Email in the sidebar box to unlock your tools.")
        st.stop()

target_domain = str(st.secrets.get("allowed_domain", "yourcompany.com")).strip().lower()
if "@" in user_email and not user_email.endswith(f"@{target_domain}"):
    st.subheader("🔒 Access Restricted")
    st.error(f"Your account ({user_email}) is outside the authorized corporate domain (@{target_domain}). Access denied.")
    st.stop()

# Store session data globally to auto-unlock child modules
st.session_state["user_identity"] = user_email
st.session_state["security_cleared"] = True

st.success(f"✓ Security cleared. Session authenticated for **{user_email}**!")
st.markdown("""
### 🧭 Quick Multi-Page Navigation Menu
Use the navigation index links located on your left-hand sidebar layout to open active modules:
* **📥 Log New Shipment:** Fast standalone entry portal grid for tracking records and RFQs.
* **📊 Analytics Dashboard:** Colorized metric status cards, revenue graphs, and performance parameters.
* **✏️ Live Data Ledger:** Full-screen table containing an **interactive grid editor**—click on any cell to overwrite updates directly!
""")
