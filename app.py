# app.py — FA Fin Apps · Inventory Aging Analytics
# Streamlit application entry point

import streamlit as st
import pandas as pd
from datetime import date
import traceback

from modules.translations import get_t
from modules.data_loader import load_file, load_file_raw, get_column_options
from modules.aging_engine import (
    get_default_buckets, calculate_aging,
    build_qty_summary, build_val_summary,
    build_warehouse_summary, build_batch_summary,
    build_summary_stats
)
from modules.excel_export import generate_excel
from modules.styling import (
    inject_css, sidebar_logo_html, app_header_html,
    hero_section_html, section_header, footer_html,
    default_buckets_html
)
from modules.ui_components import (
    render_kpis, chart_aging_qty, chart_aging_val,
    chart_aging_warehouse, chart_top10_oldest, chart_top10_value,
    render_validation_table
)
from utils.validators import validate_column_mapping, validate_data, validate_custom_buckets

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Inventory Aging Analytics · FA Fin Apps",
    page_icon="assets/fa_logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)
inject_css()


def _init_custom_buckets(lang: str):
    t0 = get_t(lang)
    st.session_state["custom_buckets"] = [
        {"name": t0["bucket_0_3"],   "from_day": 0,   "to_day": 90},
        {"name": t0["bucket_3_6"],   "from_day": 91,  "to_day": 180},
        {"name": t0["bucket_6_9"],   "from_day": 181, "to_day": 270},
        {"name": t0["bucket_9_12"],  "from_day": 271, "to_day": 365},
        {"name": t0["bucket_1_2"],   "from_day": 366, "to_day": 730},
        {"name": t0["bucket_2plus"], "from_day": 731, "to_day": None},
    ]


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    # ── Logo + brand ─────────────────────────────────────────────────────────
    # (rendered using get_t with temp lang, overwritten below)
    _tmp_lang = st.session_state.get("lang_select", "pl")
    _tmp_t    = get_t(_tmp_lang)
    st.markdown(sidebar_logo_html(_tmp_t), unsafe_allow_html=True)

    # ── Language ──────────────────────────────────────────────────────────────
    lang = st.selectbox(
        "🌐 Język / Language",
        options=["pl", "en"],
        format_func=lambda x: "🇵🇱 Polski" if x == "pl" else "🇬🇧 English",
        key="lang_select"
    )
    t = get_t(lang)

    st.markdown("---")

    # ── Aging method ──────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.06em;color:#8A9BB5;margin-bottom:4px;">{t["method_label"]}</div>',
        unsafe_allow_html=True
    )
    method_options = [t["method_index"], t["method_batch"]]
    aging_method = st.radio(
        t["method_label"], options=method_options,
        label_visibility="collapsed", key="aging_method_radio"
    )
    use_batch = (aging_method == t["method_batch"])

    st.markdown("---")

    # ── Aging date ────────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.06em;color:#8A9BB5;margin-bottom:4px;">{t["date_label"]}</div>',
        unsafe_allow_html=True
    )
    aging_date = st.date_input(
        t["date_label"], value=date.today(),
        label_visibility="collapsed", key="aging_date_input"
    )

    st.markdown("---")

    # ── Bucket type ───────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.06em;color:#8A9BB5;margin-bottom:4px;">{t["buckets_type_label"]}</div>',
        unsafe_allow_html=True
    )
    bucket_type = st.radio(
        t["buckets_type_label"],
        options=[t["buckets_default"], t["buckets_custom"]],
        label_visibility="collapsed", key="bucket_type_radio"
    )
    default_buckets_list = get_default_buckets(lang)

    if bucket_type == t["buckets_default"]:
        st.markdown(default_buckets_html(default_buckets_list), unsafe_allow_html=True)
        buckets = default_buckets_list

    else:
        # ── Custom buckets editor ─────────────────────────────────────────────
        hint_text = ("Wprowadź przedziały w dniach. Przykład: 0–90 = 0–3 mies."
                     if lang == "pl" else
                     "Enter ranges in days. Example: 0–90 = 0–3 months.")
        st.markdown(f'<div class="cb-hint">{hint_text}</div>', unsafe_allow_html=True)

        if "custom_buckets" not in st.session_state:
            _init_custom_buckets(lang)

        # handle remove
        if st.session_state.get("_remove_bucket_idx") is not None:
            idx_r = st.session_state.pop("_remove_bucket_idx")
            cb = st.session_state.get("custom_buckets", [])
            if len(cb) > 1 and 0 <= idx_r < len(cb):
                cb.pop(idx_r)
                st.session_state["custom_buckets"] = cb

        # handle add
        if st.session_state.get("_add_bucket"):
            st.session_state.pop("_add_bucket")
            cb = st.session_state.get("custom_buckets", [])
            last_to = cb[-1].get("to_day") if cb else None
            new_from = (last_to + 1) if last_to is not None else 731
            cb.append({"name": "", "from_day": new_from, "to_day": new_from + 89})
            st.session_state["custom_buckets"] = cb

        cb_list = st.session_state.get("custom_buckets", [])
        lbl_from = t.get("bucket_from", "Od dnia" if lang == "pl" else "From day")
        lbl_to   = t.get("bucket_to",   "Do dnia" if lang == "pl" else "To day")
        lbl_name = t.get("bucket_name", "Nazwa" if lang == "pl" else "Name")
        lbl_rem  = t.get("bucket_remove", "Usuń" if lang == "pl" else "Remove")

        for i, b in enumerate(cb_list):
            is_last = (i == len(cb_list) - 1)
            st.markdown(f'<div class="cb-card"><div class="cb-card-header">#{i+1}</div></div>', unsafe_allow_html=True)
            st.markdown('<div class="cb-inputs">', unsafe_allow_html=True)

            new_name = st.text_input(
                lbl_name, value=b.get("name", ""),
                key=f"cb_name_{i}", placeholder=lbl_name,
                label_visibility="collapsed"
            )
            cf, ct = st.columns(2)
            with cf:
                new_from = st.number_input(
                    lbl_from, value=int(b.get("from_day") or 0),
                    min_value=0, step=1, key=f"cb_from_{i}",
                    label_visibility="collapsed"
                )
            with ct:
                cur_to = b.get("to_day")
                if is_last:
                    to_v = st.number_input(
                        lbl_to, value=int(cur_to) if cur_to is not None else 0,
                        min_value=0, step=1, key=f"cb_to_{i}",
                        help=t.get("bucket_to_help", "0 = open"),
                        label_visibility="collapsed"
                    )
                    new_to = int(to_v) if int(to_v) > 0 else None
                else:
                    to_v = st.number_input(
                        lbl_to,
                        value=int(cur_to) if cur_to is not None else int(new_from) + 89,
                        min_value=1, step=1, key=f"cb_to_{i}",
                        label_visibility="collapsed"
                    )
                    new_to = int(to_v)

            st.markdown('</div>', unsafe_allow_html=True)
            rstr = f"{int(new_from)}–{'∞' if new_to is None else int(new_to)}"
            st.markdown(
                f'<div style="font-size:0.62rem;color:#8A9BB5;margin:-1px 0 3px 0;">{rstr} dni/days</div>',
                unsafe_allow_html=True
            )
            st.markdown('<div class="cb-remove">', unsafe_allow_html=True)
            if st.button(lbl_rem, key=f"cb_rem_{i}"):
                st.session_state["_remove_bucket_idx"] = i
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            cb_list[i] = {"name": new_name, "from_day": int(new_from), "to_day": new_to}

        st.session_state["custom_buckets"] = cb_list

        st.markdown('<div class="cb-add">', unsafe_allow_html=True)
        if st.button(t.get("bucket_add", "➕ Add"), key="cb_add_btn"):
            st.session_state["_add_bucket"] = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        berrs, bwarns = validate_custom_buckets(cb_list, t)
        for w in bwarns:
            st.markdown(f'<div style="background:#FFF8E7;border-radius:5px;padding:4px 8px;font-size:0.68rem;color:#7D5A00;margin-top:3px;">⚠️ {w}</div>', unsafe_allow_html=True)
        for e in berrs:
            st.markdown(f'<div style="background:#FDECEA;border-radius:5px;padding:4px 8px;font-size:0.68rem;color:#C0392B;margin-top:3px;">❌ {e}</div>', unsafe_allow_html=True)
        buckets = default_buckets_list if berrs else cb_list

    st.markdown("---")
    st.markdown(
        '<div style="font-size:0.68rem;color:#8A9BB5;text-align:center;">FA Fin Apps · v1.2 · © 2025</div>',
        unsafe_allow_html=True
    )

# ── Refresh t after sidebar ───────────────────────────────────────────────────
t = get_t(lang)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# ── App header ────────────────────────────────────────────────────────────────
st.markdown(app_header_html(t), unsafe_allow_html=True)

# ── Hero section (only before file upload) ────────────────────────────────────
if not st.session_state.get("file_uploader"):
    st.markdown(hero_section_html(t), unsafe_allow_html=True)

# ── STEP 1: File Upload ───────────────────────────────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown(section_header(t["upload_header"]), unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    t["upload_label"], type=["xlsx", "xls", "csv"],
    help=t["upload_help"], label_visibility="collapsed", key="file_uploader"
)

df_raw = None

if uploaded_file is not None:
    with st.expander(t["header_row_preview"], expanded=False):
        df_peek = load_file_raw(uploaded_file)
        if df_peek is not None:
            st.dataframe(df_peek.head(6), use_container_width=True)
        else:
            st.warning(t["error_file_read"])

    col_hr1, col_hr2 = st.columns([1, 3])
    with col_hr1:
        header_row = st.number_input(
            t["header_row_label"], min_value=1, max_value=50,
            value=st.session_state.get("header_row_val", 1),
            step=1, help=t["header_row_help"], key="header_row_input"
        )
        st.session_state["header_row_val"] = int(header_row)

    with st.spinner("Loading..."):
        df_raw = load_file(uploaded_file, header_row=int(header_row))

    if df_raw is not None:
        st.success(
            f"{t['upload_success']} — {t['rows_loaded']}: **{len(df_raw):,}** "
            f"| {t['cols_loaded']}: **{len(df_raw.columns)}**"
        )
        with st.expander(t["preview_header"], expanded=False):
            st.dataframe(df_raw.head(20), use_container_width=True, hide_index=True)
    else:
        st.error(t["error_file_read"])

st.markdown("</div>", unsafe_allow_html=True)

# ── STEP 2: Column Mapping ────────────────────────────────────────────────────
mapping = {}

if df_raw is not None:
    col_options  = [""] + get_column_options(df_raw)
    skip_label   = t["col_skip"]

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(section_header(t["mapping_header"]), unsafe_allow_html=True)
    st.caption(t["mapping_desc"])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**📌 {t['mandatory_cols']}**")
        mat_idx      = st.selectbox(t["col_material_index"], col_options, key="map_idx")
        receipt_date = st.selectbox(t["col_receipt_date"],   col_options, key="map_date")
        mat_name     = st.selectbox(t["col_material_name"],  col_options, key="map_name")
        doc_number   = st.selectbox(t["col_doc_number"],     col_options, key="map_doc")
        quantity     = st.selectbox(t["col_quantity"],       col_options, key="map_qty")

    with col2:
        st.markdown(f"**🔧 {t['optional_cols']}**")
        col_opts_skip = [skip_label] + get_column_options(df_raw)
        value_col     = st.selectbox(t["col_value"],     col_opts_skip, key="map_val")
        warehouse_col = st.selectbox(t["col_warehouse"], col_opts_skip, key="map_wh")
        if use_batch:
            st.markdown(f"**🏷️ {t['batch_col_required']}**")
            batch_col = st.selectbox(t["col_batch"], col_options, key="map_batch")
        else:
            batch_col = ""

    mapping = {
        "material_index": mat_idx      if mat_idx else None,
        "receipt_date":   receipt_date if receipt_date else None,
        "material_name":  mat_name     if mat_name else None,
        "doc_number":     doc_number   if doc_number else None,
        "quantity":       quantity     if quantity else None,
        "value":          value_col    if value_col and value_col != skip_label else None,
        "warehouse":      warehouse_col if warehouse_col and warehouse_col != skip_label else None,
        "batch":          batch_col    if batch_col else None,
    }
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Calc section ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    if not mapping.get("value"):     st.info(t["info_no_value_col"])
    if not mapping.get("warehouse"): st.info(t["info_no_wh_col"])
    if use_batch and not mapping.get("batch"): st.warning(t["info_batch_required"])

    calc_col1, _ = st.columns([2, 1])
    with calc_col1:
        calc_clicked = st.button(t["calc_button"], type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # CALCULATION
    # ══════════════════════════════════════════════════════════════════════════
    if calc_clicked or st.session_state.get("results_ready"):

        missing_cols = validate_column_mapping(mapping, use_batch)
        if missing_cols:
            st.error(f"❌ {t['error_missing_cols']}{', '.join(missing_cols)}")
            st.stop()

        if calc_clicked:
            try:
                with st.spinner("Calculating..."):
                    method_label = t["method_batch"] if use_batch else t["method_index"]
                    df_work = df_raw.copy()
                    df_work[mapping["quantity"]] = pd.to_numeric(df_work[mapping["quantity"]], errors="coerce").fillna(0)
                    if mapping.get("value"):
                        df_work[mapping["value"]] = pd.to_numeric(df_work[mapping["value"]], errors="coerce").fillna(0)

                    validation_issues = validate_data(df_work, mapping, aging_date, use_batch, t)
                    df_result = calculate_aging(df_work, mapping, aging_date, buckets, use_batch, method_label, t)
                    df_qty    = build_qty_summary(df_result, mapping, buckets, use_batch, t)
                    df_val    = build_val_summary(df_result, mapping, buckets, use_batch, t)
                    df_wh     = build_warehouse_summary(df_result, mapping, buckets, t)
                    df_batch  = build_batch_summary(df_result, mapping, buckets, use_batch, t)
                    stats     = build_summary_stats(df_result, mapping, buckets, t)

                    # extra KPIs
                    stats["n_records"] = len(df_result)
                    stats["n_batches"] = df_result[mapping["batch"]].nunique() if mapping.get("batch") else None

                    val_log_rows = [[v["row"], v["type"], v["description"], v["severity"]] for v in validation_issues]

                    st.session_state.update({
                        "results_ready": True,
                        "df_result": df_result, "df_qty": df_qty, "df_val": df_val,
                        "df_wh": df_wh, "df_batch": df_batch, "stats": stats,
                        "validation_issues": validation_issues, "val_log_rows": val_log_rows,
                        "buckets_used": buckets, "mapping_used": mapping,
                        "aging_date_used": aging_date, "use_batch_used": use_batch,
                    })
                    st.success(t["calc_success"])

            except Exception as e:
                st.error(f"{t['calc_error']}: {str(e)}")
                with st.expander("Debug"):
                    st.code(traceback.format_exc())
                st.stop()

        if st.session_state.get("results_ready"):
            df_result         = st.session_state["df_result"]
            df_qty            = st.session_state["df_qty"]
            df_val            = st.session_state["df_val"]
            df_wh             = st.session_state["df_wh"]
            df_batch          = st.session_state["df_batch"]
            stats             = st.session_state["stats"]
            validation_issues = st.session_state["validation_issues"]
            val_log_rows      = st.session_state["val_log_rows"]
            buckets_used      = st.session_state["buckets_used"]
            mapping_used      = st.session_state["mapping_used"]
            aging_date_used   = st.session_state["aging_date_used"]
            use_batch_used    = st.session_state["use_batch_used"]

            # ── Tabs ──────────────────────────────────────────────────────────
            tabs_list = [t["tab_dashboard"], t["tab_detail"], t["tab_qty_summary"]]
            if df_val is not None:   tabs_list.append(t["tab_val_summary"])
            if df_wh is not None:    tabs_list.append(t["tab_wh_summary"])
            if df_batch is not None: tabs_list.append(t["tab_batch_summary"])
            tabs_list.append(t["tab_validation"])

            tab_objs = st.tabs(tabs_list)
            ti = 0

            # Dashboard
            with tab_objs[ti]:
                ti += 1
                render_kpis(stats, t)
                st.write("")
                c1, c2 = st.columns(2)
                with c1:
                    chart_aging_qty(df_result, t["out_bucket"], mapping_used["quantity"], t, buckets_used)
                with c2:
                    if mapping_used.get("value"):
                        chart_aging_val(df_result, t["out_bucket"], mapping_used["value"], t, buckets_used)
                    else:
                        st.info(t["info_no_value_col"])

                if mapping_used.get("warehouse"):
                    c3, c4 = st.columns(2)
                    with c3:
                        chart_aging_warehouse(df_result, mapping_used["warehouse"], t["out_bucket"], mapping_used["quantity"], t, buckets_used)
                    with c4:
                        chart_top10_oldest(df_result, mapping_used["material_index"], mapping_used["material_name"], t["out_age_days"], mapping_used["quantity"], t)
                else:
                    c3, c4 = st.columns(2)
                    with c3:
                        chart_top10_oldest(df_result, mapping_used["material_index"], mapping_used["material_name"], t["out_age_days"], mapping_used["quantity"], t)
                    with c4:
                        if mapping_used.get("value"):
                            chart_top10_value(df_result, mapping_used["material_index"], mapping_used["material_name"], mapping_used["value"], t)

            # Detailed data
            with tab_objs[ti]:
                ti += 1
                st.markdown(section_header(t["tab_detail"]), unsafe_allow_html=True)
                st.dataframe(df_result.drop(columns=["_bucket_order"], errors="ignore"), use_container_width=True, hide_index=True)

            # Qty summary
            with tab_objs[ti]:
                ti += 1
                st.markdown(section_header(t["tab_qty_summary"]), unsafe_allow_html=True)
                st.dataframe(df_qty, use_container_width=True, hide_index=True)

            # Val summary
            if df_val is not None:
                with tab_objs[ti]:
                    ti += 1
                    st.markdown(section_header(t["tab_val_summary"]), unsafe_allow_html=True)
                    st.dataframe(df_val, use_container_width=True, hide_index=True)

            # Warehouse summary
            if df_wh is not None:
                with tab_objs[ti]:
                    ti += 1
                    st.markdown(section_header(t["tab_wh_summary"]), unsafe_allow_html=True)
                    st.dataframe(df_wh, use_container_width=True, hide_index=True)

            # Batch summary
            if df_batch is not None:
                with tab_objs[ti]:
                    ti += 1
                    st.markdown(section_header(t["tab_batch_summary"]), unsafe_allow_html=True)
                    st.dataframe(df_batch, use_container_width=True, hide_index=True)

            # Validation
            with tab_objs[ti]:
                ti += 1
                st.markdown(section_header(t["validation_header"]), unsafe_allow_html=True)
                render_validation_table(validation_issues, t)

            # Excel download
            st.markdown("---")
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown(section_header(t["download_button"]), unsafe_allow_html=True)
            excel_bytes = generate_excel(
                df_detail=df_result.drop(columns=["_bucket_order"], errors="ignore"),
                df_qty=df_qty, df_val=df_val, df_wh=df_wh, df_batch=df_batch,
                validation_log=val_log_rows, mapping=mapping_used,
                aging_date=aging_date_used, buckets=buckets_used, stats=stats, t=t
            )
            st.download_button(
                label=t["download_button"], data=excel_bytes,
                file_name=f"inventory_aging_{aging_date_used.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.markdown("</div>", unsafe_allow_html=True)

else:
    # No file yet
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(
        f'<div style="text-align:center;padding:44px 20px;">'
        f'<div style="font-size:3.5rem;margin-bottom:14px;">📦</div>'
        f'<h3 style="color:#1B2B4B;font-weight:800;margin-bottom:8px;">{t["step1"]}</h3>'
        f'<p style="color:#8A9BB5;font-size:0.92rem;max-width:380px;margin:0 auto;">{t["instructions"]}</p>'
        f'</div>',
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(footer_html(t), unsafe_allow_html=True)
