import { chromium } from 'playwright'
import { mkdir } from 'node:fs/promises'

const BASE = 'http://127.0.0.1:5173'
const OUT = '/workspace/docs/assets'

async function clickNav(page, label) {
  await page.getByRole('button', { name: new RegExp(label, 'i') }).first().click()
  await page.waitForTimeout(800)
}

async function main() {
  await mkdir(OUT, { recursive: true })
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })

  await page.goto(BASE, { waitUntil: 'networkidle' })
  await page.waitForTimeout(1200)
  await page.screenshot({ path: `${OUT}/01-home-dashboard.png`, fullPage: false })

  const searchInput = page.locator('.topbar-input')
  await searchInput.fill('Kylian Mbappe')
  await page.getByRole('button', { name: /^Search$/i }).click()
  await page.waitForSelector('.player-profile, .empty-state', { timeout: 120000 })
  await page.waitForTimeout(1500)
  await page.screenshot({ path: `${OUT}/02-player-dashboard.png`, fullPage: false })

  await clickNav(page, '3D Globe')
  await page.waitForTimeout(2500)
  await page.screenshot({ path: `${OUT}/03-globe-intelligence.png`, fullPage: false })

  await clickNav(page, 'AI Reports')
  await page.waitForTimeout(1000)
  await page.screenshot({ path: `${OUT}/04-ai-reports.png`, fullPage: false })

  await clickNav(page, 'Compare Players')
  await page.waitForTimeout(1000)
  await page.screenshot({ path: `${OUT}/05-compare-players.png`, fullPage: false })

  await clickNav(page, 'Informations auteur')
  await page.waitForTimeout(800)
  await page.screenshot({ path: `${OUT}/06-author.png`, fullPage: false })

  await browser.close()
  console.log('Screenshots saved to', OUT)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
