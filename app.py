import streamlit as st
import hashlib
import os
import time
import pandas as pd
from datetime import datetime
from cryptography.fernet import Fernet

st.set_page_config(
    page_title="Blockchain E-Discovery Portal", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- NEW: CATCH NEXT PAGE BEFORE MENU RENDERS ---
# This safely updates the menu before it gets drawn on the screen
if "next_page" in st.session_state:
    st.session_state.workflow_nav = st.session_state.next_page
    del st.session_state.next_page
# ------------------------------------------------

STORAGE_DIR = "offchain_encrypted_storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

if "fernet_key" not in st.session_state:
    st.session_state.fernet_key = Fernet.generate_key()
cipher = Fernet(st.session_state.fernet_key)

if "blockchain_ledger" not in st.session_state:
    st.session_state.blockchain_ledger = []

if "evidence_db" not in st.session_state:
    st.session_state.evidence_db = {}

if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

def generate_sha256(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def commit_block(action: str, evidence_id: str, actor: str, tx_details: dict):
    block_index = len(st.session_state.blockchain_ledger) + 1
    prev_hash = st.session_state.blockchain_ledger[-1]["block_hash"] if st.session_state.blockchain_ledger else "0" * 64
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    block_data = f"{block_index}{action}{evidence_id}{actor}{timestamp}{prev_hash}"
    block_hash = hashlib.sha256(block_data.encode()).hexdigest()
    
    block = {
        "block_index": block_index,
        "timestamp": timestamp,
        "action": action,
        "evidence_id": evidence_id,
        "actor": actor,
        "details": tx_details,
        "previous_hash": prev_hash,
        "block_hash": block_hash
    }
    st.session_state.blockchain_ledger.append(block)
    return block

st.sidebar.title("⚖️ LexLedger")
st.sidebar.caption("Permissioned E-Discovery & Chain of Custody Portal")

if st.session_state.authenticated_user:
    st.sidebar.success(f"User: **{st.session_state.authenticated_user['name']}**")
    st.sidebar.caption(f"Role: {st.session_state.authenticated_user['role']}")
    st.sidebar.caption(f"Address: `{st.session_state.authenticated_user['address'][:10]}...`")
    if st.sidebar.button("Log Out"):
        st.session_state.authenticated_user = None
        st.rerun()

menu = [
    "1. Authentication (T1)",
    "2. Evidence Registration (T2 & T3)",
    "3. Integrity Verification (T4)",
    "4. Custody Transfer (T6 & T7)",
    "5. Evidence Search & Retrieval (T8)",
    "6. Blockchain Audit Trail (T9 & T10)"
]

choice = st.sidebar.radio("Evaluation Workflow Navigation", menu, key="workflow_nav")

if choice == "1. Authentication (T1)":
    st.header("Task T1: User Authentication & Access Control")
    st.info("Log in with pre-configured legal practitioner test accounts to access restricted features.")
    
    users = {
        "Kwame Mensah (Lead Counsel)": {"role": "Legal Practitioner (LP)", "address": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"},
        "Abena Osei (Evidence Custodian)": {"role": "Records Manager (RM)", "address": "0x2546BcD3c84621e976D8185a91A922aC76D4f705"},
        "Dr. Eric Adongo (Forensic Auditor)": {"role": "Cybersecurity Specialist (CY)", "address": "0xBcd4042DE499D14e55001CAbB24a81d524842741"}
    }
    
    selected_user = st.selectbox("Select Test Account", list(users.keys()))
    if st.button("Log In & Authenticate"):
        st.session_state.authenticated_user = {
            "name": selected_user,
            "role": users[selected_user]["role"],
            "address": users[selected_user]["address"]
        }
        st.success(f"Authenticated successfully as {selected_user}!")
        st.toast(f"Welcome back, {selected_user}!", icon="✅")
        
        # TRANSITION FIX: Use the next_page staging variable
        time.sleep(1.5) 
        st.session_state.next_page = menu[1]
        st.rerun()

if not st.session_state.authenticated_user and choice != "1. Authentication (T1)":
    st.warning("⚠️ Please complete Task T1 (Authentication) in the sidebar to proceed.")
    st.stop()

elif choice == "2. Evidence Registration (T2 & T3)":
    st.header("Tasks T2 & T3: Evidence Registration & SHA-256 Hashing")
    st.write("Register controlled test evidence. The file will be encrypted off-chain while its SHA-256 fingerprint is committed on-chain.")
    
    col1, col2 = st.columns(2)
    with col1:
        suit_number = st.text_input("Court Suit Number", "SUIT/ACC/2026/089")
        evidence_id = st.text_input("Unique Evidence ID", f"EVID-{int(time.time())}")
        description = st.text_area("Evidence Description", "Digital correspondence PDF extracted from drive.")
    
    with col2:
        uploaded_file = st.file_uploader("Upload Controlled Test File", type=["pdf", "docx", "txt", "png", "jpg"])
    
    if uploaded_file and st.button("Register & Commit to Blockchain"):
        file_bytes = uploaded_file.read()
        sha256_hash = generate_sha256(file_bytes)
        
        encrypted_bytes = cipher.encrypt(file_bytes)
        enc_filename = f"{evidence_id}_{uploaded_file.name}.enc"
        enc_path = os.path.join(STORAGE_DIR, enc_filename)
        with open(enc_path, "wb") as f:
            f.write(encrypted_bytes)
            
        st.session_state.evidence_db[evidence_id] = {
            "suit_number": suit_number,
            "filename": uploaded_file.name,
            "sha256_hash": sha256_hash,
            "enc_path": enc_path,
            "current_custodian": st.session_state.authenticated_user["address"],
            "registered_by": st.session_state.authenticated_user["name"],
            "description": description
        }
        
        block = commit_block(
            action="EVIDENCE_REGISTERED",
            evidence_id=evidence_id,
            actor=st.session_state.authenticated_user["address"],
            tx_details={"suit": suit_number, "hash": sha256_hash, "file": uploaded_file.name}
        )
        
        st.success("✅ Evidence Registered Successfully!")
        st.json({
            "Evidence ID": evidence_id,
            "SHA-256 Cryptographic Hash": sha256_hash,
            "Off-Chain Encrypted Location": enc_path,
            "Blockchain Transaction Block": block["block_index"],
            "Block Hash": block["block_hash"]
        })
        
        # TRANSITION FIX
        time.sleep(3)
        st.session_state.next_page = menu[2]
        st.rerun()

elif choice == "3. Integrity Verification (T4)":
    st.header("Task T4: Cryptographic Evidence Integrity Verification")
    st.write("Verify whether a file's content has been altered by comparing its live hash against the immutable ledger record.")
    
    if not st.session_state.evidence_db:
        st.info("No evidence registered yet. Please complete Task T2 first.")
    else:
        ev_id = st.selectbox("Select Evidence Record to Verify", list(st.session_state.evidence_db.keys()))
        target_record = st.session_state.evidence_db[ev_id]
        
        st.markdown(f"**Target SHA-256 Hash on Ledger:** `{target_record['sha256_hash']}`")
        verify_file = st.file_uploader("Re-upload File to Verify Integrity")
        
        if verify_file and st.button("Run Verification Check"):
            live_bytes = verify_file.read()
            live_hash = generate_sha256(live_bytes)
            
            if live_hash == target_record["sha256_hash"]:
                st.success("🟢 **INTEGRITY MATCH CONFIRMED**: File is authentic and un-tampered!")
                commit_block("INTEGRITY_VERIFIED_PASS", ev_id, st.session_state.authenticated_user["address"], {"result": "MATCH"})
                
                # TRANSITION FIX
                time.sleep(3)
                st.session_state.next_page = menu[3]
                st.rerun()
            else:
                st.error("🔴 **TAMPER WARNING**: Live file hash DOES NOT match the recorded blockchain ledger hash!")
                st.write(f"Live File Hash: `{live_hash}`")
                commit_block("INTEGRITY_VERIFIED_FAIL", ev_id, st.session_state.authenticated_user["address"], {"result": "MISMATCH", "live_hash": live_hash})

elif choice == "4. Custody Transfer (T6 & T7)":
    st.header("Tasks T6 & T7: Chain of Custody Transfer & History")
    
    if not st.session_state.evidence_db:
        st.info("No evidence records available.")
    else:
        ev_id = st.selectbox("Select Evidence Item", list(st.session_state.evidence_db.keys()))
        record = st.session_state.evidence_db[ev_id]
        
        st.markdown(f"**Current Custodian:** `{record['current_custodian']}`")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Execute Custody Transfer (T6)")
            new_custodian = st.text_input("New Custodian Address", "0x8626f69A4512D05D6132b3815049581781c1c1f5")
            notes = st.text_area("Transfer Reason / Notes", "Transferred to Registrar for Court Submission.")
            
            if st.button("Transfer Custody On-Chain"):
                record["current_custodian"] = new_custodian
                commit_block("CUSTODY_TRANSFERRED", ev_id, st.session_state.authenticated_user["address"], {"new_custodian": new_custodian, "notes": notes})
                st.success(f"Custody of {ev_id} transferred successfully!")
                
                # TRANSITION FIX
                time.sleep(2)
                st.session_state.next_page = menu[4]
                st.rerun()
                
        with col2:
            st.subheader("Custody History Ledger (T7)")
            history = [b for b in st.session_state.blockchain_ledger if b["evidence_id"] == ev_id]
            for h in history:
                st.markdown(f"**Block #{h['block_index']}** | `{h['timestamp']}`")
                st.caption(f"Action: {h['action']} | Actor: `{h['actor'][:10]}...`")
                st.json(h["details"])
                st.divider()

elif choice == "5. Evidence Search & Retrieval (T8)":
    st.header("Task T8: Evidence Search & Decryption")
    
    search_term = st.text_input("Search by Court Suit Number or Evidence ID")
    if st.session_state.evidence_db:
        for ev_id, data in st.session_state.evidence_db.items():
            if search_term.lower() in ev_id.lower() or search_term.lower() in data["suit_number"].lower() or not search_term:
                with st.expander(f"📌 {ev_id} — Suit: {data['suit_number']}"):
                    st.write(f"**Filename:** {data['filename']}")
                    st.write(f"**SHA-256 Hash:** `{data['sha256_hash']}`")
                    st.write(f"**Custodian:** `{data['current_custodian']}`")
                    
                    if os.path.exists(data["enc_path"]):
                        with open(data["enc_path"], "rb") as f:
                            enc_data = f.read()
                        decrypted_data = cipher.decrypt(enc_data)
                        st.download_button(
                            label=f"⬇️ Decrypt & Download {data['filename']}",
                            data=decrypted_data,
                            file_name=f"decrypted_{data['filename']}",
                            mime="application/octet-stream"
                        )

elif choice == "6. Blockchain Audit Trail (T9 & T10)":
    st.header("Tasks T9 & T10: Audit Log & Court Summary Report")
    
    st.subheader("System Block Ledger (T9)")
    if st.session_state.blockchain_ledger:
        df = pd.DataFrame(st.session_state.blockchain_ledger)
        st.dataframe(df[["block_index", "timestamp", "action", "evidence_id", "actor", "block_hash"]], use_container_width=True)
        
        st.subheader("Generate Audit Summary Report (T10)")
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Export Court-Ready Audit Trail (CSV)",
            data=csv_data,
            file_name=f"audit_trail_report_{int(time.time())}.csv",
            mime="text/csv"
        )
    else:
        st.info("Blockchain ledger is currently empty.")
