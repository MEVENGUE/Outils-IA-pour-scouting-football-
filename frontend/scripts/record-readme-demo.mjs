import { chromium } from 'playwright'
import { mkdir } from 'node:fs/promises'
import { rename, readdir } from 'node:fs/promises'
import { join } from 'node:path'

const BASE = 'http://127.0.0.1:5173'
const OUT = '/workspace/docs/assets'

async function clickNav(page, label) {
  await page.getByRole('button', { name: new RegExp(label, 'i') }).first().click()
  await page.waitForTimeout(1200)
}

async function main() {
  await mkdir(OUT, { recursive: true })
  const browser = await chromium.launch()
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: OUT, size: { width: 1440, height: 900 } },
  })
  const page = await context.newPage()

  await page.goto(BASE, { waitUntil: 'networkidle' })
  await page.waitForTimeout(1500)

  const searchInput = page.locator('.topbar-input')
  await searchInput.fill('Kylian Mbappe')
  await page.getByRole('button', { name: /^Search$/i }).click()
  await page.waitForSelector('.player-profile, .empty-state', { timeout: 120000 })
  await page.waitForTimeout(2000)

  await clickNav(page, '3D Globe')
  await page.waitForTimeout(3000)

  await clickNav(page, 'AI Reports')
  await page.waitForTimeout(2000)

  await clickNav(page, 'Compare Players')
  await page.waitForTimeout(2000)

  await clickNav(page, 'Watchlist')
  await page.waitForTimeout(1500)

  await clickNav(page, 'Informations auteur')
  await page.waitForTimeout(2000)

  const video = page.video()
  await page.close()
  await context.close()
  await browser.close()

  if (video) {
    const webmPath = await video.path()
    await rename(webmPath, join(OUT, 'x-scout-demo.webm'))
    console.log('Demo video saved to', join(OUT, 'x-scout-demo.webm'))
  }

  const leftovers = await readdir(OUT)
  for (const file of leftovers.filter((f) => f.endsWith('.webm') && f !== 'x-scout-demo.webm')) {
    await rename(join(OUT, file), join(OUT, 'x-scout-demo.webm')).catch(() => {})
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
