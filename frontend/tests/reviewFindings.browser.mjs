// Run against the frontend dev server:
// node --test frontend/tests/reviewFindings.browser.mjs
// Uses installed Playwright, or the integration checkout's isolated QA tools.
// AEGIS_BROWSER_TEST_URL and AEGIS_PLAYWRIGHT_MODULE can override those defaults.
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import process from 'node:process'
import { after, before, beforeEach, describe, it } from 'node:test'

const require = createRequire(import.meta.url)
let playwright
if (process.env.AEGIS_PLAYWRIGHT_MODULE) {
  playwright = require(process.env.AEGIS_PLAYWRIGHT_MODULE)
} else {
  try {
    playwright = require('playwright/test')
  } catch (error) {
    if (error.code !== 'MODULE_NOT_FOUND') throw error
    playwright = createRequire(new URL('../../../qa-tools/package.json', import.meta.url))('playwright/test')
  }
}
const { chromium } = playwright
const expect = playwright.expect.configure({ timeout: 15000 })
const baseUrl = process.env.AEGIS_BROWSER_TEST_URL || 'http://localhost:5176/'
const browserErrors = []
let cloudAttempts = 0
let assistantAttempts = 0
let browser

before(async () => {
  browser = await chromium.launch({
    channel: 'chrome',
    headless: true,
    args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'],
  })
})
after(async () => { await browser?.close() })

async function openPage(options) {
  const page = await browser.newPage({ reducedMotion: 'reduce', ...options })
  page.on('pageerror', (error) => browserErrors.push(error.message))
  await page.route('**/*', (route) => {
    const url = route.request().url()
    if (/generativelanguage\.googleapis|api\.openai\.com/.test(url)) {
      cloudAttempts += 1
      return route.abort()
    }
    if (/\/ai\/assistant(?:[/?]|$)/.test(url)) {
      assistantAttempts += 1
      return route.abort()
    }
    return route.continue()
  })
  await page.goto(baseUrl, { waitUntil: 'networkidle' })
  await page.locator('.model-status-ready').waitFor({ timeout: 60000 })
  return page
}

describe('mobile drawer keyboard regression', { timeout: 300000 }, () => {
  let page
  let close
  let summary
  before(async () => {
    page = await openPage({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true })
    close = page.locator('.mobile-drawer-close')
    summary = page.locator('.regional-marker-editor summary')
  })
  after(async () => { await page?.close() })
  beforeEach(async () => {
    if (await page.getByRole('dialog').count()) await page.keyboard.press('Escape')
    await page.getByLabel('Select synthetic health alert scenario').selectOption('heart-alert')
    await page.getByLabel('Select synthetic health alert scenario').selectOption('normal')
    await page.getByLabel('Select anatomical region').selectOption('head')
    await page.keyboard.press('Escape')
    await page.getByLabel('Open region details', { exact: true }).click()
    await expect(page.getByRole('dialog')).toBeFocused()
    await expect(page.locator('.regional-marker-editor')).not.toHaveAttribute('open', '')
  })

  it('collapsed editor includes summary and wraps forward past hidden controls', async () => {
    await page.keyboard.press('Tab')
    await expect(close).toBeFocused()
    await page.keyboard.press('Tab')
    await expect(summary).toBeFocused()
    await page.keyboard.press('Tab')
    await expect(close).toBeFocused()
  })

  it('collapsed editor wraps Shift+Tab from Close to summary', async () => {
    await close.focus()
    await page.keyboard.press('Shift+Tab')
    await expect(summary).toBeFocused()
    await page.keyboard.press('Shift+Tab')
    await expect(close).toBeFocused()
  })

  it('expanded editor includes enabled buttons and wraps forward', async () => {
    await summary.click()
    await close.focus()
    for (const control of [summary, page.getByRole('button', { name: 'MARK WARNING', exact: true }), page.getByRole('button', { name: 'MARK CRITICAL', exact: true }), close]) {
      await page.keyboard.press('Tab')
      await expect(control).toBeFocused()
    }
    await expect(page.getByRole('button', { name: 'CLEAR ADDED MARKER', exact: true })).toBeDisabled()
  })

  it('expanded editor wraps backward to the last enabled control', async () => {
    await summary.click()
    await close.focus()
    await page.keyboard.press('Shift+Tab')
    await expect(page.getByRole('button', { name: 'MARK CRITICAL', exact: true })).toBeFocused()
    await page.getByRole('button', { name: 'MARK CRITICAL', exact: true }).click()
    const clear = page.getByRole('button', { name: 'CLEAR ADDED MARKER', exact: true })
    await expect(clear).toBeEnabled()
    await close.focus()
    await page.keyboard.press('Shift+Tab')
    // The new finding also supplies a focusable alert card after the editor.
    await expect(page.locator('.right-hud .alert-item').last()).toBeFocused()
  })

  it('skips hidden, disabled, inert, negative-tabindex and closed nested-details controls', async () => {
    await page.getByRole('dialog').evaluate((panel) => {
      const fixture = document.createElement('div')
      fixture.id = 'focus-filter-fixture'
      fixture.innerHTML = '<button hidden>Hidden</button><button style="display:none">Display none</button><button style="visibility:hidden">Invisible</button><button disabled>Disabled</button><fieldset disabled><button>Disabled fieldset</button></fieldset><div inert><button>Inert</button></div><button tabindex="-2">Negative</button><details><summary>Nested summary</summary><button>Closed details control</button></details><button id="last-visible-control">Last visible</button>'
      panel.append(fixture)
    })
    try {
      await summary.focus()
      await page.keyboard.press('Tab')
      await expect(page.getByText('Nested summary', { exact: true })).toBeFocused()
      await page.keyboard.press('Tab')
      await expect(page.locator('#last-visible-control')).toBeFocused()
      await page.keyboard.press('Tab')
      await expect(close).toBeFocused()
      await page.keyboard.press('Shift+Tab')
      await expect(page.locator('#last-visible-control')).toBeFocused()
    } finally {
      await page.locator('#focus-filter-fixture').evaluate((element) => element.remove())
    }
  })

  it('contains unexpected programmatic focus and handles an empty Tab list', async () => {
    await page.getByLabel('Select synthetic astronaut').focus()
    await expect(page.getByRole('dialog')).toBeFocused()
    await page.getByRole('dialog').evaluate((panel) => {
      panel.querySelector('.mobile-drawer-close').disabled = true
      panel.querySelector('summary').tabIndex = -1
    })
    try {
      await page.keyboard.press('Tab')
      await expect(page.getByRole('dialog')).toBeFocused()
      await page.keyboard.press('Shift+Tab')
      await expect(page.getByRole('dialog')).toBeFocused()
    } finally {
      await page.getByRole('dialog').evaluate((panel) => {
        panel.querySelector('.mobile-drawer-close').disabled = false
        panel.querySelector('summary').removeAttribute('tabindex')
      })
    }
  })

  it('Close, Escape, backdrop and touch restore the drawer toggle', async () => {
    const toggle = page.locator('.mobile-details-toggle')
    for (const method of ['close', 'escape', 'backdrop', 'touch']) {
      if (method === 'close') await close.click()
      if (method === 'escape') await page.keyboard.press('Escape')
      if (method === 'backdrop') await page.locator('.mobile-drawer-backdrop').click({ position: { x: 5, y: 5 } })
      if (method === 'touch') await close.tap()
      await expect(page.getByRole('dialog')).toHaveCount(0)
      await expect(toggle).toBeFocused()
      await toggle.click()
    }
  })

  it('restores the region selector when that control opened the drawer', async () => {
    await page.keyboard.press('Escape')
    const selector = page.getByLabel('Select anatomical region')
    await selector.focus()
    await selector.selectOption('rightArm')
    await expect(page.getByRole('dialog')).toBeFocused()
    await page.keyboard.press('Escape')
    await expect(selector).toBeFocused()
  })
})

// Independent expected fixtures: global vital alerts never imply a local marker.
const scenarioColors = [
  ['normal', {}],
  ['heart-alert', {}],
  ['respiratory-alert', {}],
  ['left-arm-alert', { leftArm: 'ffd43b' }],
  ['right-arm-alert', { rightArm: 'ff4757' }],
  ['multiple-alerts', { leftArm: 'ffd43b', rightArm: 'ff4757', rightLeg: 'ffd43b' }],
  ['left-arm-critical', { leftArm: 'ff4757' }],
  ['left-leg-critical', { leftLeg: 'ff4757' }],
  ['right-leg-critical', { rightLeg: 'ff4757' }],
  ['multiple-localized-critical', { leftArm: 'ff4757', rightLeg: 'ff4757' }],
]

describe('astronaut-scoped synthetic markers', { timeout: 300000 }, () => {
  let page
  const astronaut = () => page.getByLabel('Select synthetic astronaut')
  const scenario = () => page.getByLabel('Select synthetic health alert scenario')
  const region = () => page.getByLabel('Select anatomical region')
  const summary = () => page.locator('.anatomy-alert-summary')
  async function count(value) {
    await expect(summary()).toContainText(value ? `${value} LOCALIZED MARKER${value === 1 ? '' : 'S'}` : 'NO LOCALIZED MARKERS')
  }
  async function colors(expected) {
    await expect.poll(() => page.evaluate((expected) => {
      const meshes = []
      window.markerTestStore.getState().scene.traverse((mesh) => {
        if (mesh.isMesh && mesh.userData.aegisLayer && mesh.userData.aegisLayer !== 'skin') {
          meshes.push({ name: mesh.name, region: mesh.userData.aegisRegion, selection: mesh.userData.aegisSelection, color: mesh.material.color.getHexString() })
        }
      })
      if (meshes.length !== 127) return `Expected 127 non-skin meshes; found ${meshes.length}`
      for (const mesh of meshes) {
        const color = expected[mesh.selection] || expected[mesh.region] || '00d5f2'
        if (mesh.color !== color) return `${mesh.name}: ${mesh.color} != ${color}`
      }
      return 'ok'
    }, expected)).toBe('ok')
  }
  async function addMarker(selected, severity) {
    await region().selectOption(selected)
    const editor = page.locator('.regional-marker-editor')
    if (!await editor.evaluate((element) => element.open)) await editor.locator('summary').click()
    await page.getByRole('button', { name: `MARK ${severity.toUpperCase()}`, exact: true }).click()
    await expect(page.locator('.regional-provenance')).toContainText('Synthetic demonstration')
    await expect(page.locator('.region-detail-panel')).toContainText('no clinical diagnosis', { ignoreCase: true })
  }
  before(async () => {
    page = await openPage({ viewport: { width: 1440, height: 1050 } })
    await page.evaluate(async () => {
      const fiberUrl = performance.getEntriesByType('resource').map((entry) => entry.name).find((url) => url.includes('/@react-three_fiber.js'))
      window.markerTestStore = [...(await import(fiberUrl))._roots.values()][0].store
    })
  })
  after(async () => { await page?.close() })
  beforeEach(async () => {
    for (const id of ['A-02', 'A-01']) {
      await astronaut().selectOption(id)
      await scenario().selectOption('heart-alert')
      await scenario().selectOption('normal')
    }
    await page.getByRole('button', { name: 'FULL BODY', exact: true }).click()
  })

  it('isolates A-01 right-arm critical and A-02 markers, counts and actual mesh colours', async () => {
    await addMarker('rightArm', 'critical')
    await count(1)
    await colors({ rightArm: 'ff4757' })
    await astronaut().selectOption('A-02')
    await count(0)
    await colors({})
    await expect(page.getByRole('button', { name: 'CLEAR ADDED MARKER', exact: true })).toBeDisabled()
    await expect(page.locator('.region-detail-panel')).toHaveClass(/status-no-data/)
    await addMarker('leftLeg', 'warning')
    await addMarker('liver', 'critical')
    await count(2)
    await colors({ leftLeg: 'ffd43b', liver: 'ff4757' })
    await astronaut().selectOption('A-01')
    await count(1)
    await colors({ rightArm: 'ff4757' })
    await astronaut().selectOption('A-02')
    await count(2)
    await colors({ leftLeg: 'ffd43b', liver: 'ff4757' })
  })

  it('editing and clearing the same region only changes the selected astronaut', async () => {
    await addMarker('rightArm', 'critical')
    await astronaut().selectOption('A-02')
    await addMarker('rightArm', 'critical')
    await astronaut().selectOption('A-01')
    await addMarker('rightArm', 'warning')
    await count(1)
    await colors({ rightArm: 'ffd43b' })
    await astronaut().selectOption('A-02')
    await count(1)
    await colors({ rightArm: 'ff4757' })
    await astronaut().selectOption('A-01')
    await page.getByRole('button', { name: 'CLEAR ADDED MARKER', exact: true }).click()
    await count(0)
    await colors({})
    await astronaut().selectOption('A-02')
    await count(1)
    await colors({ rightArm: 'ff4757' })
  })

  it('retains custom markers across all layers and camera reset', async () => {
    await addMarker('rightArm', 'critical')
    await addMarker('liver', 'warning')
    for (const layer of ['SKELETON', 'MUSCLES', 'ORGANS', 'FULL BODY']) {
      await page.getByRole('button', { name: layer, exact: true }).click()
      await count(2)
      await colors({ rightArm: 'ff4757', liver: 'ffd43b' })
    }
    await page.getByLabel('Reset camera', { exact: true }).click()
    await count(2)
    await colors({ rightArm: 'ff4757', liver: 'ffd43b' })
  })

  it('scenario reset clears the selected custom bucket and preserves other astronauts and explicit scenarios', async () => {
    await addMarker('rightArm', 'critical')
    await astronaut().selectOption('A-02')
    await addMarker('leftLeg', 'warning')
    await scenario().selectOption('left-arm-alert')
    await count(1)
    await colors({ leftArm: 'ffd43b' })
    await astronaut().selectOption('A-01')
    await count(2)
    await colors({ leftArm: 'ffd43b', rightArm: 'ff4757' })
    await scenario().selectOption('normal')
    await count(0)
    await colors({})
    await astronaut().selectOption('A-02')
    await count(0)
    await colors({})
  })

  for (const [id, expected] of scenarioColors) {
    it(`preserves demo scenario ${id} without inferring regional findings from global vitals`, async () => {
      assert.equal(await scenario().locator('option').count(), 10)
      await scenario().selectOption(id)
      for (const selected of ['A-01', 'A-02']) {
        await astronaut().selectOption(selected)
        await count(Object.keys(expected).length)
        await colors(expected)
      }
    })
  }
})

it('has no uncaught browser errors or AI generation/chat requests', () => {
  assert.deepEqual(browserErrors, [])
  assert.equal(cloudAttempts, 0)
  assert.equal(assistantAttempts, 0)
})
