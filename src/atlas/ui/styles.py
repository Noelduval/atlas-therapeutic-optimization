"""Restrained design tokens derived from the accepted Atlas UI references."""

APP_CSS = """
<style>
:root {
  --atlas-navy: #092556;
  --atlas-teal: #007a76;
  --atlas-text: #15213a;
  --atlas-muted: #5d687b;
  --atlas-rule: #d9dee7;
  --atlas-soft: #f6f8fb;
}
.stApp { background: #ffffff; color: var(--atlas-text); }
[data-testid="stHeader"] { background: rgba(255,255,255,.96); }
[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid var(--atlas-rule); }
[data-testid="stSidebar"] > div:first-child { padding-top: 1.75rem; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: .2rem; }
[data-testid="stSidebar"] [data-testid="stRadioOption"] {
  border-left: 3px solid transparent;
  padding: .62rem .8rem;
  transition: background-color .15s ease, border-color .15s ease;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] {
  background: var(--atlas-soft);
  border-left-color: var(--atlas-teal);
}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div > div:first-child {
  display: none;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"] p {
  color: var(--atlas-text);
  font-weight: 520;
}
[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] p {
  color: var(--atlas-navy);
  font-weight: 650;
}
.block-container { max-width: 1180px; padding-top: 4.5rem; padding-bottom: 5rem; }
h1, h2, h3 { color: var(--atlas-navy); letter-spacing: -0.025em; }
h1 { font-size: clamp(2.5rem, 5vw, 4rem) !important; font-weight: 650 !important; }
h2 { font-weight: 620 !important; }
p, li, td, th, label, button { font-size: 0.96rem; line-height: 1.55; }
.atlas-wordmark { color: var(--atlas-navy); font-size: 2rem; font-weight: 650; letter-spacing: -0.04em; margin: 0 0 1.4rem; }
.atlas-description { max-width: 760px; color: var(--atlas-muted); font-size: 1.05rem; line-height: 1.65; margin: .75rem 0 2rem; }
.atlas-metadata { max-width: 760px; border-top: 1px solid var(--atlas-rule); margin: 2rem 0; }
.atlas-row { display: grid; grid-template-columns: minmax(170px, 230px) 1fr; gap: 1.5rem; padding: .72rem 0; border-bottom: 1px solid var(--atlas-rule); }
.atlas-key { color: var(--atlas-muted); }
.atlas-value { color: var(--atlas-text); font-weight: 550; }
.atlas-kicker { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--atlas-muted); margin-bottom: .5rem; }
.stButton > button[kind="primary"] { background: var(--atlas-teal); border: 1px solid var(--atlas-teal); border-radius: 4px; font-weight: 600; padding: .65rem 1.2rem; }
.stButton > button { border-radius: 4px; }
[data-testid="stDataFrame"] { border: 1px solid var(--atlas-rule); border-radius: 2px; }
[data-testid="stMetric"] { background: transparent; border-top: 1px solid var(--atlas-rule); padding-top: .75rem; }
@media (max-width: 700px) {
  .block-container { padding-top: 2rem; }
  .atlas-row { grid-template-columns: 1fr; gap: .15rem; }
  h1 { font-size: 2.35rem !important; }
  [data-testid="stDataFrame"] { max-width: calc(100vw - 2rem); overflow-x: auto; }
  code { white-space: pre-wrap !important; overflow-wrap: anywhere; }
}
</style>
"""
