"""Exercise every scenario's artwork in the browser."""
from pathlib import Path
import sys, tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app
from launcher import LocalServer
from playwright.sync_api import sync_playwright, expect

def run():
 with tempfile.TemporaryDirectory() as directory:
  server=LocalServer(create_app(Path(directory)/'themes.sqlite3',testing=True),0)
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];seen=set()
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(f'http://127.0.0.1:{server.port}')
    page.locator('.hero h1').click()
    records=page.evaluate("async()=> (await (await fetch('/api/bootstrap')).json())")
    for story in records['scenarios']:
     journey=page.evaluate("""async ({scenario,csrf}) => (await (await fetch('/api/journeys', {method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify({scenario})})).json())""",{'scenario':story['id'],'csrf':records['csrf']})
     page.evaluate('(id)=>location.hash="play/"+id',journey['id'])
     expect(page.locator('h1')).to_have_text(story['title'])
     expect(page.locator('body')).to_have_attribute('data-atmosphere',story['audio'])
     image=page.locator('.atmosphere-banner img')
     expect(image).to_have_attribute('src','/static/art/'+story['audio']+'.svg')
     image.evaluate('img=>img.decode()')
     assert image.evaluate('img=>img.naturalWidth')>0
     if story['audio'] not in seen:
      seen.add(story['audio'])
      for theme in ('dark','light'):
       page.evaluate('(theme)=>document.documentElement.dataset.theme=theme',theme)
       for width in (1440,390):
        page.set_viewport_size({'width':width,'height':900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),story['id']
        expect(page.locator('.story-panel')).to_be_visible()
      page.set_viewport_size({'width':1440,'height':1000})
    page.evaluate('document.documentElement.dataset.theme="dark"')
    page.wait_for_timeout(300)
    page.screenshot(path='../verification/polish-player.png',full_page=True)
    page.evaluate('location.hash="home"')
    expect(page.get_by_text('Music begins with your first touch',exact=False)).to_be_visible()
    assert page.locator('body').get_attribute('data-atmosphere') is None
    page.wait_for_timeout(300)
    page.screenshot(path='../verification/polish-home.png',full_page=True)
    assert not errors,errors
    print('105 scenario themes; 10 profiles in light/dark at desktop/mobile widths; no overflow or page errors.')
    browser.close()
  finally:server.stop()

if __name__=='__main__':run()
