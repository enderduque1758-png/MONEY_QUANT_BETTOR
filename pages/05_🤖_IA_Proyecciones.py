import json
import streamlit as st
from services import ai_validate

st.set_page_config(page_title="IA | MONEY QUANT BETTOR", page_icon="🤖", layout="wide")
st.title("🤖 IA — Proyecciones y recomendaciones")
st.caption("Valida el modelo usando automáticamente el contexto que le entregues. No inventa datos.")

sport=st.text_input('Deporte','MLB')
home=st.text_input('Local')
away=st.text_input('Visitante')
context=st.text_area('Contexto estadístico / H2H / cuotas',height=260,placeholder='Puedes pegar el resumen generado por el panel principal.')
if st.button('🧠 Analizar',type='primary'):
    payload={'sport':sport,'event':{'home':home,'away':away},'context':context,'instruction':'Devuelve recomendación principal y hasta 5 opciones opcionales. No inventes datos. Si faltan datos críticos o EV no es positivo, usa SIN APUESTA.'}
    result=ai_validate(payload)
    if not result.get('ok'):
        st.error(result.get('error','IA no configurada'))
    else:
        text=result.get('text','')
        try:
            data=json.loads(text)
            c=st.columns(4); c[0].metric('Mercado',data.get('mercado_recomendado','SIN APUESTA')); c[1].metric('Prob. IA',f"{float(data.get('probabilidad_ia',0)):.1f}%"); c[2].metric('Cuota justa',f"{float(data.get('cuota_justa',0)):.2f}"); c[3].metric('Confianza',f"{float(data.get('confianza',0)):.1f}/10")
            st.markdown('### 🥇 Recomendación principal'); st.write(data.get('mercado_recomendado','SIN APUESTA'))
            st.markdown('### 🔵 Opciones opcionales'); st.write(data.get('opciones_opcionales',data.get('alternativas',[])))
            st.markdown('### 📊 Justificación'); st.write(data.get('razonamiento',''))
            st.markdown('### ⚠️ Riesgos'); st.write(data.get('riesgos',''))
        except Exception:
            st.code(text,language='json')
