import puppeteer from 'puppeteer';
// Or import puppeteer from 'puppeteer-core';

// Launch the browser and open a new blank page
const browser = await puppeteer.launch();
const page = await browser.newPage();

// Navigate the page to a URL.
await page.goto('https://finance.yahoo.com/quote/{ticker}/news');

// Set screen size.

const links = await.$$eval("img"), { elements } =>
    elements.map((element) => ({
        li: elem
    }))

await page.evaluate(() => {
    window.scrollTo(0, document.body.scrollHeight);
});
// Links to explore





await browser.close();