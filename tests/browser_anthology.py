"""Optional browser regression for the expanded catalogue and soundtrack."""
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app
from launcher import LocalServer
from stories.scenarios import SCENARIOS
from engine.story_validator import validate
from playwright.sync_api import sync_playwright, expect


def wait_for(page, expression, arg=None):
    # Poll through the automation protocol; keep the application's strict CSP intact.
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        if page.evaluate(expression,arg):return
        page.wait_for_timeout(50)
    raise AssertionError('Condition did not become true: '+expression+'; status='+str(page.evaluate('WhatIfAudio.status()')))


def run():
    with tempfile.TemporaryDirectory() as directory:
        server=LocalServer(create_app(Path(directory)/'anthology.sqlite3',testing=True),0)
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
                context=browser.new_context(viewport={'width':1440,'height':1000})
                page=context.new_page();errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                base=f'http://127.0.0.1:{server.port}'
                page.goto(base)
                expect(page.locator('.hero')).to_be_visible()
                assert not page.evaluate('WhatIfAudio.status().enabled')
                page.locator('.hero h1').click()
                expect(page.locator('#welcome-dialog')).to_have_count(0)
                wait_for(page, 'WhatIfAudio.status().running && WhatIfAudio.status().signal > .001')
                assert page.evaluate('WhatIfAudio.status().profile')=='main'
                expect(page.locator('#audio-status')).to_contain_text('Between Possibilities')
                # Volume controls affect the actual Web Audio output signal.
                page.locator('#audio-volume').evaluate("node => {node.value='0';node.dispatchEvent(new Event('input'));}")
                wait_for(page, 'WhatIfAudio.status().signal < .00001')
                page.locator('#audio-volume').evaluate("node => {node.value='40';node.dispatchEvent(new Event('input'));}")
                wait_for(page, 'WhatIfAudio.status().signal > .001')
                page.get_by_role('button',name='Pause soundtrack').click()
                wait_for(page, '!WhatIfAudio.status().enabled && WhatIfAudio.status().voices === 0')
                page.locator('.hero h1').click()
                assert not page.evaluate('WhatIfAudio.status().enabled')
                page.get_by_role('button',name='Play soundtrack').click()
                wait_for(page, 'WhatIfAudio.status().signal > .001')
                page.get_by_role('link',name='Start Exploring').click()
                expect(page.locator('.card')).to_have_count(12)
                print('Audio controls passed; checking catalogue pages.',flush=True)
                titles=[]
                for index in range(9):
                    print('Catalogue page',index+1,flush=True)
                    titles.extend(page.locator('.card h3').all_text_contents())
                    if index<8:
                        page.get_by_role('button',name='Next →',exact=True).click()
                        expect(page.locator('.pagination')).to_contain_text(f'Page {index+2} of 9')
                print('Collected titles:',len(titles),len(set(titles)),flush=True)
                assert len(titles)==105 and len(set(titles))==105
                expect(page.get_by_role('button',name='Next →',exact=True)).to_be_disabled()
                page.get_by_label('Filter by category').select_option('Murder mystery')
                expect(page.locator('.card')).to_have_count(10)
                expect(page.locator('.content-note')).to_have_count(10)
                page.locator('.card').first.get_by_role('button',name='☆ Save',exact=True).click()
                page.get_by_label('Filter progress').select_option('saved')
                expect(page.locator('.card')).to_have_count(1)
                saved=page.locator('.card h3').inner_text()
                page.reload()
                page.get_by_label('Filter progress').select_option('saved')
                expect(page.locator('.card h3')).to_have_text(saved)
                page.get_by_label('Filter progress').select_option('all')
                # All genre assignments load actual PCM audio, not decorative controls.
                genre_names={s['audio']:s['category'] for s in SCENARIOS.values() if s['structure']!='classic'}
                for profile,genre in genre_names.items():
                    page.get_by_label('Filter by category').select_option(genre)
                    page.locator('.card').first.get_by_role('button',name='Preview atmosphere').click()
                    wait_for(page, '(profile) => WhatIfAudio.status().profile===profile && !WhatIfAudio.status().loading && WhatIfAudio.status().signal>.0001',arg=profile)
                    wait_for(page, 'WhatIfAudio.status().voices <= 1')
                    assert page.evaluate('WhatIfAudio.status().cached')<=3
                # Simulate the visibility event to check suspend/resume behavior without an operating-system UI.
                page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))")
                wait_for(page, '!WhatIfAudio.status().running')
                page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'))")
                wait_for(page, 'WhatIfAudio.status().running')
                # Each shared structure reaches each of its three endings through the browser player.
                for structure in ['investigation','negotiation','countdown']:
                    story=next(s for s in SCENARIOS.values() if s['structure']==structure)
                    witnesses={}
                    for path in validate(story):witnesses.setdefault(path['scene'],path)
                    for ending,path in witnesses.items():
                        page.goto(base+'/#explore')
                        page.get_by_role('searchbox').fill(story['title'])
                        page.get_by_label('Filter by category').select_option('')
                        page.locator('.card').get_by_role('button',name='Enter scenario',exact=False).click()
                        expect(page.locator('.story-panel')).to_be_visible()
                        for event in path['history']:
                            page.locator('.choice').filter(has_text=event['label']).click()
                            expect(page.locator('main')).not_to_have_attribute('aria-busy','true')
                        expect(page.get_by_role('heading',name=story['scenes'][ending]['title'])).to_be_visible()
                        expect(page.locator('.narrative')).to_have_text(story['scenes'][ending]['text'])
                        wait_for(page, '(profile)=>WhatIfAudio.status().profile===profile',arg=story['audio'])
                # A network failure must leave the game playable and the soundtrack honestly paused.
                page.goto(base+'/#explore')
                page.get_by_role('searchbox').fill('')
                page.route('**/static/audio/*.wav',lambda route:route.abort())
                page.get_by_label('Filter by category').select_option('Retro')
                page.locator('.card').first.get_by_role('button',name='Preview atmosphere').click()
                expect(page.locator('#toast')).to_be_visible()
                wait_for(page, '!WhatIfAudio.status().enabled')
                page.locator('.card').first.get_by_role('button',name='Enter scenario').click()
                expect(page.locator('.story-panel')).to_be_visible()
                page.unroute('**/static/audio/*.wav')
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.get_by_role('button',name='Open Timeline Lab').click()
                expect(page.locator('.graph')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert not errors,errors
                failed_context=browser.new_context()
                failed_page=failed_context.new_page()
                failed_page.route('**/static/audio/*.wav',lambda route:route.abort())
                failed_page.goto(base)
                failed_page.locator('.hero h1').click()
                expect(failed_page.locator('#toast')).to_contain_text('Use ♫ to try again.')
                assert not failed_page.evaluate('WhatIfAudio.status().enabled')
                expect(failed_page.locator('.hero')).to_be_visible()
                failed_context.close()
                for gesture in ('touch','keyboard'):
                    fresh=browser.new_context(has_touch=True)
                    first=fresh.new_page();first.goto(base)
                    expect(first.locator('.hero')).to_be_visible()
                    if gesture=='touch':first.locator('.hero h1').tap()
                    else:first.keyboard.press('Tab')
                    wait_for(first,'WhatIfAudio.status().running && WhatIfAudio.status().signal > .001')
                    fresh.close()
                browser.close()
                print('Anthology browser checks passed: 105 unique cards, nine pages, bookmarks, ten genre scores, measurable audio output, volume, pause, cache limit, visibility simulation, nine new-story endings, audio network failure and mobile graph.')
        finally:server.stop()

if __name__=='__main__':run()
