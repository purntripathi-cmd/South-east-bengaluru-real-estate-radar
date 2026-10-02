"""
Custom Sticky / Frozen Column Table Renderer for Streamlit
Freezes first 3 columns and sticky header with horizontal and vertical scroll.
"""

import pandas as pd
import streamlit as st


def render_sticky_frozen_table(df: pd.DataFrame, frozen_cols: int = 3, table_id: str = "custom_table", max_height: str = "520px"):
    """
    Renders an HTML/CSS table where the first `frozen_cols` columns are permanently frozen / sticky on the left,
    and the table header is sticky on top, while the remaining columns scroll horizontally.
    """
    if df.empty:
        st.info("No records to display.")
        return

    cols = list(df.columns)
    frozen_col_count = min(frozen_cols, len(cols))
    frozen_headers = cols[:frozen_col_count]
    scroll_headers = cols[frozen_col_count:]

    # Define fixed pixel widths for frozen columns
    col_widths = [190, 160, 160]  # width in px
    offsets = [0]
    for i in range(1, frozen_col_count):
        offsets.append(offsets[i-1] + col_widths[i-1])

    # Build CSS
    css = f"""
    <style>
    #{table_id}_container {{
        overflow-x: auto;
        overflow-y: auto;
        max-height: {max_height};
        border-radius: 8px;
        border: 1px solid #334155;
        background-color: #0B1120;
        position: relative;
        margin-bottom: 12px;
    }}
    #{table_id}_container table {{
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        font-size: 0.84rem;
    }}
    #{table_id}_container th {{
        position: sticky;
        top: 0;
        background-color: #1E293B;
        color: #38BDF8;
        font-weight: 700;
        padding: 10px 14px;
        border-bottom: 2px solid #334155;
        border-right: 1px solid #1E293B;
        white-space: nowrap;
        z-index: 25;
        text-align: left;
    }}
    #{table_id}_container td {{
        padding: 9px 14px;
        border-bottom: 1px solid #1E293B;
        border-right: 1px solid #1E293B;
        white-space: nowrap;
        background-color: #0B1120;
        color: #E2E8F0;
    }}
    #{table_id}_container tr:nth-child(even) td {{
        background-color: #0F172A;
    }}
    #{table_id}_container tr:hover td {{
        background-color: #1E293B !important;
    }}
    """

    # Frozen column CSS rules
    for idx in range(frozen_col_count):
        nth = idx + 1
        left_px = offsets[idx]
        width_px = col_widths[idx]
        is_last_frozen = (idx == frozen_col_count - 1)
        border_right = "border-right: 3px solid #0D9488 !important; box-shadow: 4px 0 10px rgba(0,0,0,0.6);" if is_last_frozen else "border-right: 1px solid #334155;"

        css += f"""
        #{table_id}_container th:nth-child({nth}) {{
            position: sticky;
            left: {left_px}px;
            top: 0;
            z-index: 40 !important;
            background-color: #1E293B;
            min-width: {width_px}px;
            max-width: {width_px + 30}px;
            width: {width_px}px;
            {border_right}
        }}
        #{table_id}_container td:nth-child({nth}) {{
            position: sticky;
            left: {left_px}px;
            z-index: 20;
            background-color: #0B1120;
            min-width: {width_px}px;
            max-width: {width_px + 30}px;
            width: {width_px}px;
            font-weight: {'700' if nth == 1 else '500'};
            color: {'#38BDF8' if nth == 1 else ('#F8FAFC' if nth == 2 else '#10B981')};
            {border_right}
        }}
        #{table_id}_container tr:nth-child(even) td:nth-child({nth}) {{
            background-color: #0F172A;
        }}
        #{table_id}_container tr:hover td:nth-child({nth}) {{
            background-color: #1E293B !important;
        }}
        """

    css += "</style>"

    # Build Table HTML
    html = [f"<div id='{table_id}_container'>{css}<table><thead><tr>"]
    for c in cols:
        html.append(f"<th>{c}</th>")
    html.append("</tr></thead><tbody>")

    for _, row in df.iterrows():
        html.append("<tr>")
        for c in cols:
            val = str(row[c])
            # Highlight specific text
            if "🟢" in val:
                cell_content = f"<span style='color:#10B981; font-weight:700;'>{val}</span>"
            elif "🔴" in val:
                cell_content = f"<span style='color:#EF4444; font-weight:700;'>{val}</span>"
            elif "⭐" in val:
                cell_content = f"<span style='color:#FBBF24; font-weight:600;'>{val}</span>"
            elif val.startswith("₹"):
                cell_content = f"<span style='color:#F59E0B; font-weight:600;'>{val}</span>"
            elif "http" in val:
                cell_content = f"<a href='{val}' target='_blank' rel='noreferrer noopener' style='color:#38BDF8;'>Link ↗</a>"
            else:
                cell_content = val
            html.append(f"<td>{cell_content}</td>")
        html.append("</tr>")

    html.append("</tbody></table></div>")

    # Render HTML in Streamlit
    st.markdown("".join(html), unsafe_allow_html=True)
