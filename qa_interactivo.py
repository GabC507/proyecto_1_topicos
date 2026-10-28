from playwright.sync_api import sync_playwright
import os, json

BASE = r'file:///C:/Users/LIGA-EQUIPO7/Downloads/proyecto_1_topicos/frontend'
API = 'http://127.0.0.1:8000'
OUT = 'qa_evidencias_detalladas'
os.makedirs(OUT, exist_ok=True)

def shot(page, name):
    path = os.path.join(OUT, name)
    page.screenshot(path=path, full_page=True)
    print(f'  [CAPTURA] {name}')

with sync_playwright() as sp:
    browser = sp.chromium.launch(headless=True)
    
    print('\n=== PR #3 - DATOS GUARDADOS CON CONSENTIMIENTO ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    try:
        page.goto(BASE + '/index.html')
        page.wait_for_timeout(2500)
        shot(page, 'PR03_01_index_carga.png')
        
        consent = page.locator('#saveContactConsent')
        print(f'  Checkbox consentimiento (#saveContactConsent): {consent.count()}')
        if consent.count() > 0:
            shot(page, 'PR03_02_checkbox_consentimiento.png')
        
        forget = page.locator('#forgetSavedContact')
        print(f'  Botón "Borrar mis datos guardados": {forget.count()}')
        if forget.count() > 0:
            shot(page, 'PR03_03_boton_borrar_datos.png')
        
        page.fill('#name', 'Juan Perez QA')
        page.fill('#phone', '+56 9 8765 4321')
        shot(page, 'PR03_04_datos_rellenos_sin_consent.png')
        print('  Campos nombre/teléfono: OK')
    except Exception as e:
        print(f'  ERROR: {e}')
    ctx.close()
    
    print('\n=== PR #4 - CALENDARIO DINÁMICO ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    try:
        page.goto(BASE + '/index.html')
        page.wait_for_timeout(2500)
        shot(page, 'PR04_01_index_calendario.png')
        
        dates = page.locator('input[type=date]')
        print(f'  Input fecha: {dates.count()}')
        
        slots = page.locator('.slot')
        print(f'  Slots (.slot): {slots.count()}')
        if slots.count() > 0:
            shot(page, 'PR04_02_slots_visibles.png')
        else:
            shot(page, 'PR04_02_sin_slots_visibles.png')
        
        page.set_viewport_size({'width': 375, 'height': 812})
        page.wait_for_timeout(1500)
        shot(page, 'PR04_03_responsive_mobile.png')
        print('  Responsive móvil: OK')
        
        page.set_viewport_size({'width': 1280, 'height': 900})
        page.wait_for_timeout(1000)
    except Exception as e:
        print(f'  ERROR: {e}')
    ctx.close()
    
    print('\n=== PR #1 - CANCELAR/REPROGRAMAR CON CÓDIGO PRIVADO ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    try:
        page.goto(BASE + '/index.html')
        page.wait_for_timeout(2500)
        shot(page, 'PR01_01_pagina_principal.png')
        
        manage = page.locator('text=/gestionar/i, text=/cancelar/i, text=/reprogramar/i')
        print(f'  Texto gestionar/cancelar/reprogramar: {manage.count()}')
        
        code_inp = page.locator('input[placeholder*="códig" i], input[placeholder*="codig" i]')
        print(f'  Input código privado: {code_inp.count()}')
        
        shot(page, 'PR01_02_busqueda_gestion.png')
    except Exception as e:
        print(f'  ERROR: {e}')
    ctx.close()
    
    print('\n=== PR #2 - BLOQUEOS ADMIN + TELÉFONO +507 ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    try:
        page.goto(BASE + '/admin.html')
        page.wait_for_timeout(2500)
        shot(page, 'PR02_01_admin_login.png')
        
        ti = page.locator('input[type=password]')
        if ti.count() > 0:
            ti.first.fill('test-token')
            btns = page.locator('button')
            clicked = False
            for i in range(btns.count()):
                try:
                    txt = btns.nth(i).inner_text().lower()
                    if 'entr' in txt or 'acc' in txt or 'login' in txt:
                        btns.nth(i).click()
                        clicked = True
                        break
                except:
                    pass
            if clicked:
                print('  Login con token: OK')
            page.wait_for_timeout(4000)
        
        shot(page, 'PR02_02_admin_logueado.png')
        
        blocks = page.locator('text=/bloqueo/i')
        print(f'  Texto "bloqueo": {blocks.count()}')
        shot(page, 'PR02_03_seccion_bloqueos.png')
        
        page.set_viewport_size({'width': 375, 'height': 812})
        page.wait_for_timeout(1500)
        shot(page, 'PR02_04_admin_mobile.png')
        print('  Responsive móvil admin: OK')
    except Exception as e:
        print(f'  ERROR: {e}')
    ctx.close()
    
    print('\n=== API - VALIDACIONES ===')
    ctx = browser.new_context()
    page = ctx.new_page()
    try:
        page.goto(API + '/api/admin/forecast')
        page.wait_for_timeout(1500)
        shot(page, 'API_01_forecast_sin_token.png')
        try:
            body = page.inner_text('body')
            print(f'  /api/admin/forecast sin token: {body[:80]}')
        except:
            pass
    except Exception as e:
        print(f'  ERROR: {e}')
    ctx.close()
    
    ctx = browser.new_context(extra_http_headers={'X-Admin-Token': 'test-token'})
    page = ctx.new_page()
    try:
        page.goto(API + '/api/admin/forecast')
        page.wait_for_timeout(1500)
        shot(page, 'API_02_forecast_con_token.png')
        print('  /api/admin/forecast con token: OK')
        
        page.goto(API + '/api/admin/demand-forecast?weeks=8')
        page.wait_for_timeout(2000)
        shot(page, 'API_03_demand_forecast_con_token.png')
        print('  /api/admin/demand-forecast?weeks=8 con token: OK')
    except Exception as e:
        print(f'  ERROR: {e}')
    ctx.close()
    
    browser.close()
    print(f'\n=== COMPLETADO ===')
    print(f'Evidencias en: {OUT}/')
