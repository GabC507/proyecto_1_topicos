from playwright.sync_api import sync_playwright
import os

OUT = 'qa_evidencias_detalladas_prs'
os.makedirs(OUT, exist_ok=True)

def shot(page, name):
    path = os.path.join(OUT, name)
    page.screenshot(path=path, full_page=True)
    print(f'  [CAPTURA] {name}')

with sync_playwright() as sp:
    browser = sp.chromium.launch(headless=True)
    
    print('\n=== PR #3 (feature/saved-contact-details) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    try:
        page.goto('file:///C:/Users/LIGA-EQUIPO7/Downloads/proyecto_1_topicos/frontend_index_pr3.html')
        page.wait_for_timeout(2500)
        shot(page, 'PR3_01_carga_rama.png')
        consent = page.locator('#saveContactConsent')
        print(f'  #saveContactConsent: {consent.count()}')
        if consent.count() > 0:
            shot(page, 'PR3_02_consent_presente.png')
        forget = page.locator('#forgetSavedContact')
        print(f'  #forgetSavedContact: {forget.count()}')
        if forget.count() > 0:
            shot(page, 'PR3_03_boton_borrar_presente.png')
        page.fill('#name', 'Test QA')
        page.fill('#phone', '+56 9 1111 2222')
        shot(page, 'PR3_04_datos_rellenos.png')
    except Exception as e:
        print(f'  ERR: {e}')
    ctx.close()
    
    print('\n=== PR #4 (feature/dynamic-availability-calendar) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    try:
        page.goto('file:///C:/Users/LIGA-EQUIPO7/Downloads/proyecto_1_topicos/frontend_index_pr4.html')
        page.wait_for_timeout(2500)
        shot(page, 'PR4_01_carga_rama.png')
        dates = page.locator('input[type=date]')
        print(f'  input[type=date]: {dates.count()}')
        slots = page.locator('.slot')
        print(f'  .slot: {slots.count()}')
        page.set_viewport_size({'width': 375, 'height': 812})
        page.wait_for_timeout(1500)
        shot(page, 'PR4_02_movil_rama.png')
    except Exception as e:
        print(f'  ERR: {e}')
    ctx.close()
    
    print('\n=== PR #1 (feature/secure-customer-appointment-management) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    try:
        page.goto('file:///C:/Users/LIGA-EQUIPO7/Downloads/proyecto_1_topicos/frontend_index_pr1.html')
        page.wait_for_timeout(2500)
        shot(page, 'PR1_01_carga_rama.png')
        manage = page.locator('text=/gestionar/i')
        print(f'  text=/gestionar/i: {manage.count()}')
        code = page.locator('input[placeholder*="códig" i]')
        print(f'  input codigo: {code.count()}')
        shot(page, 'PR1_02_gestion_elementos.png')
    except Exception as e:
        print(f'  ERR: {e}')
    ctx.close()
    
    print('\n=== PR #2 (feature/admin-blocked-times) ===')
    ctx = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = ctx.new_page()
    try:
        page.goto('file:///C:/Users/LIGA-EQUIPO7/Downloads/proyecto_1_topicos/frontend_admin_pr2.html')
        page.wait_for_timeout(2500)
        shot(page, 'PR2_01_carga_rama.png')
        ti = page.locator('input[type=password]')
        if ti.count() > 0:
            ti.first.fill('test-token')
            btns = page.locator('button')
            for i in range(btns.count()):
                try:
                    txt = btns.nth(i).inner_text().lower()
                    if 'entr' in txt or 'acc' in txt or 'login' in txt:
                        btns.nth(i).click()
                        break
                except:
                    pass
            page.wait_for_timeout(4000)
        shot(page, 'PR2_02_logueado_rama.png')
        blocks = page.locator('text=/bloqueo/i')
        print(f'  text=/bloqueo/i: {blocks.count()}')
        page.set_viewport_size({'width': 375, 'height': 812})
        page.wait_for_timeout(1500)
        shot(page, 'PR2_03_movil_rama.png')
    except Exception as e:
        print(f'  ERR: {e}')
    ctx.close()
    
    browser.close()
    print(f'\n=== COMPLETADO ===')
    print(f'Evidencias: {OUT}/')
