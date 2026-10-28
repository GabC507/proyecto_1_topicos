from playwright.sync_api import sync_playwright
import os

os.makedirs('qa_evidencias', exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = context.new_page()
    
    try:
        page.goto('file:///C:/Users/LIGA-EQUIPO7/Downloads/proyecto_1_topicos/frontend/index.html')
        page.wait_for_timeout(2000)
        page.screenshot(path='qa_evidencias/01_frontend_index.png')
        print('01:OK')
    except Exception as e:
        print('01:ERR')
    
    try:
        page.goto('file:///C:/Users/LIGA-EQUIPO7/Downloads/proyecto_1_topicos/frontend/admin.html')
        page.wait_for_timeout(2000)
        page.screenshot(path='qa_evidencias/02_admin_sin_token.png')
        print('02:OK')
    except Exception as e:
        print('02:ERR')
    
    try:
        page.goto('http://127.0.0.1:8000/api/admin/forecast')
        page.wait_for_timeout(1000)
        page.screenshot(path='qa_evidencias/04_api_sin_token.png')
        print('04:OK')
    except Exception as e:
        print('04:ERR')
    
    try:
        context2 = browser.new_context(extra_http_headers={'X-Admin-Token': 'test-token'})
        page2 = context2.new_page()
        page2.goto('http://127.0.0.1:8000/api/admin/forecast')
        page2.wait_for_timeout(1500)
        page2.screenshot(path='qa_evidencias/05_api_con_token.png')
        print('05:OK')
        context2.close()
    except Exception as e:
        print('05:ERR')
    
    browser.close()
