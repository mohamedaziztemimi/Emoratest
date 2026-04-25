import fs from 'fs';
import { createWorker } from 'tesseract.js';
import { pdf as pdfToImg } from 'pdf-to-img';

const pdfPath = 'Emoratest refactroing playbook.md';
const outputPath = 'playbook_text.txt';

async function extractTextWithOCR() {
    console.log('Starting PDF OCR extraction...');
    console.log('Converting PDF to images...');

    const converter = await pdfToImg(pdfPath, {
        scale: 2.0,
        outputFormat: 'png'
    });

    const worker = await createWorker('eng', 1, {
        logger: m => {
            if (m.status === 'recognizing text') {
                process.stdout.write(`\rOCR progress: ${Math.round(m.progress * 100)}%`);
            }
        }
    });

    let fullText = '';
    let pageNum = 0;
    const maxPages = 10;

    for await (const image of converter.toIterator()) {
        pageNum++;
        if (pageNum > maxPages) break;

        console.log(`\nProcessing page ${pageNum}...`);

        try {
            // Run OCR on the image buffer
            const { data: { text } } = await worker.recognize(image.buffer);

            fullText += `\n${'='.repeat(60)}\n`;
            fullText += `PAGE ${pageNum}\n`;
            fullText += `${'='.repeat(60)}\n`;
            fullText += text + '\n\n';

            console.log(`Page ${pageNum} extracted: ${text.length} characters`);

        } catch (e) {
            console.error(`Error processing page ${pageNum}:`, e.message);
        }
    }

    await worker.terminate();

    fs.writeFileSync(outputPath, fullText);
    console.log(`\n\n=== TEXT WRITTEN TO ${outputPath} ===`);
    console.log(`Total characters: ${fullText.length}`);
}

extractTextWithOCR().catch(console.error);
