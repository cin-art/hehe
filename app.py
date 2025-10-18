
import streamlit as st
import pandas as pd
import pickle, io, os
import numpy as np

st.set_page_config(page_title="Partners-Score (MVP)", layout="wide")

st.title("Partners-Score - Credit Scoring MVP")
st.markdown("""Upload a CSV with PME features to receive a credit score and a short analysis.
Columns expected: `faturamento_mensal, tempo_operacao_meses, inadimplencia_pct, parceladas_pct, crescimento_3m, ticket_medio, chargebacks_pct, numero_clientes`""")

model_file = "pipeline_model.pkl"

@st.cache_data
def load_model():
    with open(model_file, "rb") as f:
        obj = pickle.load(f)
    return obj

if not os.path.exists(model_file):
    st.error("Model file not found on the server. Please ensure pipeline_model.pkl is in the app folder.")
else:
    obj = load_model()
    pipeline = obj["pipeline"]
    features = obj["features"]

    uploaded = st.file_uploader("Upload CSV", type=["csv","xlsx"])
    col1, col2 = st.columns([2,1])

    if uploaded is not None:
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
        except Exception as e:
            st.error("Failed to read file: " + str(e))
            st.stop()

        st.write("Preview of uploaded data (first 10 rows):")
        st.dataframe(df.head(10))

        missing = [c for c in features if c not in df.columns]
        if missing:
            st.warning(f"The uploaded file is missing columns: {missing}. Please follow the template.")
            st.markdown("Download template below:")
            with open("sample_template.csv", "rb") as f:
                st.download_button("Download CSV template", data=f, file_name="sample_template.csv", mime='text/csv')

        else:
            X = df[features].copy()
            # Fill na with median
            X = X.fillna(X.median())
            proba = pipeline.predict_proba(X)[:,1]
            df["score_raw"] = (1 - proba) * 100  # map default probability -> credit score (higher better)
            df["decision"] = df["score_raw"].apply(lambda s: "approve" if s>=60 else ("review" if s>=40 else "reject"))
            st.success("Scoring complete. See results below.")

            st.write(df[["company_id","score_raw","decision"] + features].head(20))

            # Show distribution
            st.subheader("Score distribution (preview)")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
            ax.hist(df["score_raw"], bins=20)
            ax.set_xlabel("Score (0-100)")
            ax.set_ylabel("Count")
            st.pyplot(fig)

            # Show feature importance (model-level)
            st.subheader("Model feature importances")
            try:
                importances = pipeline.named_steps["gb"].feature_importances_
                imp_df = pd.DataFrame({"feature": features, "importance": importances}).sort_values("importance", ascending=False)
                st.table(imp_df)
            except Exception:
                st.info("Feature importances not available for this model.")

            # Individual company analysis selection
            st.subheader("Individual analysis and PDF report")
            comp = st.selectbox("Choose company_id to view report", df["company_id"].tolist())
            row = df[df["company_id"] == comp].iloc[0]

            st.write("Score:", round(row["score_raw"],2))
            st.write("Decision:", row["decision"])
            st.markdown("**Top factors (heuristic):**")
            # Simple heuristic explanation: show top 3 features that push towards higher default probability
            diffs = {}
            for f in features:
                try:
                    val = float(row[f])
                except Exception:
                    val = None
                diffs[f] = val if val is not None else 0

            explained = sorted(features, key=lambda x: abs(diffs[x] - df[x].median()), reverse=True)[:3]
            for ef in explained:
                st.write(f"- **{ef}**: value = {row[ef]} (median in file = {df[ef].median():.3g})")

            # PDF download for selected company (simple text report)
            from fpdf import FPDF
            pdf_buf = io.BytesIO()
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, "Partners-Score - Individual Analysis", ln=1)
            pdf.cell(0, 8, f"Company ID: {row['company_id']}", ln=1)
            pdf.cell(0, 8, f"Score: {round(row['score_raw'],2)}", ln=1)
            pdf.cell(0, 8, f"Decision: {row['decision']}", ln=1)
            pdf.ln(4)
            pdf.multi_cell(0, 6, "Top factors:")
            for ef in explained:
                pdf.multi_cell(0, 6, f"- {ef}: {row[ef]} (median = {df[ef].median():.3g})")
            pdf.output(pdf_buf)
            pdf_buf.seek(0)
            st.download_button("Download individual PDF report", data=pdf_buf, file_name=f"report_{row['company_id']}.pdf", mime="application/pdf")

    else:
        st.info("Upload a CSV to get started. You can download a template for reference.")
        with open("sample_template.csv", "rb") as f:
            st.download_button("Download CSV template", data=f, file_name="sample_template.csv", mime='text/csv')
