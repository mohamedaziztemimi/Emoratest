import fs from 'fs';
import { createWorker } from 'tesseract.js';
import { createCanvas } from 'canvas';
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf.mjs';

const pdfPath = 'Emoratest refactroing playbook.md';
const outputPath = 'playbook_text.txt';

// Set up worker
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/legacy/build/pdf.worker.mjs', import.meta.url).toString();

async function extractTextWithOCR() {
    console.log('Starting PDF OCR extraction...');

    // Load PDF
    const pdfData = new Uint8Array(fs.readFileSync(pdfPath));
    const pdf = await pdfjsLib.getDocument({ data: pdfData }).promise;
    console.log(`PDF loaded: ${pdf.numPages} pages`);

    const worker = await createWorker('eng', 1, {
        logger: m => {
            if (m.status === 'recognizing text') {
                process.stdout.write(`\rPage progress: ${Math.round(m.progress * 100)}%`);
            }
        }
    });

    let fullText = '';
    const numPages = Math.min(10, pdf.numPages); // Process first 10 pages for now

    for (let i = 1; i <= numPages; i++) {
        console.log(`\nProcessing page ${i}...`);

        try {
            const page = await pdf.getPage(i);
            const viewport = page.getViewport({ scale: 2.0 }); // Higher scale for better OCR

            const canvas = createCanvas(viewport.width, viewport.height);
            const context = canvas.getContext('2d');

            await page.render({
                canvasContext: context,
                viewport: viewport
            }).promise;

            // Get image buffer
            const imageBuffer = canvas.toBuffer('image/png');

            // Run OCR
            const { data: { text } } = await worker.recognize(imageBuffer);

            fullText += `\n${'='.repeat(60)}\n`;
            fullText += `PAGE ${i}\n`;
            fullText += `${'='.repeat(60)}\n`;
            fullText += text + '\n\n';

            console.log(`Page ${i} extracted: ${text.length} characters`);

        } catch (e) {
            console.error(`Error processing page ${i}:`, e.message);
        }
    }

    await worker.terminate();

    fs.writeFileSync(outputPath, fullText);
    console.log(`\n\n=== TEXT WRITTEN TO ${outputPath} ===`);
    console.log(`Total characters: ${fullText.length}`);
}

extractTextWithOCR().catch(console.error);
