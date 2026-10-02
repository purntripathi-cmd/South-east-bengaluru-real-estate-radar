"""
Custom Sticky / Frozen Column Table Renderer for Streamlit
Freezes first 3 columns and sticky header with horizontal and vertical scroll.
Renders via Streamlit Components HTML iframe for 100% guaranteed visibility across all browsers.
"""

import html as html_lib
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def render_sticky_frozen_table(df: pd.DataFrame, frozen_cols: int = 2, table_id: str = "custom_table", max_height: str = "540px"):
    """
    Renders an HTML/CSS table where the first `frozen_cols` columns are permanently frozen / sticky on the left,
    and the table header is sticky on top, while the remaining columns scroll horizontally.
    Uses components.html for rock-solid iframe rendering without markdown stripping.
    """
    if df.empty:
        st.info("No records to display.")
        return

    cols = list(df.columns)
    frozen_col_count = min(frozen_cols, len(cols))
    frozen_headers = cols[:frozen_col_count]

    # Calculate optimal pixel height
    try:
        max_h_int = int(str(max_height).replace("px", "").strip())
    except Exception:
        max_h_int = 540
    calc_height = min(max_h_int, max(280, (len(df) + 1) * 44 + 50))

    # Column widths for frozen columns
    # Col 1 (Property Name): 185px
    # Col 2 (Builder / Unit / Developer): 150px
    # Col 3 (Date Posted): 155px
    # Col 4 (Road Dist to Landmark): 155px
    col_widths = [185, 150, 155, 155]
    offsets = [0]
    for i in range(1, frozen_col_count):
        w = col_widths[i-1] if i-1 < len(col_widths) else 150
        offsets.append(offsets[i-1] + w)

    # Build pure CSS
    css_rules = [f"""
    * {{
        box-sizing: border-box;
    }}
    body {{
        margin: 0;
        padding: 0;
        background-color: #0B1120;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #F8FAFC;
    }}
    .table-container {{
        position: relative;
        overflow-x: auto;
        overflow-y: auto;
        max-height: {calc_height - 10}px;
        width: 100%;
        border: 1px solid #334155;
        border-radius: 8px;
        background-color: #0B1120;
        -webkit-overflow-scrolling: touch;
    }}
    table {{
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        font-size: 0.83rem;
    }}
    th {{
        position: sticky;
        top: 0;
        background-color: #1E293B;
        color: #38BDF8;
        font-weight: 700;
        padding: 10px 14px;
        border-bottom: 2px solid #334155;
        border-right: 1px solid #334155;
        white-space: nowrap;
        z-index: 25;
        text-align: left;
    }}
    td {{
        padding: 9px 14px;
        border-bottom: 1px solid #1E293B;
        border-right: 1px solid #1E293B;
        white-space: nowrap;
        background-color: #0B1120;
        color: #E2E8F0;
    }}
    tr:nth-child(even) td {{
        background-color: #0F172A;
    }}
    tr:hover td {{
        background-color: #1E293B !important;
    }}
    """]

    # Frozen column rules
    for idx in range(frozen_col_count):
        nth = idx + 1
        left_px = offsets[idx]
        width_px = col_widths[idx] if idx < len(col_widths) else 150
        is_last_frozen = (idx == frozen_col_count - 1)
        
        if is_last_frozen:
            border_r = "border-right: 3px solid #0D9488 !important; box-shadow: 4px 0 10px rgba(0,0,0,0.6);"
        else:
            border_r = "border-right: 1px solid #334155;"

        # Color coding: Col 1 = Sky, Col 2 = White, Col 3 = Emerald (Date), Col 4 = Amber (Road Distance)
        if nth == 1:
            font_color = "#38BDF8"
            font_weight = "700"
        elif nth == 2:
            font_color = "#F8FAFC"
            font_weight = "500"
        elif nth == 3:
            font_color = "#10B981"
            font_weight = "600"
        elif nth == 4:
            font_color = "#F59E0B"
            font_weight = "700"
        else:
            font_color = "#E2E8F0"
            font_weight = "500"

        css_rules.append(f"""
        th.fcol-{nth} {{
            position: sticky;
            left: {left_px}px;
            top: 0;
            z-index: 45 !important;
            background-color: #1E293B;
            min-width: {width_px}px;
            max-width: {width_px + 30}px;
            width: {width_px}px;
            {border_r}
        }}
        td.fcol-{nth} {{
            position: sticky;
            left: {left_px}px;
            z-index: 20;
            background-color: #0B1120;
            min-width: {width_px}px;
            max-width: {width_px + 30}px;
            width: {width_px}px;
            font-weight: {font_weight};
            color: {font_color};
            {border_r}
        }}
        tr:nth-child(even) td.fcol-{nth} {{
            background-color: #0F172A;
        }}
        tr:hover td.fcol-{nth} {{
            background-color: #1E293B !important;
        }}
        """)

    # Responsive rule for mobile (<768px): keep column 1 sticky, unfreeze others to avoid screen clipping
    css_rules.append("""
    @media (max-width: 768px) {
        th.fcol-2, th.fcol-3, th.fcol-4, td.fcol-2, td.fcol-3, td.fcol-4 {
            position: static !important;
            border-right: 1px solid #1E293B !important;
            box-shadow: none !important;
        }
    }
    """)

    full_css = "\n".join(css_rules)

    # Build Table HTML
    html_parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        f"<style>{full_css}</style>",
        "</head>",
        "<body>",
        f"<div class='table-container' id='{table_id}_container'>",
        "<table>",
        "<thead>",
        "<tr>"
    ]

    for idx, c in enumerate(cols):
        col_class = f" class='fcol-{idx+1}'" if idx < frozen_col_count else ""
        html_parts.append(f"<th{col_class}>{html_lib.escape(str(c))}</th>")
    html_parts.append("</tr></thead><tbody>")

    for _, row in df.iterrows():
        html_parts.append("<tr>")
        for idx, c in enumerate(cols):
            col_class = f" class='fcol-{idx+1}'" if idx < frozen_col_count else ""
            raw_val = str(row[c]) if row[c] is not None else ""
            
            # Format cell content
            if "🟢" in raw_val:
                cell_content = f"<span style='color:#10B981; font-weight:700;'>{html_lib.escape(raw_val)}</span>"
            elif "🔴" in raw_val:
                cell_content = f"<span style='color:#EF4444; font-weight:700;'>{html_lib.escape(raw_val)}</span>"
            elif "⭐" in raw_val:
                cell_content = f"<span style='color:#FBBF24; font-weight:600;'>{html_lib.escape(raw_val)}</span>"
            elif raw_val.startswith("₹"):
                cell_content = f"<span style='color:#F59E0B; font-weight:600;'>{html_lib.escape(raw_val)}</span>"
            elif raw_val.startswith("http://") or raw_val.startswith("https://"):
                cell_content = f"<a href='{html_lib.escape(raw_val)}' target='_blank' rel='noreferrer noopener' style='color:#38BDF8; text-decoration:underline;'>Link ↗</a>"
            elif "Core Radar (Tab 1)" in raw_val:
                cell_content = f"<span style='background:#065F46; color:#6EE7B7; padding:2px 6px; border-radius:4px; font-weight:700;'>{html_lib.escape(raw_val)}</span>"
            elif "Nearby Extension" in raw_val:
                cell_content = f"<span style='background:#5B21B6; color:#DDD6FE; padding:2px 6px; border-radius:4px; font-weight:700;'>{html_lib.escape(raw_val)}</span>"
            else:
                cell_content = html_lib.escape(raw_val)

            html_parts.append(f"<td{col_class}>{cell_content}</td>")
        html_parts.append("</tr>")

    html_parts.extend([
        "</tbody>",
        "</table>",
        "</div>",
        "</body>",
        "</html>"
    ])

    full_html = "\n".join(html_parts)

    # Render via Streamlit Components HTML iframe for 100% reliable rendering
    components.html(full_html, height=calc_height, scrolling=True)
